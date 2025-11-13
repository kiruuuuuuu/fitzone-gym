from django.urls import path
from . import views

app_name = 'trainer'

urlpatterns = [
    # Trainer Portal
    path('schedule/', views.trainer_schedule, name='schedule'),
    path('classes/<int:class_id>/roster/', views.trainer_class_roster, name='class_roster'),
    path('bookings/<int:booking_id>/attendance/', views.mark_attendance, name='mark_attendance'),
    
    # Trainer Workout Plans
    path('plans/', views.TrainerPlanListView.as_view(), name='plan_list'),
    path('plans/create/', views.trainer_plan_create, name='plan_create'),
    path('plans/<int:plan_id>/edit/', views.trainer_plan_edit, name='plan_edit'),
    path('plans/<int:plan_id>/assign/', views.trainer_plan_assign, name='plan_assign'),
    
    # Trainer Individual Workout Assignment
    path('assign-workout/', views.trainer_assign_workout, name='assign_workout'),
]

