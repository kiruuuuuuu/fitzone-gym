from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Workout, UserWorkoutCompletion
from .utils import user_has_access_to_workout, get_accessible_workouts
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
        workout_data = {
            'workout': workout,
            'has_access': has_access
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
    }
    return render(request, 'workouts/workout_detail.html', context)


@login_required
def mark_completed(request, workout_id):
    """Mark workout as completed"""
    workout = get_object_or_404(Workout, id=workout_id)
    
    # Check access before allowing completion
    if not user_has_access_to_workout(request.user, workout):
        messages.error(request, 'You do not have access to this workout. Please upgrade your subscription.')
        return redirect('workouts:workout_detail', workout_id=workout_id)
    
    # Create completion record
    created = UserWorkoutCompletion.objects.get_or_create(
        user=request.user,
        workout=workout
    )[1]
    
    # Award points and update streak if not already completed
    if created:
        award_points_and_update_streak(
            request.user,
            points=10,
            source='workout',
            description=f'Completed {workout.title}'
        )
    
    messages.success(request, f'Congratulations! You completed {workout.title}.')
    return redirect('workouts:workout_detail', workout_id=workout_id)
