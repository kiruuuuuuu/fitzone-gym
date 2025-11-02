from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

from core.models import CustomUser, Subscription


@method_decorator(login_required, name='dispatch')
class AdminDashboardView(TemplateView):
    """Custom admin dashboard"""
    template_name = 'admin/custom_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not request.user.is_staff:
            raise PermissionDenied("You do not have permission to access this page.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Key metrics
        context['total_users'] = CustomUser.objects.count()
        context['active_subscriptions'] = Subscription.objects.filter(status='active').count()
        
        # Calculate total revenue from active subscriptions
        total_revenue = Subscription.objects.filter(status='active').aggregate(
            total=Sum('plan__price')
        )['total'] or 0
        context['total_revenue'] = total_revenue
        
        return context

