from django.urls import path
from . import views

app_name = 'trainer'

urlpatterns = [
    # Trainer Portal
    path('schedule/', views.trainer_schedule, name='schedule'),
    path('classes/<int:class_id>/roster/', views.trainer_class_roster, name='class_roster'),
    path('bookings/<int:booking_id>/attendance/', views.mark_attendance, name='mark_attendance'),
]

