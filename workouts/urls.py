from django.urls import path
from . import views

app_name = 'workouts'

urlpatterns = [
    path('', views.library, name='library'),
    path('<int:workout_id>/', views.workout_detail, name='workout_detail'),
    path('<int:workout_id>/complete/', views.mark_completed, name='mark_completed'),
]

