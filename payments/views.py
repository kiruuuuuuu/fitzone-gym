from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from core.models import MembershipPlan, Subscription, CustomUser


@login_required
def create_checkout_session(request, plan_id):
    """Create subscription directly (Stripe bypassed)"""
    plan = get_object_or_404(MembershipPlan, id=plan_id, is_active=True)
    
    try:
        # Cancel any existing active subscriptions
        existing_subscriptions = Subscription.objects.filter(
            user=request.user,
            status='active'
        )
        for sub in existing_subscriptions:
            sub.status = 'cancelled'
            sub.save()
        
        # Calculate period dates
        now = timezone.now()
        duration_map = {
            'trial': timedelta(days=7),
            '1_week': timedelta(days=7),
            '1_month': timedelta(days=30),
            '3_months': timedelta(days=90),
            '6_months': timedelta(days=180),
            '12_months': timedelta(days=365),
        }
        duration = duration_map.get(plan.duration, timedelta(days=30))
        period_end = now + duration
        
        # Create subscription directly
        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            status='active',
            current_period_start=now,
            current_period_end=period_end,
            stripe_subscription_id=None  # No Stripe needed
        )
        
        messages.success(request, f'Payment successful! Your {plan.name} subscription is now active.')
        return redirect('payments:checkout_success')
        
    except Exception as e:
        messages.error(request, f'Error processing payment: {str(e)}')
        return redirect('pricing')


@login_required
def checkout_success(request):
    """Handle successful checkout"""
    messages.success(request, 'Payment successful! Your subscription is now active.')
    return redirect('dashboard')


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
