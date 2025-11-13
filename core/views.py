from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from .models import MembershipPlan, Subscription, CustomUser, UserPoints, Trainer, PersonalTrainerSubscription
from .forms import RegistrationForm, ContactForm
from bookings.models import Booking, GymClass
from workouts.models import UserWorkoutPlan, Workout
from datetime import datetime, timedelta


def home(request):
    """Homepage view"""
    # Get featured workouts (mix of free and popular categories)
    featured_workouts = Workout.objects.all().order_by('?')[:6]  # Random 6 workouts
    
    # Get workouts by category for quick access
    workout_categories = Workout.CATEGORY_CHOICES[:8]  # Show first 8 categories
    
    # Check user access for workouts if authenticated
    if request.user.is_authenticated:
        from workouts.utils import user_has_access_to_workout, can_view_workout_details
        for workout in featured_workouts:
            workout.has_access = user_has_access_to_workout(request.user, workout)
            workout.can_view_details = can_view_workout_details(request.user, workout)
    else:
        from workouts.utils import can_view_workout_details
        for workout in featured_workouts:
            workout.has_access = workout.is_free  # Non-authenticated users only see free workouts
            workout.can_view_details = can_view_workout_details(request.user, workout)
    
    context = {
        'active_members': CustomUser.objects.filter(is_active=True).count(),
        'total_classes': GymClass.objects.filter(is_active=True).count(),
        'featured_workouts': featured_workouts,
        'workout_categories': workout_categories,
    }
    return render(request, 'home.html', context)


def about(request):
    """About Us page"""
    return render(request, 'about.html')


def contact(request):
    """Contact page with form"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # In a real app, you would send an email here
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})


def pricing(request):
    """Membership plans page"""
    plans = MembershipPlan.objects.filter(is_active=True).order_by('price')
    return render(request, 'pricing.html', {'plans': plans})


def schedule(request):
    """Class schedule page"""
    classes = GymClass.objects.filter(is_active=True).order_by('schedule_time', 'schedule_days')
    return render(request, 'schedule.html', {'classes': classes})


def register(request):
    """User registration"""
    # Prevent logged-in users from accessing registration
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in. Please log out to create a new account.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to FitZone Gym!')
            return redirect('dashboard')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    """Member dashboard"""
    from django.utils import timezone
    from datetime import timedelta
    
    user = request.user
    
    # Get active subscription
    try:
        subscription = Subscription.objects.filter(
            user=user, 
            status__in=['active', 'trialing']
        ).latest('created_at')
    except Subscription.DoesNotExist:
        subscription = None
    
    # Calculate subscription details if exists
    subscription_details = None
    if subscription and subscription.plan:
        now = timezone.now()
        start_date = subscription.current_period_start or subscription.created_at
        end_date = subscription.current_period_end
        
        # Calculate remaining days
        remaining_days = None
        if end_date:
            delta = end_date.date() - now.date()
            remaining_days = max(0, delta.days)
        
        # Get included workouts
        included_workouts = subscription.plan.included_workouts.all()
        
        # Next billing date (same as period end for now)
        next_billing_date = end_date
        
        subscription_details = {
            'plan_name': subscription.plan.name,
            'status': subscription.status,
            'duration': subscription.plan.get_duration_display(),
            'start_date': start_date,
            'end_date': end_date,
            'remaining_days': remaining_days,
            'next_billing_date': next_billing_date,
            'included_workouts': included_workouts,
            'included_workouts_count': included_workouts.count(),
        }
    
    # Get upcoming bookings
    today = datetime.now().date()
    upcoming_bookings = Booking.objects.filter(
        user=user,
        booking_date__gte=today,
        status='confirmed'
    ).order_by('booking_date')[:5]
    
    # Get user streak and points
    try:
        streak = user.streak
    except:
        streak = None
    
    total_points = UserPoints.objects.filter(user=user).aggregate(
        total=Sum('points')
    )['total'] or 0
    
    # Get assigned workout plans
    assigned_plans = UserWorkoutPlan.objects.filter(user=user).select_related('plan', 'plan__trainer')
    
    # Get personal trainer subscription
    personal_trainer_subscription = PersonalTrainerSubscription.objects.filter(
        user=user,
        status='active'
    ).select_related('trainer', 'trainer__user').first()
    
    # Get trainer-assigned individual workouts
    trainer_assigned_workouts = None
    if personal_trainer_subscription:
        from workouts.models import TrainerAssignedWorkout
        trainer_assigned_workouts = TrainerAssignedWorkout.objects.filter(
            trainer=personal_trainer_subscription.trainer,
            user=user
        ).select_related('workout').order_by('-assigned_at')
    
    context = {
        'subscription': subscription,
        'subscription_details': subscription_details,
        'upcoming_bookings': upcoming_bookings,
        'streak': streak,
        'total_points': total_points,
        'assigned_plans': assigned_plans,
        'personal_trainer_subscription': personal_trainer_subscription,
        'trainer_assigned_workouts': trainer_assigned_workouts,
    }
    return render(request, 'dashboard.html', context)


@login_required
def qr_code(request):
    """QR code generation for gym entry"""
    from .utils import generate_qr_code
    
    qr_data = generate_qr_code(request.user)
    
    context = {
        'qr_data': qr_data,
    }
    return render(request, 'core/qr_code.html', context)


def custom_logout(request):
    """Custom logout view that accepts GET requests"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')


