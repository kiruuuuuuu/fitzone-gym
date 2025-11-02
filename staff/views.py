from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from datetime import datetime, timedelta
from .mixins import StaffRequiredMixin, TrainerRequiredMixin

from core.models import CustomUser, MembershipPlan, Subscription, Trainer, UserPoints, QRCodeSession
from bookings.models import GymClass, Booking
from workouts.models import Workout
from community.models import Challenge


# Staff Dashboard Views (for Admins)
@method_decorator(login_required, name='dispatch')
class StaffDashboard(StaffRequiredMixin, ListView):
    """Main staff dashboard showing stats and overview"""
    template_name = 'staff/dashboard.html'
    context_object_name = 'recent_members'

    def get_queryset(self):
        return CustomUser.objects.filter(is_staff=False).order_by('-created_at')[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Key metrics
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=7)
        
        context['total_members'] = CustomUser.objects.filter(is_staff=False).count()
        context['active_subscriptions'] = Subscription.objects.filter(status='active').count()
        
        # Revenue calculations
        active_subs = Subscription.objects.filter(status='active')
        context['total_mrr'] = sum([sub.plan.price for sub in active_subs if sub.plan])
        
        # Recent members
        context['new_members_7d'] = CustomUser.objects.filter(
            is_staff=False,
            created_at__gte=seven_days_ago
        ).count()
        
        # Today's classes
        context['todays_classes'] = GymClass.objects.filter(
            is_active=True
        ).count()
        
        # Class bookings today
        context['bookings_today'] = Booking.objects.filter(
            booking_date=today,
            status='confirmed'
        ).count()
        
        # Recent transactions
        context['recent_subscriptions'] = Subscription.objects.all().order_by('-created_at')[:5]
        
        return context


@method_decorator(login_required, name='dispatch')
class MemberListView(StaffRequiredMixin, ListView):
    """List all members with search capability"""
    template_name = 'staff/member_list.html'
    context_object_name = 'members'
    paginate_by = 20

    def get_queryset(self):
        queryset = CustomUser.objects.filter(is_staff=False)
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


@login_required
def member_detail(request, user_id):
    """Detailed view of a specific member"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    member = get_object_or_404(CustomUser, id=user_id, is_staff=False)
    
    # Get member's data
    active_subscription = Subscription.objects.filter(user=member, status='active').first()
    all_subscriptions = Subscription.objects.filter(user=member).order_by('-created_at')
    
    upcoming_bookings = Booking.objects.filter(
        user=member,
        booking_date__gte=timezone.now().date(),
        status='confirmed'
    ).order_by('booking_date')[:10]
    
    past_bookings = Booking.objects.filter(
        user=member,
        booking_date__lt=timezone.now().date()
    ).order_by('-booking_date')[:10]
    
    workout_completions = member.workout_completions.all()[:10]
    
    total_points = UserPoints.objects.filter(user=member).aggregate(
        total=Sum('points')
    )['total'] or 0
    
    recent_points = UserPoints.objects.filter(user=member).order_by('-created_at')[:10]
    
    try:
        streak = member.streak
    except:
        streak = None
    
    context = {
        'member': member,
        'active_subscription': active_subscription,
        'all_subscriptions': all_subscriptions,
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'workout_completions': workout_completions,
        'total_points': total_points,
        'recent_points': recent_points,
        'streak': streak,
    }
    
    return render(request, 'staff/member_detail.html', context)


@method_decorator(login_required, name='dispatch')
class PlanListView(StaffRequiredMixin, ListView):
    """List all membership plans"""
    template_name = 'staff/plan_list.html'
    context_object_name = 'plans'
    model = MembershipPlan


@login_required
def plan_create(request):
    """Create a new membership plan"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        features = request.POST.get('features')
        stripe_price_id = request.POST.get('stripe_price_id')
        is_active = request.POST.get('is_active') == 'on'
        
        if name and price:
            try:
                plan = MembershipPlan.objects.create(
                    name=name,
                    price=price,
                    features=features,
                    stripe_price_id=stripe_price_id,
                    is_active=is_active
                )
                messages.success(request, f'Plan "{plan.name}" created successfully!')
                return redirect('staff:plan_list')
            except Exception as e:
                messages.error(request, f'Error creating plan: {str(e)}')
    
    return render(request, 'staff/plan_form.html', {'action': 'Create'})


