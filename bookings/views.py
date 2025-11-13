from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
from .models import GymClass, Booking, ClassSchedule
from .forms import BookingForm


@login_required
def book_class(request):
    """Book a class"""
    # Get all active classes with their upcoming schedules
    today = timezone.now().date()
    classes = GymClass.objects.filter(is_active=True).prefetch_related('schedules').order_by('name')
    
    # Filter schedules to only show upcoming ones
    for gym_class in classes:
        gym_class.upcoming_schedules = gym_class.schedules.filter(
            class_date__gte=today,
            is_active=True
        ).order_by('class_date', 'class_time')
    
    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        
        try:
            with transaction.atomic():
                # Lock the ClassSchedule row until this transaction is done
                class_schedule = ClassSchedule.objects.select_for_update().get(
                    id=schedule_id,
                    is_active=True,
                    class_date__gte=today
                )
                
                gym_class = class_schedule.gym_class
                
                # Check if class is active
                if not gym_class.is_active:
                    messages.error(request, 'This class is not available for booking.')
                    return redirect('bookings:book_class')

                # Re-check capacity *inside* the transaction
                available_spots = class_schedule.available_spots()
                
                if available_spots <= 0:
                    messages.error(request, 'This class session is fully booked.')
                    return redirect('bookings:book_class')

                # Check if user already booked this schedule
                existing_booking = Booking.objects.filter(
                    user=request.user,
                    class_schedule=class_schedule,
                    status='confirmed'
                ).exists()

                if existing_booking:
                    messages.error(request, 'You have already booked this class session.')
                    return redirect('bookings:book_class')

                # Create booking
                booking = Booking.objects.create(
                    user=request.user,
                    gym_class=gym_class,
                    class_schedule=class_schedule,
                    booking_date=class_schedule.class_date,
                    status='confirmed'
                )

            messages.success(request, f'Successfully booked {gym_class.name} for {class_schedule.class_date}!')
            return redirect('bookings:my_bookings')
            
        except ClassSchedule.DoesNotExist:
            messages.error(request, 'Class schedule not found or no longer available.')
            return redirect('bookings:book_class')
        except Exception as e:
            messages.error(request, f'Error booking class: {str(e)}')
            return redirect('bookings:book_class')
    
    context = {
        'classes': classes,
    }
    return render(request, 'bookings/book_class.html', context)


@login_required
def my_bookings(request):
    """View user's bookings"""
    bookings = Booking.objects.filter(user=request.user).select_related('gym_class', 'class_schedule').order_by('-booking_date', '-created_at')
    
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
