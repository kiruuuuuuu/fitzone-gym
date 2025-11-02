from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils import timezone
import stripe
import json
from core.models import MembershipPlan, Subscription, CustomUser
try:
    from .webhooks import handle_checkout_session_completed, handle_subscription_updated, handle_subscription_deleted
except ImportError:
    # Fallback if webhooks module is not available
    def handle_checkout_session_completed(session):
        pass
    def handle_subscription_updated(subscription_obj):
        pass
    def handle_subscription_deleted(subscription_obj):
        pass

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def create_checkout_session(request, plan_id):
    """Create Stripe checkout session"""
    plan = get_object_or_404(MembershipPlan, id=plan_id, is_active=True)
    
    try:
        # Create or get Stripe customer
        if not request.user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=request.user.email,
                name=f"{request.user.first_name} {request.user.last_name}",
                metadata={'user_id': request.user.id}
            )
            request.user.stripe_customer_id = customer.id
            request.user.save()
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=request.user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': plan.stripe_price_id or 'price_test',
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.build_absolute_uri('/payments/success/') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri('/pricing/'),
            metadata={
                'plan_id': plan.id,
                'user_id': request.user.id,
            }
        )
        
        return redirect(checkout_session.url)
        
    except Exception as e:
        messages.error(request, f'Error creating checkout session: {str(e)}')
        return redirect('pricing')


@login_required
def checkout_success(request):
    """Handle successful checkout"""
    session_id = request.GET.get('session_id')
    
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            messages.success(request, 'Payment successful! Your subscription is now active.')
        except:
            messages.info(request, 'Your subscription is being processed.')
    
    return redirect('dashboard')


@csrf_exempt
def webhook(request):
    """Stripe webhook endpoint"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        handle_checkout_session_completed(event['data']['object'])
    elif event['type'] == 'customer.subscription.updated':
        handle_subscription_updated(event['data']['object'])
    elif event['type'] == 'customer.subscription.deleted':
        handle_subscription_deleted(event['data']['object'])
    
    return HttpResponse(status=200)


@login_required
def my_subscription(request):
    """User subscription management page"""
    subscriptions = Subscription.objects.filter(user=request.user).order_by('-created_at')
    active_subscription = subscriptions.filter(status='active').first()
    
    context = {
        'subscriptions': subscriptions,
        'active_subscription': active_subscription,
    }
    return render(request, 'payments/my_subscription.html', context)
