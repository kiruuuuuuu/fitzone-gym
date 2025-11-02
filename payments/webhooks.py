from django.utils import timezone
from datetime import datetime
from core.models import Subscription, MembershipPlan, CustomUser
import stripe


def handle_checkout_session_completed(session):
    """Handle checkout.session.completed event"""
    user_id = session['metadata'].get('user_id')
    plan_id = session['metadata'].get('plan_id')
    
    try:
        user = CustomUser.objects.get(id=user_id)
        plan = MembershipPlan.objects.get(id=plan_id)
        
        # Get subscription from Stripe
        subscription_id = session.get('subscription')
        if subscription_id:
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Create or update subscription
            subscription, created = Subscription.objects.update_or_create(
                user=user,
                stripe_subscription_id=subscription_id,
                defaults={
                    'plan': plan,
                    'status': 'active',
                    'current_period_start': datetime.fromtimestamp(stripe_subscription['current_period_start'], tz=timezone.utc),
                    'current_period_end': datetime.fromtimestamp(stripe_subscription['current_period_end'], tz=timezone.utc),
                }
            )
    except CustomUser.DoesNotExist:
        print(f"Webhook Error: User {user_id} not found.")
        raise  # Re-raise the exception to trigger a non-200 response
    except MembershipPlan.DoesNotExist:
        print(f"Webhook Error: Plan {plan_id} not found.")
        raise
    except Exception as e:
        print(f"Generic webhook error: {e}")
        raise


def handle_subscription_updated(subscription_obj):
    """Handle customer.subscription.updated event"""
    subscription_id = subscription_obj['id']
    
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
        subscription.status = subscription_obj['status']
        subscription.current_period_start = datetime.fromtimestamp(subscription_obj['current_period_start'], tz=timezone.utc)
        subscription.current_period_end = datetime.fromtimestamp(subscription_obj['current_period_end'], tz=timezone.utc)
        subscription.save()
    except Subscription.DoesNotExist:
        print(f"Webhook Error: Subscription {subscription_id} not found.")
        # For updates, don't raise - subscription might have been deleted
        pass
    except Exception as e:
        print(f"Error handling subscription updated: {e}")
        raise


def handle_subscription_deleted(subscription_obj):
    """Handle customer.subscription.deleted event"""
    subscription_id = subscription_obj['id']
    
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
        subscription.status = 'cancelled'
        subscription.save()
    except Subscription.DoesNotExist:
        print(f"Webhook Error: Subscription {subscription_id} not found.")
        # For deletions, don't raise - subscription might have already been deleted
        pass
    except Exception as e:
        print(f"Error handling subscription deleted: {e}")
        raise

