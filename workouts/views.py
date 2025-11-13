from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import date
from .models import Workout, UserWorkoutCompletion
from .utils import user_has_access_to_workout, get_accessible_workouts, can_view_workout_details
from core.utils import award_points_and_update_streak


def library(request):
    """Workout library"""
    # Get all workouts for filtering, but we'll check access per workout
    all_workouts = Workout.objects.all()
    
    # Filtering
    category = request.GET.get('category')
    difficulty = request.GET.get('difficulty')
    search = request.GET.get('search')
    
    if category:
        all_workouts = all_workouts.filter(category=category)
    if difficulty:
        all_workouts = all_workouts.filter(difficulty_level=difficulty)
    if search:
        all_workouts = all_workouts.filter(Q(title__icontains=search) | Q(description__icontains=search))
    
    # Separate free and premium workouts, and check access
    free_workouts = []
    premium_workouts = []
    
    for workout in all_workouts:
        has_access = user_has_access_to_workout(request.user, workout)
        can_view_details = can_view_workout_details(request.user, workout)
        workout_data = {
            'workout': workout,
            'has_access': has_access,
            'can_view_details': can_view_details
        }
        
        if workout.is_free:
            free_workouts.append(workout_data)
        else:
            premium_workouts.append(workout_data)
    
    context = {
        'free_workouts': free_workouts,
        'premium_workouts': premium_workouts,
        'categories': Workout.CATEGORY_CHOICES,
        'difficulties': Workout.DIFFICULTY_CHOICES,
        'selected_category': category,
        'selected_difficulty': difficulty,
        'search_query': search,
    }
    return render(request, 'workouts/library.html', context)


def workout_detail(request, workout_id):
    """Workout detail page"""
    workout = get_object_or_404(Workout, id=workout_id)
    
    # Check access
    has_access = user_has_access_to_workout(request.user, workout)
    can_view_details = can_view_workout_details(request.user, workout)
    
    # Check if user has completed this workout
    completed = False
    if request.user.is_authenticated:
        completed = UserWorkoutCompletion.objects.filter(
            user=request.user,
            workout=workout
        ).exists()
    
    context = {
        'workout': workout,
        'completed': completed,
        'has_access': has_access,
        'can_view_details': can_view_details,
    }
    return render(request, 'workouts/workout_detail.html', context)


@login_required
def workout_today(request):
    """What workout will you be doing today? - Category-based workout selection"""
    category = request.GET.get('category')
    today = timezone.now().date()
    
    # Get today's completed workouts
    completed_today = UserWorkoutCompletion.objects.filter(
        user=request.user,
        completed_at__date=today
    ).select_related('workout')
    
    if category:
        # Get workouts for selected category
        workouts = Workout.objects.filter(category=category)
        
        # Separate free and paid workouts
        free_workouts = []
        paid_workouts = []
        
        for workout in workouts:
            has_access = user_has_access_to_workout(request.user, workout)
            can_view_details = can_view_workout_details(request.user, workout)
            workout_data = {
                'workout': workout,
                'has_access': has_access,
                'can_view_details': can_view_details,
                'completed_today': completed_today.filter(workout=workout).exists()
            }
            
            if workout.is_free:
                free_workouts.append(workout_data)
            else:
                paid_workouts.append(workout_data)
        
        context = {
            'selected_category': category,
            'category_name': dict(Workout.CATEGORY_CHOICES).get(category, category),
            'free_workouts': free_workouts,
            'paid_workouts': paid_workouts,
            'completed_today': completed_today,
            'categories': Workout.CATEGORY_CHOICES,
        }
    else:
        # Show category selection
        context = {
            'categories': Workout.CATEGORY_CHOICES,
            'completed_today': completed_today,
        }
    
    return render(request, 'workouts/workout_today.html', context)


@login_required
def mark_completed(request, workout_id):
    """Mark workout as completed"""
    workout = get_object_or_404(Workout, id=workout_id)
    redirect_to = request.GET.get('redirect_to', 'workout_detail')
    
    # Check access before allowing completion
    if not user_has_access_to_workout(request.user, workout):
        messages.error(request, 'You do not have access to this workout. Please upgrade your subscription.')
        if redirect_to == 'workout_today':
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(f"{reverse('workouts:workout_today')}?category={workout.category}")
        return redirect('workouts:workout_detail', workout_id=workout_id)
    
    # Create completion record (only once per day)
    today = timezone.now().date()
    created = UserWorkoutCompletion.objects.filter(
        user=request.user,
        workout=workout,
        completed_at__date=today
    ).exists()
    
    if not created:
        UserWorkoutCompletion.objects.create(
            user=request.user,
            workout=workout
        )
        
        # Award points and update streak
        award_points_and_update_streak(
            request.user,
            points=10,
            source='workout',
            description=f'Completed {workout.title}'
        )
        messages.success(request, f'Congratulations! You completed {workout.title}.')
    else:
        messages.info(request, f'You have already completed {workout.title} today.')
    
    if redirect_to == 'workout_today':
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(f"{reverse('workouts:workout_today')}?category={workout.category}")
    return redirect('workouts:workout_detail', workout_id=workout_id)
