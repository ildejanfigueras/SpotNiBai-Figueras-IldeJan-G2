from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView

from accounts.models import CustomUser


@login_required
def home(request):
    """Send each user to the dashboard for their role."""
    if request.user.role == CustomUser.Role.ADMIN:
        return redirect("dashboard:admin_dashboard")
    return redirect("dashboard:user_dashboard")


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    required_role = None

    def test_func(self):
        return self.request.user.role == self.required_role


class AdminDashboardView(RoleRequiredMixin, TemplateView):
    required_role = CustomUser.Role.ADMIN
    template_name = "dashboard/admin_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_users"] = CustomUser.objects.count()
        context["recent_users"] = CustomUser.objects.order_by("-date_joined")[:5]
        return context


class UserDashboardView(RoleRequiredMixin, TemplateView):
    required_role = CustomUser.Role.USER
    template_name = "dashboard/user_dashboard.html"