"""
Utility functions for workout access control
"""
from django.utils import timezone


def user_has_access_to_workout(user, workout):
    """
    Check if a user has access to a workout.
    
    Rules:
    - Free workouts are always accessible
    - Paid workouts require an active subscription with a plan that includes the workout
    
    Args:
        user: CustomUser instance
        workout: Workout instance
    
    Returns:
        bool: True if user has access, False otherwise
    """
    # Free workouts are always accessible
    if workout.is_free:
        return True
    
    # Paid workouts require active subscription
    if not user.is_authenticated:
        return False
    
    # Check if user has an active subscription
    from core.models import Subscription
    
    active_subscription = Subscription.objects.filter(
        user=user,
        status='active',
        current_period_end__gte=timezone.now()
    ).first()
    
    if not active_subscription or not active_subscription.plan:
        return False
    
    # Check if the plan includes this workout
    return workout in active_subscription.plan.included_workouts.all()


def get_accessible_workouts(user):
    """
    Get all workouts accessible to a user.
    
    Args:
        user: CustomUser instance (can be AnonymousUser)
    
    Returns:
        QuerySet: Workouts the user can access
    """
    from .models import Workout
    from core.models import Subscription
    
    # Always include free workouts
    accessible = Workout.objects.filter(is_free=True)
    
    # If user is authenticated and has active subscription, include plan workouts
    if user.is_authenticated:
        active_subscription = Subscription.objects.filter(
            user=user,
            status='active',
            current_period_end__gte=timezone.now()
        ).first()
        
        if active_subscription and active_subscription.plan:
            # Add workouts from the subscription plan
            plan_workouts = active_subscription.plan.included_workouts.all()
            accessible = accessible.union(plan_workouts)
    
    return accessible.distinct()

