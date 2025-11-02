from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError


class CustomUser(AbstractUser):
    """Custom user model extending Django's AbstractUser"""
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return self.username


class MembershipPlan(models.Model):
    """Membership subscription plans"""
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.TextField(help_text="List of features included in this plan")
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['price']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate that active plans have Stripe Price ID"""
        if self.is_active and not self.stripe_price_id:
            raise ValidationError({'stripe_price_id': 'An active plan must have a Stripe Price ID.'})
    
    def save(self, *args, **kwargs):
        """Call full_clean before saving to enforce validation"""
        self.full_clean()
        super().save(*args, **kwargs)


class Subscription(models.Model):
    """User subscription to a membership plan"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('past_due', 'Past Due'),
        ('unpaid', 'Unpaid'),
        ('trialing', 'Trialing'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(MembershipPlan, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    current_period_start = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name if self.plan else 'No Plan'}"
    
    @property
    def is_active(self):
        return self.status == 'active'


class Trainer(models.Model):
    """Gym trainers"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='trainer_profile')
    bio = models.TextField(blank=True)
    specializations = models.CharField(max_length=500, blank=True, help_text="Comma-separated list of specializations")
    profile_picture = models.ImageField(upload_to='trainer_pictures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.user.get_full_name() or self.user.username


class UserPoints(models.Model):
    """Gamification: Points earned by users"""
    POINT_SOURCES = [
        ('checkin', 'Gym Check-in'),
        ('class', 'Class Attendance'),
        ('workout', 'Workout Completion'),
        ('challenge', 'Challenge Completion'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='points')
    points = models.IntegerField(default=0)
    source = models.CharField(max_length=20, choices=POINT_SOURCES)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.points} points ({self.source})"


class UserStreak(models.Model):
    """Gamification: User's current streak"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.current_streak} day streak"


class QRCodeSession(models.Model):
    """QR code sessions for gym entry"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='qr_sessions')
    session_token = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.session_token[:10]}..."
