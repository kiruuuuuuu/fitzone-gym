from django.db import models
from django.conf import settings


class Post(models.Model):
    """Community feed posts"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    image = models.ImageField(upload_to='community_posts/', blank=True, null=True)
    likes_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.content[:50]}..."


class Comment(models.Model):
    """Comments on community posts"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.user.username} on {self.post.id} - {self.content[:30]}..."


class Like(models.Model):
    """Likes on community posts"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['post', 'user']]
    
    def __str__(self):
        return f"{self.user.username} likes post {self.post.id}"


class Challenge(models.Model):
    """Community challenges"""
    GOAL_TYPES = [
        ('visits', 'Most Visits'),
        ('workouts', 'Most Workouts Completed'),
        ('points', 'Most Points Earned'),
        ('streak', 'Longest Streak'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    goal_value = models.IntegerField(blank=True, null=True, help_text="Optional: specific goal value")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return self.name
    
    @property
    def is_active(self):
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date


class UserChallenge(models.Model):
    """User participation in challenges"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='challenges')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='participants')
    progress = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['user', 'challenge']]
        ordering = ['-progress']
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.name} ({self.progress})"
