from django.contrib import admin
from .models import GymClass, Booking


@admin.register(GymClass)
class GymClassAdmin(admin.ModelAdmin):
    """Admin interface for GymClass"""
    list_display = ['name', 'trainer', 'schedule_time', 'duration', 'max_capacity', 'available_spots', 'is_active']
    list_filter = ['is_active', 'schedule_time', 'trainer', 'created_at']
    search_fields = ['name', 'description', 'trainer__user__username']
    ordering = ['schedule_time', 'name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Class Information', {
            'fields': ('name', 'description', 'trainer', 'duration', 'max_capacity')
        }),
        ('Schedule', {
            'fields': ('schedule_time', 'schedule_days', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin interface for Booking"""
    list_display = ['user', 'gym_class', 'booking_date', 'status', 'created_at']
    list_filter = ['status', 'booking_date', 'created_at']
    search_fields = ['user__username', 'user__email', 'gym_class__name']
    ordering = ['-booking_date', '-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('user', 'gym_class', 'booking_date', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
