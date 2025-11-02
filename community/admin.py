from django.contrib import admin
from .models import Post, Comment, Like, Challenge, UserChallenge


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin interface for Post"""
    list_display = ['user', 'content_preview', 'likes_count', 'created_at']
    list_filter = ['created_at', 'likes_count']
    search_fields = ['user__username', 'content']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'likes_count']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for Comment"""
    list_display = ['user', 'post', 'content_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'content', 'post__content']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def content_preview(self, obj):
        return obj.content[:30] + '...' if len(obj.content) > 30 else obj.content
    content_preview.short_description = 'Content'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    """Admin interface for Like"""
    list_display = ['user', 'post', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__content']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    """Admin interface for Challenge"""
    list_display = ['name', 'goal_type', 'start_date', 'end_date', 'is_active', 'created_at']
    list_filter = ['goal_type', 'start_date', 'end_date', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-start_date']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Challenge Information', {
            'fields': ('name', 'description', 'goal_type', 'goal_value')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(UserChallenge)
class UserChallengeAdmin(admin.ModelAdmin):
    """Admin interface for UserChallenge"""
    list_display = ['user', 'challenge', 'progress', 'joined_at']
    list_filter = ['challenge', 'joined_at']
    search_fields = ['user__username', 'challenge__name']
    ordering = ['-progress', '-joined_at']
    readonly_fields = ['joined_at', 'updated_at']
