from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
from .models import GymClass, Booking
from .forms import BookingForm


@login_required
def book_class(request):
    """Book a class"""
    classes = GymClass.objects.filter(is_active=True).order_by('schedule_time', 'schedule_days')
    
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        booking_date = request.POST.get('booking_date')
        
        try:
            with transaction.atomic():
                # Lock the GymClass row until this transaction is done
                gym_class = GymClass.objects.select_for_update().get(id=class_id, is_active=True)

                # Re-check capacity *inside* the transaction
                existing_bookings = Booking.objects.filter(
                    gym_class=gym_class,
                    booking_date=booking_date,
                    status='confirmed'
                ).count()

                if existing_bookings >= gym_class.max_capacity:
                    messages.error(request, 'This class is fully booked for the selected date.')
                    return redirect('bookings:book_class')

                # Check if user already booked this class on this date
                existing_booking = Booking.objects.filter(
                    user=request.user,
                    gym_class=gym_class,
                    booking_date=booking_date,
                    status='confirmed'
                ).exists()

                if existing_booking:
                    messages.error(request, 'You have already booked this class for the selected date.')
                    return redirect('bookings:book_class')

                # Create booking
                booking = Booking.objects.create(
                    user=request.user,
                    gym_class=gym_class,
                    booking_date=booking_date,
                    status='confirmed'
                )

            messages.success(request, f'Successfully booked {gym_class.name}!')
            return redirect('bookings:my_bookings')
            
        except GymClass.DoesNotExist:
            messages.error(request, 'Class not found.')
            return redirect('bookings:book_class')
    
    context = {
        'classes': classes,
    }
    return render(request, 'bookings/book_class.html', context)


@login_required
def my_bookings(request):
    """View user's bookings"""
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date', '-created_at')
    
    # Separate upcoming and past bookings
    today = timezone.now().date()
    upcoming = bookings.filter(booking_date__gte=today, status='confirmed')
    past = bookings.filter(booking_date__lt=today) | bookings.filter(status__in=['cancelled', 'completed'])
    
    context = {
        'upcoming': upcoming,
        'past': past,
    }
    return render(request, 'bookings/my_bookings.html', context)


@login_required
def cancel_booking(request, booking_id):
    """Cancel a booking"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status == 'cancelled':
        messages.error(request, 'This booking is already cancelled.')
        return redirect('bookings:my_bookings')
    
    if booking.booking_date < timezone.now().date():
        messages.error(request, 'Cannot cancel past bookings.')
        return redirect('bookings:my_bookings')
    
    booking.status = 'cancelled'
    booking.save()
    
    messages.success(request, f'Booking for {booking.gym_class.name} has been cancelled.')
    return redirect('bookings:my_bookings')
