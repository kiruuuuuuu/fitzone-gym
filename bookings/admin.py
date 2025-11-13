from django.contrib import admin
from .models import GymClass, Booking, ClassSchedule


@admin.register(GymClass)
class GymClassAdmin(admin.ModelAdmin):
    """Admin interface for GymClass"""
    list_display = ['name', 'trainer', 'is_paid', 'location_type', 'duration', 'max_capacity', 'is_active']
    list_filter = ['is_active', 'is_paid', 'location_type', 'trainer', 'created_at']
    search_fields = ['name', 'description', 'trainer__user__username']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Class Information', {
            'fields': ('name', 'description', 'trainer', 'duration', 'max_capacity')
        }),
        ('Payment & Location', {
            'fields': ('is_paid', 'price', 'location_type', 'location_details')
        }),
        ('Legacy Schedule (Deprecated)', {
            'fields': ('schedule_time', 'schedule_days'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    """Admin interface for ClassSchedule"""
    list_display = ['gym_class', 'class_date', 'class_time', 'available_spots', 'is_active']
    list_filter = ['is_active', 'class_date', 'gym_class']
    search_fields = ['gym_class__name']
    ordering = ['class_date', 'class_time']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('gym_class', 'class_date', 'class_time', 'max_capacity', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def available_spots(self, obj):
        return obj.available_spots()
    available_spots.short_description = 'Available Spots'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin interface for Booking"""
    list_display = ['user', 'gym_class', 'class_schedule', 'booking_date', 'status', 'created_at']
    list_filter = ['status', 'booking_date', 'created_at']
    search_fields = ['user__username', 'user__email', 'gym_class__name']
    ordering = ['-booking_date', '-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('user', 'gym_class', 'class_schedule', 'booking_date', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