@login_required
def plan_edit(request, plan_id):
    """Edit a membership plan"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    plan = get_object_or_404(MembershipPlan, id=plan_id)
    
    if request.method == 'POST':
        plan.name = request.POST.get('name')
        plan.price = request.POST.get('price')
        plan.features = request.POST.get('features')
        plan.stripe_price_id = request.POST.get('stripe_price_id')
        plan.is_active = request.POST.get('is_active') == 'on'
        
        try:
            plan.save()
            messages.success(request, f'Plan "{plan.name}" updated successfully!')
            return redirect('staff:plan_list')
        except Exception as e:
            messages.error(request, f'Error updating plan: {str(e)}')
    
    return render(request, 'staff/plan_form.html', {'plan': plan, 'action': 'Edit'})


@method_decorator(login_required, name='dispatch')
class ClassListView(StaffRequiredMixin, ListView):
    """List all gym classes"""
    template_name = 'staff/class_list.html'
    context_object_name = 'classes'
    model = GymClass


@login_required
def class_create(request):
    """Create a new gym class"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    trainers = Trainer.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        trainer_id = request.POST.get('trainer')
        duration = request.POST.get('duration')
        max_capacity = request.POST.get('max_capacity')
        schedule_time = request.POST.get('schedule_time')
        schedule_days = request.POST.get('schedule_days')
        is_active = request.POST.get('is_active') == 'on'
        
        if name and duration and max_capacity:
            try:
                trainer = Trainer.objects.get(id=trainer_id) if trainer_id else None
                GymClass.objects.create(
                    name=name,
                    description=description,
                    trainer=trainer,
                    duration=duration,
                    max_capacity=max_capacity,
                    schedule_time=schedule_time,
                    schedule_days=schedule_days,
                    is_active=is_active
                )
                messages.success(request, f'Class "{name}" created successfully!')
                return redirect('staff:class_list')
            except Exception as e:
                messages.error(request, f'Error creating class: {str(e)}')
    
    return render(request, 'staff/class_form.html', {'trainers': trainers, 'action': 'Create'})


@login_required
def class_edit(request, class_id):
    """Edit a gym class"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    gym_class = get_object_or_404(GymClass, id=class_id)
    trainers = Trainer.objects.all()
    
    if request.method == 'POST':
        gym_class.name = request.POST.get('name')
        gym_class.description = request.POST.get('description')
        trainer_id = request.POST.get('trainer')
        gym_class.duration = request.POST.get('duration')
        gym_class.max_capacity = request.POST.get('max_capacity')
        gym_class.schedule_time = request.POST.get('schedule_time')
        gym_class.schedule_days = request.POST.get('schedule_days')
        gym_class.is_active = request.POST.get('is_active') == 'on'
        
        try:
            gym_class.trainer = Trainer.objects.get(id=trainer_id) if trainer_id else None
            gym_class.save()
            messages.success(request, f'Class "{gym_class.name}" updated successfully!')
            return redirect('staff:class_list')
        except Exception as e:
            messages.error(request, f'Error updating class: {str(e)}')
    
    return render(request, 'staff/class_form.html', {'gym_class': gym_class, 'trainers': trainers, 'action': 'Edit'})


@login_required
def workout_list(request):
    """List all workouts"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    workouts = Workout.objects.all().order_by('category', 'difficulty_level', 'title')
    return render(request, 'staff/workout_list.html', {'workouts': workouts})


@login_required
def workout_create(request):
    """Create a new workout"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        video_url = request.POST.get('video_url')
        difficulty = request.POST.get('difficulty_level')
        duration = request.POST.get('duration')
        category = request.POST.get('category')
        
        if title and description and difficulty and duration and category:
            try:
                Workout.objects.create(
                    title=title,
                    description=description,
                    video_url=video_url,
                    difficulty_level=difficulty,
                    duration=duration,
                    category=category
                )
                messages.success(request, f'Workout "{title}" created successfully!')
                return redirect('staff:workout_list')
            except Exception as e:
                messages.error(request, f'Error creating workout: {str(e)}')
    
    return render(request, 'staff/workout_form.html', {
        'categories': Workout.CATEGORY_CHOICES,
        'difficulties': Workout.DIFFICULTY_CHOICES,
        'action': 'Create'
    })


@login_required
def workout_edit(request, workout_id):
    """Edit a workout"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    workout = get_object_or_404(Workout, id=workout_id)
    
    if request.method == 'POST':
        workout.title = request.POST.get('title')
        workout.description = request.POST.get('description')
        workout.video_url = request.POST.get('video_url')
        workout.difficulty_level = request.POST.get('difficulty_level')
        workout.duration = request.POST.get('duration')
        workout.category = request.POST.get('category')
        
        try:
            workout.save()
            messages.success(request, f'Workout "{workout.title}" updated successfully!')
            return redirect('staff:workout_list')
        except Exception as e:
            messages.error(request, f'Error updating workout: {str(e)}')
    
    return render(request, 'staff/workout_form.html', {
        'workout': workout,
        'categories': Workout.CATEGORY_CHOICES,
        'difficulties': Workout.DIFFICULTY_CHOICES,
        'action': 'Edit'
    })