@login_required
def select_trainer(request):
    """View to select and subscribe to a personal trainer"""
    trainers = Trainer.objects.all().select_related('user')
    
    # Split specializations for each trainer
    for trainer in trainers:
        if trainer.specializations:
            trainer.specializations_list = [s.strip() for s in trainer.specializations.split(',') if s.strip()]
        else:
            trainer.specializations_list = []
    
    # Get user's current active personal trainer subscription if any
    current_subscription = PersonalTrainerSubscription.objects.filter(
        user=request.user,
        status='active'
    ).first()
    
    # Default price for personal trainer subscription (can be made configurable)
    trainer_price = 5000.00  # 5000 rupees per month
    
    context = {
        'trainers': trainers,
        'current_subscription': current_subscription,
        'trainer_price': trainer_price,
    }
    return render(request, 'core/select_trainer.html', context)


@login_required
def subscribe_trainer(request, trainer_id):
    """Subscribe to a personal trainer (payment bypassed, instant activation)"""
    trainer = get_object_or_404(Trainer, id=trainer_id)
    
    # Check if user already has an active subscription with this trainer
    existing = PersonalTrainerSubscription.objects.filter(
        user=request.user,
        trainer=trainer,
        status='active'
    ).first()
    
    if existing:
        messages.info(request, f'You already have an active subscription with {trainer.user.get_full_name()}.')
        return redirect('select_trainer')
    
    # Cancel any existing active subscriptions with other trainers
    PersonalTrainerSubscription.objects.filter(
        user=request.user,
        status='active'
    ).update(status='cancelled', end_date=timezone.now())
    
    # Default price (can be made configurable)
    trainer_price = 5000.00
    
    try:
        # Create subscription (payment bypassed - instant activation)
        subscription = PersonalTrainerSubscription.objects.create(
            user=request.user,
            trainer=trainer,
            status='active',
            price=trainer_price,
            start_date=timezone.now(),
            # end_date can be set based on subscription duration (e.g., 1 month from now)
            # For now, leaving it null for ongoing subscription
        )
        
        messages.success(request, f'Successfully subscribed to {trainer.user.get_full_name()} as your personal trainer!')
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f'Error subscribing to trainer: {str(e)}')
        return redirect('select_trainer')


@login_required
def cancel_trainer_subscription(request, subscription_id):
    """Cancel a personal trainer subscription"""
    subscription = get_object_or_404(
        PersonalTrainerSubscription,
        id=subscription_id,
        user=request.user
    )
    
    if subscription.status == 'cancelled':
        messages.info(request, 'This subscription is already cancelled.')
        return redirect('dashboard')
    
    subscription.status = 'cancelled'
    subscription.end_date = timezone.now()
    subscription.save()
    
    messages.success(request, f'Personal trainer subscription cancelled successfully.')
    return redirect('dashboard')
