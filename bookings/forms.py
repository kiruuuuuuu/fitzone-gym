from django import forms
from .models import Booking


class BookingForm(forms.ModelForm):
    """Form for booking a class"""
    
    class Meta:
        model = Booking
        fields = ['gym_class', 'booking_date']
        widgets = {
            'booking_date': forms.DateInput(attrs={'type': 'date'}),
        }