@login_required
def checkin_view(request):
    """QR code check-in page for staff"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    if request.method == 'POST':
        session_token = request.POST.get('session_token')
        
        if session_token:
            try:
                qr_session = QRCodeSession.objects.get(
                    session_token=session_token,
                    used_at__isnull=True
                )
                
                # Check if expired
                if qr_session.expires_at < timezone.now():
                    messages.error(request, 'This QR code has expired.')
                    return redirect('staff:checkin')
                
                # Mark as used
                qr_session.used_at = timezone.now()
                qr_session.save()
                
                # Award points for check-in (Phase 2)
                from core.utils import award_points_and_update_streak
                award_points_and_update_streak(
                    qr_session.user,
                    points=5,
                    source='checkin'
                )
                
                messages.success(request, f'Check-in successful! {qr_session.user.get_full_name()} scanned in.')
                return redirect('staff:checkin')
                
            except QRCodeSession.DoesNotExist:
                messages.error(request, 'Invalid or already used QR code.')
            except Exception as e:
                messages.error(request, f'Error processing check-in: {str(e)}')
    
    return render(request, 'staff/checkin.html')


# Trainer Portal Views
@login_required
def trainer_schedule(request):
    """View upcoming classes for a trainer"""
    if not hasattr(request.user, 'trainer_profile'):
        raise PermissionDenied("You must be a trainer to access this page.")
    
    trainer = request.user.trainer_profile
    today = timezone.now().date()
    
    upcoming_classes = GymClass.objects.filter(
        trainer=trainer,
        is_active=True
    ).order_by('schedule_time')
    
    # Get bookings for these classes
    for gym_class in upcoming_classes:
        gym_class.bookings_count = Booking.objects.filter(
            gym_class=gym_class,
            booking_date__gte=today,
            status='confirmed'
        ).count()
    
    return render(request, 'trainer/schedule.html', {
        'upcoming_classes': upcoming_classes,
        'trainer': trainer
    })


@login_required
def trainer_class_roster(request, class_id):
    """View and manage attendance for a specific class"""
    if not hasattr(request.user, 'trainer_profile'):
        raise PermissionDenied("You must be a trainer to access this page.")
    
    gym_class = get_object_or_404(GymClass, id=class_id, trainer=request.user.trainer_profile)
    
    # Get upcoming dates for this class
    today = timezone.now().date()
    bookings = Booking.objects.filter(
        gym_class=gym_class,
        booking_date__gte=today,
        status='confirmed'
    ).order_by('booking_date', 'user__first_name')
    
    return render(request, 'trainer/roster.html', {
        'gym_class': gym_class,
        'bookings': bookings
    })


@login_required
@require_POST
def mark_attendance(request, booking_id):
    """Mark a booking as attended or no show"""
    if not hasattr(request.user, 'trainer_profile'):
        raise PermissionDenied("You must be a trainer to access this page.")
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Verify this trainer teaches this class
    if booking.gym_class.trainer != request.user.trainer_profile:
        raise PermissionDenied("You can only mark attendance for your own classes.")
    
    action = request.POST.get('action')
    
    if action == 'attended':
        booking.status = 'completed'
        booking.save()
        
        # Award points for class attendance (Phase 2)
        from core.utils import award_points_and_update_streak
        award_points_and_update_streak(
            booking.user,
            points=15,
            source='class'
        )
        
        messages.success(request, f'{booking.user.get_full_name()} marked as attended.')
    elif action == 'no_show':
        booking.status = 'no_show'
        booking.save()
        messages.info(request, f'{booking.user.get_full_name()} marked as no show.')
    
    return redirect('trainer:class_roster', class_id=booking.gym_class.id)
