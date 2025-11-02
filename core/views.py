from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from .models import MembershipPlan, Subscription, CustomUser, UserPoints
from .forms import RegistrationForm, ContactForm
from bookings.models import Booking, GymClass
from workouts.models import UserWorkoutPlan
from datetime import datetime, timedelta


def home(request):
    """Homepage view"""
    context = {
        'active_members': CustomUser.objects.filter(is_active=True).count(),
        'total_classes': GymClass.objects.filter(is_active=True).count(),
    }
    return render(request, 'home.html', context)


def about(request):
    """About Us page"""
    return render(request, 'about.html')


def contact(request):
    """Contact page with form"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # In a real app, you would send an email here
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})


def pricing(request):
    """Membership plans page"""
    plans = MembershipPlan.objects.filter(is_active=True).order_by('price')
    return render(request, 'pricing.html', {'plans': plans})


def schedule(request):
    """Class schedule page"""
    classes = GymClass.objects.filter(is_active=True).order_by('schedule_time', 'schedule_days')
    return render(request, 'schedule.html', {'classes': classes})


def register(request):
    """User registration"""
    # Prevent logged-in users from accessing registration
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in. Please log out to create a new account.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to FitZone Gym!')
            return redirect('dashboard')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    """Member dashboard"""
    user = request.user
    
    # Get active subscription
    try:
        subscription = Subscription.objects.filter(user=user, status='active').latest('created_at')
    except Subscription.DoesNotExist:
        subscription = None
    
    # Get upcoming bookings
    today = datetime.now().date()
    upcoming_bookings = Booking.objects.filter(
        user=user,
        booking_date__gte=today,
        status='confirmed'
    ).order_by('booking_date')[:5]
    
    # Get user streak and points
    try:
        streak = user.streak
    except:
        streak = None
    
    total_points = UserPoints.objects.filter(user=user).aggregate(
        total=Sum('points')
    )['total'] or 0
    
    # Get assigned workout plans
    assigned_plans = UserWorkoutPlan.objects.filter(user=user).select_related('plan', 'plan__trainer')
    
    context = {
        'subscription': subscription,
        'upcoming_bookings': upcoming_bookings,
        'streak': streak,
        'total_points': total_points,
        'assigned_plans': assigned_plans,
    }
    return render(request, 'dashboard.html', context)


@login_required
def qr_code(request):
    """QR code generation for gym entry"""
    from .utils import generate_qr_code
    
    qr_data = generate_qr_code(request.user)
    
    context = {
        'qr_data': qr_data,
    }
    return render(request, 'core/qr_code.html', context)


def custom_logout(request):
    """Custom logout view that accepts GET requests"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')
