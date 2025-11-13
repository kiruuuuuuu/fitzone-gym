from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from datetime import datetime, timedelta
from .mixins import StaffRequiredMixin, TrainerRequiredMixin, SuperuserRequiredMixin

from core.models import CustomUser, MembershipPlan, Subscription, Trainer, UserPoints, QRCodeSession, PlanFeature, PersonalTrainerSubscription
from bookings.models import GymClass, Booking, ClassSchedule
from workouts.models import Workout, WorkoutPlan, UserWorkoutPlan, TrainerAssignedWorkout
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
    
    # Get all plans for subscription management
    all_plans = MembershipPlan.objects.filter(is_active=True).order_by('price')
    
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
        'all_plans': all_plans,
    }
    
    return render(request, 'staff/member_detail.html', context)


@login_required
@require_POST
def add_manual_points(request, user_id):
    """Add manual points to a member"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    member = get_object_or_404(CustomUser, id=user_id, is_staff=False)
    
    points = request.POST.get('points')
    description = request.POST.get('description')
    
    if points:
        try:
            points_value = int(points)
            from core.utils import award_points_and_update_streak
            award_points_and_update_streak(
                member,
                points=points_value,
                source='class',  # Using 'class' as source for manual points
                description=description or 'Manual bonus points'
            )
            messages.success(request, f'Added {points_value} points to {member.get_full_name()}')
        except ValueError:
            messages.error(request, 'Invalid points value')
        except Exception as e:
            messages.error(request, f'Error adding points: {str(e)}')
    
    return redirect('staff:member_detail', user_id=user_id)


@login_required
@require_POST
def manage_subscription(request, user_id):
    """Manually manage a member's subscription"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    member = get_object_or_404(CustomUser, id=user_id, is_staff=False)
    
    action = request.POST.get('action')
    
    if action == 'create':
        plan_id = request.POST.get('plan_id')
        if plan_id:
            try:
                plan = MembershipPlan.objects.get(id=plan_id)
                Subscription.objects.create(
                    user=member,
                    plan=plan,
                    status='active',
                    current_period_start=timezone.now(),
                    current_period_end=timezone.now() + timedelta(days=30)
                )
                messages.success(request, f'Active subscription created for {member.get_full_name()}')
            except MembershipPlan.DoesNotExist:
                messages.error(request, 'Invalid plan selected')
            except Exception as e:
                messages.error(request, f'Error creating subscription: {str(e)}')
    
    elif action == 'cancel':
        subscription_id = request.POST.get('subscription_id')
        if subscription_id:
            try:
                subscription = Subscription.objects.get(id=subscription_id, user=member)
                subscription.status = 'cancelled'
                subscription.save()
                messages.success(request, f'Subscription cancelled for {member.get_full_name()}')
            except Subscription.DoesNotExist:
                messages.error(request, 'Invalid subscription')
            except Exception as e:
                messages.error(request, f'Error cancelling subscription: {str(e)}')
    
    return redirect('staff:member_detail', user_id=user_id)


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
        features = request.POST.get('features', '')  # Keep for backward compatibility
        is_active = request.POST.get('is_active') == 'on'
        duration = request.POST.get('duration', '1_month')
        
        if name and price:
            try:
                plan = MembershipPlan.objects.create(
                    name=name,
                    price=price,
                    features=features,  # Keep old field for backward compatibility
                    is_active=is_active,
                    duration=duration
                )
                
                # Handle structured features
                feature_texts = request.POST.getlist('feature_text[]')
                feature_icons = request.POST.getlist('feature_icon[]')
                feature_highlighted = request.POST.getlist('feature_highlighted[]')
                
                for idx, (text, icon) in enumerate(zip(feature_texts, feature_icons)):
                    if text.strip():  # Only create if feature text is not empty
                        PlanFeature.objects.create(
                            plan=plan,
                            feature_text=text.strip(),
                            icon=icon.strip(),
                            order=idx,
                            is_highlighted=str(idx) in feature_highlighted
                        )
                
                # Handle included workouts
                workout_ids = request.POST.getlist('included_workouts')
                if workout_ids:
                    plan.included_workouts.set(workout_ids)
                
                messages.success(request, f'Plan "{plan.name}" created successfully!')
                return redirect('staff:plan_list')
            except Exception as e:
                messages.error(request, f'Error creating plan: {str(e)}')
    
    all_workouts = Workout.objects.all().order_by('category', 'difficulty_level', 'title')
    return render(request, 'staff/plan_form.html', {
        'action': 'Create',
        'existing_features': [],
        'all_workouts': all_workouts
    })


