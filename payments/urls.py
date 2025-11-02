from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/<int:plan_id>/', views.create_checkout_session, name='checkout'),
    path('success/', views.checkout_success, name='success'),
    path('webhook/', views.webhook, name='webhook'),
    path('my-subscription/', views.my_subscription, name='my_subscription'),
]

