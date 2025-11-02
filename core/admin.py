from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, MembershipPlan, Subscription, Trainer, UserPoints, UserStreak, QRCodeSession


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin interface for CustomUser"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'created_at']
    list_filter = ['is_staff', 'is_active', 'is_superuser', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': ('phone_number', 'date_of_birth', 'profile_picture', 'stripe_customer_id')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields': ('phone_number', 'date_of_birth', 'profile_picture')
        }),
    )


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    """Admin interface for MembershipPlan"""
    list_display = ['name', 'price', 'is_active', 'stripe_price_id', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'stripe_price_id']
    ordering = ['price']
    fieldsets = (
        ('Plan Information', {
            'fields': ('name', 'price', 'features', 'is_active')
        }),
        ('Stripe Integration', {
            'fields': ('stripe_price_id',)
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin interface for Subscription"""
    list_display = ['user', 'plan', 'status', 'current_period_start', 'current_period_end', 'created_at']
    list_filter = ['status', 'created_at', 'current_period_start']
    search_fields = ['user__username', 'user__email', 'plan__name', 'stripe_subscription_id']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Subscription Information', {
            'fields': ('user', 'plan', 'status')
        }),
        ('Stripe Information', {
            'fields': ('stripe_subscription_id', 'current_period_start', 'current_period_end')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    """Admin interface for Trainer"""
    list_display = ['user', 'get_email', 'specializations', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'specializations']
    ordering = ['user__username']
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'


@admin.register(UserPoints)
class UserPointsAdmin(admin.ModelAdmin):
    """Admin interface for UserPoints"""
    list_display = ['user', 'points', 'source', 'description', 'created_at']
    list_filter = ['source', 'created_at']
    search_fields = ['user__username', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(UserStreak)
class UserStreakAdmin(admin.ModelAdmin):
    """Admin interface for UserStreak"""
    list_display = ['user', 'current_streak', 'longest_streak', 'last_activity_date', 'updated_at']
    list_filter = ['last_activity_date', 'updated_at']
    search_fields = ['user__username']
    ordering = ['-current_streak']
    readonly_fields = ['updated_at']


@admin.register(QRCodeSession)
class QRCodeSessionAdmin(admin.ModelAdmin):
    """Admin interface for QRCodeSession"""
    list_display = ['user', 'session_token', 'expires_at', 'used_at', 'created_at']
    list_filter = ['used_at', 'created_at', 'expires_at']
    search_fields = ['user__username', 'session_token']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'session_token']