@login_required
def plan_edit(request, plan_id):
    """Edit a membership plan"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    plan = get_object_or_404(MembershipPlan, id=plan_id)
    
    if request.method == 'POST':
        plan.name = request.POST.get('name')
        plan.price = request.POST.get('price')
        plan.features = request.POST.get('features', '')  # Keep for backward compatibility
        plan.is_active = request.POST.get('is_active') == 'on'
        plan.duration = request.POST.get('duration', '1_month')
        
        try:
            plan.save()
            
            # Delete existing structured features and recreate
            plan.plan_features.all().delete()
            
            # Handle structured features
            feature_texts = request.POST.getlist('feature_text[]')
            feature_icons = request.POST.getlist('feature_icon[]')
            feature_highlighted = request.POST.getlist('feature_highlighted[]')
            
            for idx, (text, icon) in enumerate(zip(feature_texts, feature_icons)):
                if text.strip():  # Only create if feature text is not empty
                    PlanFeature.objects.create(
                        plan=plan,
                        feature_text=text.strip(),
                        icon=icon.strip(),
                        order=idx,
                        is_highlighted=str(idx) in feature_highlighted
                    )
            
            # Handle included workouts
            workout_ids = request.POST.getlist('included_workouts')
            plan.included_workouts.set(workout_ids)
            
            messages.success(request, f'Plan "{plan.name}" updated successfully!')
            return redirect('staff:plan_list')
        except Exception as e:
            messages.error(request, f'Error updating plan: {str(e)}')
    
    # Get existing structured features
    existing_features = plan.plan_features.all() if plan else []
    all_workouts = Workout.objects.all().order_by('category', 'difficulty_level', 'title')
    
    return render(request, 'staff/plan_form.html', {
        'plan': plan, 
        'action': 'Edit',
        'existing_features': existing_features,
        'all_workouts': all_workouts
    })


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
        is_paid = request.POST.get('is_paid') == 'true'
        price = request.POST.get('price')
        location_type = request.POST.get('location_type', 'offline')
        location_details = request.POST.get('location_details', '')
        is_active = request.POST.get('is_active') == 'on'
        
        # Get schedule dates and times
        schedule_dates = request.POST.getlist('schedule_date[]')
        schedule_times = request.POST.getlist('schedule_time[]')
        
        # Validation
        if not name or not duration or not max_capacity:
            messages.error(request, 'Name, duration, and max capacity are required.')
            return render(request, 'staff/class_form.html', {'trainers': trainers, 'action': 'Create'})
        
        if is_paid and (not price or float(price) <= 0):
            messages.error(request, 'Price is required for paid classes.')
            return render(request, 'staff/class_form.html', {'trainers': trainers, 'action': 'Create'})
        
        if len(schedule_dates) == 0 or len(schedule_dates) > 3:
            messages.error(request, 'Please add 1-3 schedule entries.')
            return render(request, 'staff/class_form.html', {'trainers': trainers, 'action': 'Create'})
        
        try:
            from django.db import transaction
            from datetime import datetime
            
            with transaction.atomic():
                trainer = Trainer.objects.get(id=trainer_id) if trainer_id else None
                gym_class = GymClass.objects.create(
                    name=name,
                    description=description,
                    trainer=trainer,
                    duration=int(duration),
                    max_capacity=int(max_capacity),
                    is_paid=is_paid,
                    price=float(price) if is_paid and price else None,
                    location_type=location_type,
                    location_details=location_details,
                    is_active=is_active
                )
                
                # Create ClassSchedule entries
                for date_str, time_str in zip(schedule_dates, schedule_times):
                    if date_str and time_str:
                        ClassSchedule.objects.create(
                            gym_class=gym_class,
                            class_date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                            class_time=datetime.strptime(time_str, '%H:%M').time(),
                            is_active=True
                        )
                
                messages.success(request, f'Class "{name}" created successfully with {len(schedule_dates)} schedule(s)!')
                return redirect('staff:class_list')
        except ValueError as e:
            messages.error(request, f'Invalid date or time format: {str(e)}')
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
        gym_class.duration = int(request.POST.get('duration'))
        gym_class.max_capacity = int(request.POST.get('max_capacity'))
        is_paid = request.POST.get('is_paid') == 'true'
        price = request.POST.get('price')
        location_type = request.POST.get('location_type', 'offline')
        location_details = request.POST.get('location_details', '')
        gym_class.is_active = request.POST.get('is_active') == 'on'
        
        # Get schedule dates and times
        schedule_dates = request.POST.getlist('schedule_date[]')
        schedule_times = request.POST.getlist('schedule_time[]')
        
        # Validation
        if is_paid and (not price or float(price) <= 0):
            messages.error(request, 'Price is required for paid classes.')
            return render(request, 'staff/class_form.html', {'gym_class': gym_class, 'trainers': trainers, 'action': 'Edit'})
        
        if len(schedule_dates) == 0 or len(schedule_dates) > 3:
            messages.error(request, 'Please add 1-3 schedule entries.')
            return render(request, 'staff/class_form.html', {'gym_class': gym_class, 'trainers': trainers, 'action': 'Edit'})
        
        try:
            from django.db import transaction
            from datetime import datetime
            
            with transaction.atomic():
                gym_class.trainer = Trainer.objects.get(id=trainer_id) if trainer_id else None
                gym_class.is_paid = is_paid
                gym_class.price = float(price) if is_paid and price else None
                gym_class.location_type = location_type
                gym_class.location_details = location_details
                gym_class.save()
                
                # Delete existing schedules and create new ones
                ClassSchedule.objects.filter(gym_class=gym_class).delete()
                
                # Create new ClassSchedule entries
                for date_str, time_str in zip(schedule_dates, schedule_times):
                    if date_str and time_str:
                        ClassSchedule.objects.create(
                            gym_class=gym_class,
                            class_date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                            class_time=datetime.strptime(time_str, '%H:%M').time(),
                            is_active=True
                        )
                
                messages.success(request, f'Class "{gym_class.name}" updated successfully with {len(schedule_dates)} schedule(s)!')
                return redirect('staff:class_list')
        except ValueError as e:
            messages.error(request, f'Invalid date or time format: {str(e)}')
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
    """Create workouts - step 1: select category, step 2: create multiple workouts"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    # Step 1: Category selection
    if request.method == 'GET' and not request.GET.get('category'):
        return render(request, 'staff/workout_form.html', {
            'step': 'category',
            'categories': Workout.CATEGORY_CHOICES,
            'action': 'Create'
        })
    
    # Step 2: Bulk workout creation
    selected_category = request.GET.get('category') or request.POST.get('category')
    
    if request.method == 'POST' and selected_category:
        # Get all workout data from form arrays
        titles = request.POST.getlist('workout_title[]')
        descriptions = request.POST.getlist('workout_description[]')
        is_free_list = request.POST.getlist('workout_is_free[]')
        difficulty_levels = request.POST.getlist('workout_difficulty[]')
        sets_list = request.POST.getlist('workout_sets[]')
        video_urls = request.POST.getlist('workout_video_url[]')
        
        # Get thumbnail files
        thumbnails = request.FILES.getlist('workout_thumbnail[]')
        
        created_count = 0
        errors = []
        
        try:
            from django.db import transaction
            
            with transaction.atomic():
                for idx, title in enumerate(titles):
                    if not title.strip():
                        continue  # Skip empty entries
                    
                    try:
                        workout = Workout.objects.create(
                            title=title.strip(),
                            description=descriptions[idx].strip() if idx < len(descriptions) else '',
                            category=selected_category,
                            is_free=is_free_list[idx] == 'true' if idx < len(is_free_list) else True,
                            difficulty_level=difficulty_levels[idx] if idx < len(difficulty_levels) else '1',
                            sets=int(sets_list[idx]) if idx < len(sets_list) and sets_list[idx] else 1,
                            video_url=video_urls[idx].strip() if idx < len(video_urls) and video_urls[idx] else '',
                            thumbnail=thumbnails[idx] if idx < len(thumbnails) and thumbnails[idx] else None
                        )
                        created_count += 1
                    except Exception as e:
                        errors.append(f"Error creating workout '{title}': {str(e)}")
                
                if created_count > 0:
                    messages.success(request, f'Successfully created {created_count} workout(s) in category "{dict(Workout.CATEGORY_CHOICES).get(selected_category, selected_category)}"!')
                    if errors:
                        for error in errors:
                            messages.warning(request, error)
                    return redirect('staff:workout_list')
                else:
                    messages.error(request, 'No workouts were created. Please fill in at least one workout form.')
        except Exception as e:
            messages.error(request, f'Error creating workouts: {str(e)}')
    
    # Render step 2 form
    return render(request, 'staff/workout_form.html', {
        'step': 'create',
        'selected_category': selected_category,
        'category_name': dict(Workout.CATEGORY_CHOICES).get(selected_category, selected_category),
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
        workout.sets = int(request.POST.get('sets', 1))
        workout.category = request.POST.get('category')
        workout.is_free = request.POST.get('is_free', 'true') == 'true'  # Default to free if not specified
        
        # Handle thumbnail upload
        if 'thumbnail' in request.FILES:
            workout.thumbnail = request.FILES['thumbnail']
        
        try:
            workout.save()
            messages.success(request, f'Workout "{workout.title}" updated successfully!')
            return redirect('staff:workout_list')
        except Exception as e:
            messages.error(request, f'Error updating workout: {str(e)}')
    
    return render(request, 'staff/workout_form_edit.html', {
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


# Reports Dashboard
@login_required
def reports_dashboard(request):
    """Analytics and reporting dashboard"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    # MRR (Monthly Recurring Revenue)
    active_subs = Subscription.objects.filter(status='active')
    total_mrr = sum([sub.plan.price for sub in active_subs if sub.plan])
    
    # Member growth (last 12 months)
    today = timezone.now().date()
    member_growth = []
    for i in range(11, -1, -1):
        month_start = today.replace(day=1) - timedelta(days=30*i)
        month_end = month_start.replace(day=28) + timedelta(days=10)
        month_end = month_end.replace(day=min(28, month_end.day))
        
        if i > 0:
            next_month_start = today.replace(day=1) - timedelta(days=30*(i-1))
            month_end = next_month_start - timedelta(days=1)
        
        count = CustomUser.objects.filter(
            is_staff=False,
            created_at__date__gte=month_start,
            created_at__date__lte=month_end
        ).count()
        member_growth.append({
            'month': month_start.strftime('%b %Y'),
            'count': count
        })
    
    # Class popularity
    class_popularity = GymClass.objects.annotate(
        bookings_count=Count('bookings', filter=Q(bookings__status='confirmed'))
    ).order_by('-bookings_count')[:10]
    
    # Trainer performance
    trainer_performance = []
    for trainer in Trainer.objects.all():
        classes_taught = GymClass.objects.filter(trainer=trainer).count()
        total_attendance = Booking.objects.filter(
            gym_class__trainer=trainer,
            status='completed'
        ).count()
        trainer_performance.append({
            'name': trainer.user.get_full_name(),
            'classes_taught': classes_taught,
            'attendance': total_attendance
        })
    trainer_performance = sorted(trainer_performance, key=lambda x: x['attendance'], reverse=True)[:10]
    
    # Active vs Inactive members
    active_members = CustomUser.objects.filter(is_staff=False, is_active=True).count()
    inactive_members = CustomUser.objects.filter(is_staff=False, is_active=False).count()
    
    context = {
        'total_mrr': total_mrr,
        'member_growth': member_growth,
        'class_popularity': class_popularity,
        'trainer_performance': trainer_performance,
        'active_members': active_members,
        'inactive_members': inactive_members,
    }
    
    return render(request, 'staff/reports.html', context)


# Trainer Management Views
@method_decorator(login_required, name='dispatch')
class TrainerListView(StaffRequiredMixin, ListView):
    """List all trainers"""
    template_name = 'staff/trainer_list.html'
    context_object_name = 'trainers'
    model = Trainer


@login_required
def trainer_create(request):
    """Create a new trainer - can create new user or use existing user"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    # Get users who don't already have a trainer profile
    existing_trainer_user_ids = Trainer.objects.values_list('user_id', flat=True)
    available_users = CustomUser.objects.exclude(id__in=existing_trainer_user_ids)
    
    if request.method == 'POST':
        user_type = request.POST.get('user_type', 'existing')  # 'existing' or 'new'
        bio = request.POST.get('bio')
        specializations = request.POST.get('specializations')
        
        try:
            from django.db import transaction
            
            with transaction.atomic():
                if user_type == 'new':
                    # Create new user
                    username = request.POST.get('username')
                    password = request.POST.get('password')
                    email = request.POST.get('email', '')
                    first_name = request.POST.get('first_name', '')
                    last_name = request.POST.get('last_name', '')
                    
                    # Validation
                    if not username or not password:
                        messages.error(request, 'Username and password are required when creating a new user.')
                        return render(request, 'staff/trainer_form.html', {
                            'available_users': available_users,
                            'action': 'Create'
                        })
                    
                    if CustomUser.objects.filter(username=username).exists():
                        messages.error(request, 'Username already exists.')
                        return render(request, 'staff/trainer_form.html', {
                            'available_users': available_users,
                            'action': 'Create'
                        })
                    
                    if email and CustomUser.objects.filter(email=email).exists():
                        messages.error(request, 'Email already exists.')
                        return render(request, 'staff/trainer_form.html', {
                            'available_users': available_users,
                            'action': 'Create'
                        })
                    
                    # Create the user
                    user = CustomUser.objects.create_user(
                        username=username,
                        email=email if email else None,
                        password=password,
                        first_name=first_name,
                        last_name=last_name
                    )
                else:
                    # Use existing user
                    user_id = request.POST.get('user')
                    if not user_id:
                        messages.error(request, 'Please select a user or create a new one.')
                        return render(request, 'staff/trainer_form.html', {
                            'available_users': available_users,
                            'action': 'Create'
                        })
                    
                    user = CustomUser.objects.get(id=user_id)
                    # Check if user already has a trainer profile
                    if hasattr(user, 'trainer_profile'):
                        messages.error(request, 'This user already has a trainer profile.')
                        return render(request, 'staff/trainer_form.html', {
                            'available_users': available_users,
                            'action': 'Create'
                        })
                
                # Create trainer profile
                Trainer.objects.create(
                    user=user,
                    bio=bio,
                    specializations=specializations
                )
                messages.success(request, f'Trainer created successfully for {user.get_full_name() or user.username}!')
                return redirect('staff:trainer_list')
                
        except CustomUser.DoesNotExist:
            messages.error(request, 'Invalid user selected.')
        except Exception as e:
            messages.error(request, f'Error creating trainer: {str(e)}')
    
    return render(request, 'staff/trainer_form.html', {
        'available_users': available_users,
        'action': 'Create'
    })


@login_required
def trainer_edit(request, trainer_id):
    """Edit a trainer"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    trainer = get_object_or_404(Trainer, id=trainer_id)
    
    if request.method == 'POST':
        trainer.bio = request.POST.get('bio')
        trainer.specializations = request.POST.get('specializations')
        
        try:
            trainer.save()
            messages.success(request, f'Trainer updated successfully!')
            return redirect('staff:trainer_list')
        except Exception as e:
            messages.error(request, f'Error updating trainer: {str(e)}')
    
    return render(request, 'staff/trainer_form.html', {
        'trainer': trainer,
        'action': 'Edit'
    })


# Challenge Management Views
@method_decorator(login_required, name='dispatch')
class ChallengeListView(StaffRequiredMixin, ListView):
    """List all challenges"""
    template_name = 'staff/challenge_list.html'
    context_object_name = 'challenges'
    model = Challenge


@login_required
def challenge_create(request):
    """Create a new challenge"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        goal_type = request.POST.get('goal_type')
        goal_value = request.POST.get('goal_value')
        
        if name and description and start_date and end_date and goal_type:
            try:
                challenge = Challenge.objects.create(
                    name=name,
                    description=description,
                    start_date=start_date,
                    end_date=end_date,
                    goal_type=goal_type,
                    goal_value=int(goal_value) if goal_value else None
                )
                messages.success(request, f'Challenge "{challenge.name}" created successfully!')
                return redirect('staff:challenge_list')
            except Exception as e:
                messages.error(request, f'Error creating challenge: {str(e)}')
    
    return render(request, 'staff/challenge_form.html', {
        'goal_types': Challenge.GOAL_TYPES,
        'action': 'Create'
    })


@login_required
def challenge_edit(request, challenge_id):
    """Edit a challenge"""
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    
    challenge = get_object_or_404(Challenge, id=challenge_id)
    
    if request.method == 'POST':
        challenge.name = request.POST.get('name')
        challenge.description = request.POST.get('description')
        challenge.start_date = request.POST.get('start_date')
        challenge.end_date = request.POST.get('end_date')
        challenge.goal_type = request.POST.get('goal_type')
        challenge.goal_value = request.POST.get('goal_value')
        
        try:
            challenge.goal_value = int(challenge.goal_value) if challenge.goal_value else None
            challenge.save()
            messages.success(request, f'Challenge "{challenge.name}" updated successfully!')
            return redirect('staff:challenge_list')
        except Exception as e:
            messages.error(request, f'Error updating challenge: {str(e)}')
    
    return render(request, 'staff/challenge_form.html', {
        'challenge': challenge,
        'goal_types': Challenge.GOAL_TYPES,
        'action': 'Edit'
    })


# Staff User Management Views (Admin Only)
@method_decorator(login_required, name='dispatch')
class StaffUserListView(SuperuserRequiredMixin, ListView):
    """List all users (staff and members) for staff management - Admin only"""
    template_name = 'staff/staff_user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        queryset = CustomUser.objects.all()
        
        # Filter by staff status
        staff_filter = self.request.GET.get('filter')
        if staff_filter == 'staff':
            queryset = queryset.filter(is_staff=True)
        elif staff_filter == 'members':
            queryset = queryset.filter(is_staff=False)
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        return queryset.order_by('-is_staff', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['filter'] = self.request.GET.get('filter', 'all')
        context['total_staff'] = CustomUser.objects.filter(is_staff=True).count()
        context['total_members'] = CustomUser.objects.filter(is_staff=False).count()
        return context


@login_required
def staff_user_create(request):
    """Create a new staff user - Admin only"""
    if not request.user.is_superuser:
        raise PermissionDenied("You must be an administrator to create staff users.")
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        is_staff = request.POST.get('is_staff') == 'on'
        is_active = request.POST.get('is_active', 'on') == 'on'
        
        # Validation
        if not username or not password:
            messages.error(request, 'Username and password are required.')
        elif password != password_confirm:
            messages.error(request, 'Passwords do not match.')
        elif CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif email and CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        else:
            try:
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email if email else None,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=is_staff,
                    is_active=is_active
                )
                messages.success(request, f'User "{user.username}" created successfully!')
                return redirect('staff:staff_user_list')
            except Exception as e:
                messages.error(request, f'Error creating user: {str(e)}')
    
    return render(request, 'staff/staff_user_form.html', {'action': 'Create'})


@login_required
@require_POST
def toggle_staff_status(request, user_id):
    """Toggle staff status for an existing user - Admin only"""
    if not request.user.is_superuser:
        raise PermissionDenied("You must be an administrator to change staff status.")
    
    # Prevent users from removing their own staff status
    if request.user.id == int(user_id):
        messages.error(request, 'You cannot change your own staff status.')
        return redirect('staff:staff_user_list')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Toggle staff status
    user.is_staff = not user.is_staff
    user.save()
    
    status = 'staff member' if user.is_staff else 'regular member'
    messages.success(request, f'User "{user.username}" is now a {status}.')
    
    return redirect('staff:staff_user_list')


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


# Trainer Workout Plan Views
@method_decorator(login_required, name='dispatch')
class TrainerPlanListView(TrainerRequiredMixin, ListView):
    """List all workout plans created by the trainer"""
    template_name = 'trainer/plan_list.html'
    context_object_name = 'plans'

    def get_queryset(self):
        return WorkoutPlan.objects.filter(trainer=self.request.user.trainer_profile)


@login_required
def trainer_plan_create(request):
    """Create a new workout plan"""
    if not hasattr(request.user, 'trainer_profile'):
        raise PermissionDenied("You must be a trainer to access this page.")
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        workout_ids = request.POST.getlist('workouts')
        
        if name:
            try:
                plan = WorkoutPlan.objects.create(
                    trainer=request.user.trainer_profile,
                    name=name,
                    description=description
                )
                # Add selected workouts to the plan
                if workout_ids:
                    plan.workouts.set(workout_ids)
                
                messages.success(request, f'Workout plan "{plan.name}" created successfully!')
                return redirect('trainer:plan_list')
            except Exception as e:
                messages.error(request, f'Error creating workout plan: {str(e)}')
    
    workouts = Workout.objects.all().order_by('category', 'difficulty_level', 'title')
    return render(request, 'trainer/plan_form.html', {
        'workouts': workouts,
        'action': 'Create'
    })


@login_required
def trainer_plan_edit(request, plan_id):
    """Edit a workout plan"""
    if not hasattr(request.user, 'trainer_profile'):
        raise PermissionDenied("You must be a trainer to access this page.")
    
    plan = get_object_or_404(WorkoutPlan, id=plan_id, trainer=request.user.trainer_profile)
    
    if request.method == 'POST':
        plan.name = request.POST.get('name')
        plan.description = request.POST.get('description')
        workout_ids = request.POST.getlist('workouts')
        
        try:
            plan.save()
            # Update selected workouts
            if workout_ids:
                plan.workouts.set(workout_ids)
            else:
                plan.workouts.clear()
            
            messages.success(request, f'Workout plan "{plan.name}" updated successfully!')
            return redirect('trainer:plan_list')
        except Exception as e:
            messages.error(request, f'Error updating workout plan: {str(e)}')
    
    workouts = Workout.objects.all().order_by('category', 'difficulty_level', 'title')
    return render(request, 'trainer/plan_form.html', {
        'plan': plan,
        'workouts': workouts,
        'action': 'Edit'
    })


@login_required
def trainer_plan_assign(request, plan_id):
    """Assign a workout plan to a member"""
    if not hasattr(request.user, 'trainer_profile'):
        raise PermissionDenied("You must be a trainer to access this page.")
    
    plan = get_object_or_404(WorkoutPlan, id=plan_id, trainer=request.user.trainer_profile)
    
    if request.method == 'POST':
        user_id = request.POST.get('user')
        notes = request.POST.get('notes')
        
        if user_id:
            try:
                user = CustomUser.objects.get(id=user_id, is_staff=False)
                
                # Check if already assigned
                existing = UserWorkoutPlan.objects.filter(user=user, plan=plan).first()
                if existing:
                    messages.error(request, f'{user.get_full_name()} already has this plan assigned.')
                    return redirect('trainer:plan_assign', plan_id=plan_id)
                
                UserWorkoutPlan.objects.create(
                    user=user,
                    plan=plan,
                    notes=notes
                )
                
                messages.success(request, f'Workout plan assigned to {user.get_full_name()}!')
                return redirect('trainer:plan_list')
            except CustomUser.DoesNotExist:
                messages.error(request, 'Invalid user selected.')
            except Exception as e:
                messages.error(request, f'Error assigning plan: {str(e)}')
    
    # Get all non-staff members
    members = CustomUser.objects.filter(is_staff=False).order_by('first_name', 'last_name')
    return render(request, 'trainer/plan_assign.html', {
        'plan': plan,
        'members': members
    })


@login_required
def trainer_assign_workout(request):
    """Assign individual workouts to clients who have selected this trainer"""
    if not hasattr(request.user, 'trainer_profile'):
        raise PermissionDenied("You must be a trainer to access this page.")
    
    trainer = request.user.trainer_profile
    
    # Get clients who have selected this trainer (active subscriptions)
    client_subscriptions = PersonalTrainerSubscription.objects.filter(
        trainer=trainer,
        status='active'
    ).select_related('user')
    
    clients = [sub.user for sub in client_subscriptions]
    
    if request.method == 'POST':
        user_id = request.POST.get('user')
        workout_id = request.POST.get('workout')
        notes = request.POST.get('notes', '')
        
        if user_id and workout_id:
            try:
                user = CustomUser.objects.get(id=user_id, is_staff=False)
                workout = Workout.objects.get(id=workout_id)
                
                # Verify this user is a client of this trainer
                if user not in clients:
                    messages.error(request, 'You can only assign workouts to your clients.')
                    return redirect('trainer:assign_workout')
                
                # Check if already assigned
                existing = TrainerAssignedWorkout.objects.filter(
                    trainer=trainer,
                    user=user,
                    workout=workout
                ).first()
                
                if existing:
                    # Update notes if assignment exists
                    existing.notes = notes
                    existing.save()
                    messages.success(request, f'Workout assignment updated for {user.get_full_name()}!')
                else:
                    # Create new assignment
                    TrainerAssignedWorkout.objects.create(
                        trainer=trainer,
                        user=user,
                        workout=workout,
                        notes=notes
                    )
                    messages.success(request, f'Workout "{workout.title}" assigned to {user.get_full_name()}!')
                
                return redirect('trainer:assign_workout')
            except CustomUser.DoesNotExist:
                messages.error(request, 'Invalid user selected.')
            except Workout.DoesNotExist:
                messages.error(request, 'Invalid workout selected.')
            except Exception as e:
                messages.error(request, f'Error assigning workout: {str(e)}')
    
    # Get all workouts (trainers have access to all)
    workouts = Workout.objects.all().order_by('category', 'title')
    
    # Get existing assignments for display
    existing_assignments = TrainerAssignedWorkout.objects.filter(
        trainer=trainer
    ).select_related('user', 'workout').order_by('-assigned_at')[:20]
    
    return render(request, 'trainer/assign_workout.html', {
        'trainer': trainer,
        'clients': clients,
        'workouts': workouts,
        'existing_assignments': existing_assignments,
    })
