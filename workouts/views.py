from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Workout, UserWorkoutCompletion


def library(request):
    """Workout library"""
    workouts = Workout.objects.all()
    
    # Filtering
    category = request.GET.get('category')
    difficulty = request.GET.get('difficulty')
    search = request.GET.get('search')
    
    if category:
        workouts = workouts.filter(category=category)
    if difficulty:
        workouts = workouts.filter(difficulty_level=difficulty)
    if search:
        workouts = workouts.filter(Q(title__icontains=search) | Q(description__icontains=search))
    
    context = {
        'workouts': workouts,
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
    }
    return render(request, 'workouts/workout_detail.html', context)


@login_required
def mark_completed(request, workout_id):
    """Mark workout as completed"""
    workout = get_object_or_404(Workout, id=workout_id)
    
    # Create completion record
    UserWorkoutCompletion.objects.get_or_create(
        user=request.user,
        workout=workout
    )
    
    messages.success(request, f'Congratulations! You completed {workout.title}.')
    return redirect('workouts:workout_detail', workout_id=workout_id)
