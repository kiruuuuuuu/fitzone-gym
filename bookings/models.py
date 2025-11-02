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
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    trainer = models.ForeignKey('core.Trainer', on_delete=models.SET_NULL, null=True, blank=True)
    duration = models.IntegerField(help_text="Duration in minutes")
    max_capacity = models.IntegerField(default=20)
    schedule_time = models.TimeField()
    schedule_days = models.CharField(max_length=100, help_text="Comma-separated days (e.g., monday,wednesday,friday)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['schedule_time', 'name']
        verbose_name_plural = "Gym Classes"
    
    def __str__(self):
        return self.name
    
    @property
    def available_spots(self):
        """Calculate available spots for next occurrence"""
        booked_count = self.bookings.filter(status='confirmed').count()
        return max(0, self.max_capacity - booked_count)


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
    booking_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-booking_date', '-created_at']
        unique_together = [['user', 'gym_class', 'booking_date']]
    
    def __str__(self):
        return f"{self.user.username} - {self.gym_class.name} on {self.booking_date}"
