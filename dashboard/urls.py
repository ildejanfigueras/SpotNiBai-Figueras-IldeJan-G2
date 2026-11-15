from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("admin-dashboard/", views.AdminDashboardView.as_view(), name="admin_dashboard"),
    path("member-dashboard/", views.MemberDashboardView.as_view(), name="member_dashboard"),
]