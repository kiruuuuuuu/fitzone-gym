import qrcode
import io
import base64
from datetime import datetime, timedelta
from django.utils import timezone
from .models import QRCodeSession, UserPoints, UserStreak

# Import challenge models
try:
    from community.models import UserChallenge
except ImportError:
    # Handle case where community app might not be available
    UserChallenge = None


def generate_qr_code(user):
    """Generate QR code for gym entry"""
    # Create or get existing active session
    expires_at = timezone.now() + timedelta(seconds=30)  # 30 second expiry
    
    # Generate session token
    session_token = f"{user.id}_{int(timezone.now().timestamp())}"
    
    # Create QR session
    qr_session, created = QRCodeSession.objects.update_or_create(
        user=user,
        expires_at__gt=timezone.now(),
        defaults={
            'session_token': session_token,
            'expires_at': expires_at,
        }
    )
    
    if not created:
        qr_session.session_token = session_token
        qr_session.expires_at = expires_at
        qr_session.save()
    
    # Generate QR code data
    qr_data_string = f"GYM_PRANAMYA:{user.id}:{session_token}:{int(expires_at.timestamp())}"
    
    # Create QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data_string)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return {
        'qr_image': f"data:image/png;base64,{img_str}",
        'session_token': session_token,
        'expires_at': expires_at,
    }


def award_points_and_update_streak(user, points, source='workout', description=''):
    """Award points to a user and update their streak"""
    # Award points
    UserPoints.objects.create(
        user=user,
        points=points,
        source=source,
        description=description
    )
    
    # Update streak
    update_user_streak(user)
    
    # Update active challenge progress
    if UserChallenge is not None:
        update_challenge_progress(user, points, source)


def update_user_streak(user):
    """Update user's streak based on last activity"""
    today = timezone.now().date()
    
    # Get or create streak object
    streak, created = UserStreak.objects.get_or_create(
        user=user,
        defaults={
            'current_streak': 1,
            'longest_streak': 1,
            'last_activity_date': today
        }
    )
    
    if created:
        return
    
    # Check if activity was today
    if streak.last_activity_date == today:
        # Already updated today, don't change
        return
    
    # Check if activity was yesterday (consecutive day)
    yesterday = today - timedelta(days=1)
    if streak.last_activity_date == yesterday:
        # Increment streak
        streak.current_streak += 1
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
    else:
        # Streak broken, reset to 1
        streak.current_streak = 1
    
    # Update last activity date
    streak.last_activity_date = today
    streak.save()


def update_challenge_progress(user, points, source):
    """Update user's progress in active challenges"""
    today = timezone.now().date()
    
    # Find all active challenges this user has joined
    active_user_challenges = UserChallenge.objects.filter(
        user=user,
        challenge__start_date__lte=today,
        challenge__end_date__gte=today
    )
    
    for user_challenge in active_user_challenges:
        challenge_type = user_challenge.challenge.goal_type
        
        # Check if the source of the points matches the challenge type
        if (challenge_type == 'visits' and source == 'checkin') or \
           (challenge_type == 'workouts' and source == 'workout') or \
           (challenge_type == 'points'):  # 'points' type increments by points earned
            
            if challenge_type == 'points':
                # Add the points value for points challenges
                user_challenge.progress += points
            else:
                # Add 1 for visits or workouts
                user_challenge.progress += 1
            
            user_challenge.save()
        
        # Note: 'streak' type challenges would need separate handling
        # by syncing user.streak.current_streak to user_challenge.progress

