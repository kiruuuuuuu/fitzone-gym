from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # Staff Dashboard
    path('', views.StaffDashboard.as_view(), name='dashboard'),
    path('members/', views.MemberListView.as_view(), name='member_list'),
    path('members/<int:user_id>/', views.member_detail, name='member_detail'),
    
    # Membership Plans
    path('plans/', views.PlanListView.as_view(), name='plan_list'),
    path('plans/create/', views.plan_create, name='plan_create'),
    path('plans/<int:plan_id>/edit/', views.plan_edit, name='plan_edit'),
    
    # Classes
    path('classes/', views.ClassListView.as_view(), name='class_list'),
    path('classes/create/', views.class_create, name='class_create'),
    path('classes/<int:class_id>/edit/', views.class_edit, name='class_edit'),
    
    # Workouts
    path('workouts/', views.workout_list, name='workout_list'),
    path('workouts/create/', views.workout_create, name='workout_create'),
    path('workouts/<int:workout_id>/edit/', views.workout_edit, name='workout_edit'),
    
    # Check-in
    path('checkin/', views.checkin_view, name='checkin'),
]

