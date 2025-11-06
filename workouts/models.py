from django.db import models
from django.conf import settings

# Import Trainer from core app
try:
    from core.models import Trainer
except ImportError:
    Trainer = None


class Workout(models.Model):
    """Workout library entries"""
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    CATEGORY_CHOICES = [
        # Muscle Groups
        ('chest', 'Chest'),
        ('shoulder', 'Shoulder'),
        ('back', 'Back'),
        ('legs', 'Legs'),
        ('arms', 'Arms'),
        ('abs', 'Abs'),
        ('full_body', 'Full Body'),
        # Exercise Types
        ('cardio', 'Cardio'),
        ('strength', 'Strength Training'),
        ('flexibility', 'Flexibility'),
        ('hiit', 'HIIT'),
        ('yoga', 'Yoga'),
        ('pilates', 'Pilates'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    video_url = models.URLField(blank=True, null=True, help_text="URL to workout video or GIF")
    thumbnail = models.ImageField(upload_to='workout_thumbnails/', blank=True, null=True)
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    duration = models.IntegerField(help_text="Duration in minutes")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    is_free = models.BooleanField(default=False, help_text="If checked, this workout is free for all users")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'difficulty_level', 'title']
    
    @property
    def is_premium(self):
        """Backward compatibility property"""
        return not self.is_free
    
    def __str__(self):
        status = " (Free)" if self.is_free else " (Premium)"
        return f"{self.title}{status}"


class UserWorkoutCompletion(models.Model):
    """Track user workout completions"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workout_completions')
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='completions')
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-completed_at']
        unique_together = [['user', 'workout', 'completed_at']]
    
    def __str__(self):
        return f"{self.user.username} - {self.workout.title} on {self.completed_at.date()}"


class WorkoutPlan(models.Model):
    """A workout plan template created by a trainer"""
    trainer = models.ForeignKey(
        'core.Trainer', 
        on_delete=models.CASCADE, 
        related_name='workout_plans'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="A brief description of this plan's goals")
    
    # This links your existing Workout model
    workouts = models.ManyToManyField(
        Workout, 
        related_name='plans',
        help_text="Select the workouts to include in this plan"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (by {self.trainer.user.username})"


class UserWorkoutPlan(models.Model):
    """An instance of a plan assigned to a specific user by a trainer"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='assigned_plans'
    )
    plan = models.ForeignKey(
        WorkoutPlan, 
        on_delete=models.CASCADE, 
        related_name='assignments'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Specific notes for this user")

    class Meta:
        unique_together = [['user', 'plan']]
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"
