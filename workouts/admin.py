from django.contrib import admin
from .models import Workout, UserWorkoutCompletion


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    """Admin interface for Workout"""
    list_display = ['title', 'category', 'difficulty_level', 'duration', 'created_at']
    list_filter = ['category', 'difficulty_level', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['category', 'difficulty_level', 'title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Workout Information', {
            'fields': ('title', 'description', 'category', 'difficulty_level', 'duration')
        }),
        ('Media', {
            'fields': ('video_url', 'thumbnail')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(UserWorkoutCompletion)
class UserWorkoutCompletionAdmin(admin.ModelAdmin):
    """Admin interface for UserWorkoutCompletion"""
    list_display = ['user', 'workout', 'completed_at']
    list_filter = ['completed_at', 'workout__category']
    search_fields = ['user__username', 'workout__title']
    ordering = ['-completed_at']
    readonly_fields = ['completed_at']
