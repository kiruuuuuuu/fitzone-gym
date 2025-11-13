from django.db import models
from django.conf import settings


class GymClass(models.Model):
    """Gym classes available for booking"""
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    LOCATION_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    trainer = models.ForeignKey('core.Trainer', on_delete=models.SET_NULL, null=True, blank=True)
    duration = models.IntegerField(help_text="Duration in minutes")
    max_capacity = models.IntegerField(default=20)
    schedule_time = models.TimeField(blank=True, null=True, help_text="Legacy field - use ClassSchedule for specific dates/times")
    schedule_days = models.CharField(max_length=100, blank=True, null=True, help_text="Legacy field - use ClassSchedule for specific dates/times")
    is_paid = models.BooleanField(default=False, help_text="Whether this class requires payment")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Price in rupees (required if paid)")
    location_type = models.CharField(max_length=10, choices=LOCATION_CHOICES, default='offline', help_text="Where the class is held")
    location_details = models.TextField(blank=True, null=True, help_text="Specific location info (address, zoom link, etc.)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['schedule_time', 'name']
        verbose_name_plural = "Gym Classes"
    
    def __str__(self):
        return self.name
    
    def available_spots(self, date=None):
        """Calculate available spots for a specific date or next occurrence"""
        if date:
            booked_count = self.bookings.filter(
                status='confirmed',
                booking_date=date
            ).count()
        else:
            # For backward compatibility, count all confirmed bookings
            booked_count = self.bookings.filter(status='confirmed').count()
        return max(0, self.max_capacity - booked_count)


class ClassSchedule(models.Model):
    """Individual class sessions with specific date and time"""
    gym_class = models.ForeignKey(GymClass, on_delete=models.CASCADE, related_name='schedules')
    class_date = models.DateField()
    class_time = models.TimeField()
    max_capacity = models.IntegerField(null=True, blank=True, help_text="Override class default capacity if needed")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['class_date', 'class_time']
        unique_together = [['gym_class', 'class_date', 'class_time']]
        verbose_name_plural = "Class Schedules"
    
    def __str__(self):
        return f"{self.gym_class.name} - {self.class_date} at {self.class_time}"
    
    @property
    def effective_capacity(self):
        """Get the effective capacity (schedule override or class default)"""
        return self.max_capacity if self.max_capacity is not None else self.gym_class.max_capacity
    
    def available_spots(self):
        """Calculate available spots for this specific schedule"""
        booked_count = self.bookings.filter(status='confirmed').count()
        return max(0, self.effective_capacity - booked_count)


class Booking(models.Model):
    """User bookings for gym classes"""
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    gym_class = models.ForeignKey(GymClass, on_delete=models.CASCADE, related_name='bookings')
    class_schedule = models.ForeignKey('ClassSchedule', on_delete=models.CASCADE, related_name='bookings', null=True, blank=True, help_text="Specific class schedule (preferred)")
    booking_date = models.DateField(help_text="Legacy field - use class_schedule for specific date/time")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-booking_date', '-created_at']
        unique_together = [['user', 'gym_class', 'booking_date']]
    
    def __str__(self):
        return f"{self.user.username} - {self.gym_class.name} on {self.booking_date}"
