from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView, View,
)
from django.shortcuts import get_object_or_404, redirect

from accounts.models import CustomUser
from dashboard.views import RoleRequiredMixin

from .forms import SpotForm
from .models import Category, Spot

class SpotListView(LoginRequiredMixin, ListView):
    """Browse approved spots, with search and a category filter."""
    model = Spot
    template_name = "spots/spot_list.html"
    context_object_name = "spots"
    paginate_by = 9

    def get_queryset(self):
        queryset = (
            Spot.objects.filter(status=Spot.Status.APPROVED)
            .select_related("category", "owner")
            .prefetch_related("photos")
        )
        q = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("category", "")
        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(address__icontains=q))
        if category.isdigit():
            queryset = queryset.filter(category_id=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        context["categories"] = Category.objects.all()
        context["q"] = self.request.GET.get("q", "").strip()
        context["selected_category"] = self.request.GET.get("category", "")
        context["querystring"] = params.urlencode()
        return context


class SpotDetailView(LoginRequiredMixin, DetailView):
    """Approved spots are visible to everyone; others only to the owner and admins."""
    model = Spot
    template_name = "spots/spot_detail.html"
    context_object_name = "spot"

    def get_queryset(self):
        return Spot.objects.select_related("category", "owner").prefetch_related("photos")

    def get_object(self, queryset=None):
        spot = super().get_object(queryset)
        user = self.request.user
        is_admin = user.role == CustomUser.Role.ADMIN
        if spot.status != Spot.Status.APPROVED and spot.owner_id != user.id and not is_admin:
            raise Http404("Spot not found")
        return spot


class SpotCreateView(RoleRequiredMixin, SuccessMessageMixin, CreateView):
    required_role = CustomUser.Role.USER
    model = Spot
    form_class = SpotForm
    template_name = "spots/spot_form.html"
    success_url = reverse_lazy("spots:my_spots")
    success_message = "Your spot was submitted and is waiting for admin approval."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["owner"] = self.request.user
        return kwargs

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors below and try again.")
        return super().form_invalid(form)


class MySpotListView(RoleRequiredMixin, ListView):
    """Every spot the logged-in user submitted, whatever its status."""
    required_role = CustomUser.Role.USER
    template_name = "spots/my_spots.html"
    context_object_name = "spots"
    paginate_by = 10

    def get_queryset(self):
        return (
            Spot.objects.filter(owner=self.request.user)
            .select_related("category")
            .prefetch_related("photos")
        )

class SpotUpdateView(RoleRequiredMixin, SuccessMessageMixin, UpdateView):
    """Owners edit their own spots. Anyone else's spot is a 404."""
    required_role = CustomUser.Role.USER
    form_class = SpotForm
    template_name = "spots/spot_form.html"
    success_message = "Your spot was updated and is waiting for admin approval again."

    def get_queryset(self):
        return Spot.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["owner"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.status = Spot.Status.PENDING   # edits need a new review
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors below and try again.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("spots:detail", kwargs={"pk": self.object.pk})


class SpotDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """Owners delete their own spots. Administrators can delete any spot."""
    template_name = "spots/spot_confirm_delete.html"
    context_object_name = "spot"
    success_message = "The spot was deleted."

    def get_queryset(self):
        if self.request.user.role == CustomUser.Role.ADMIN:
            return Spot.objects.all()
        return Spot.objects.filter(owner=self.request.user)

    def get_success_url(self):
        if self.request.user.role == CustomUser.Role.ADMIN:
            return reverse_lazy("spots:list")
        return reverse_lazy("spots:my_spots")

class ReviewQueueView(RoleRequiredMixin, ListView):
    """Administrators see every pending spot, oldest first."""
    required_role = CustomUser.Role.ADMIN
    template_name = "spots/review_queue.html"
    context_object_name = "spots"
    paginate_by = 10

    def get_queryset(self):
        return (
            Spot.objects.filter(status=Spot.Status.PENDING)
            .select_related("category", "owner")
            .prefetch_related("photos")
            .order_by("created_at")
        )

class SpotReviewActionView(RoleRequiredMixin, View):
    """Approve or reject a spot. POST only, administrators only."""
    required_role = CustomUser.Role.ADMIN
    http_method_names = ["post"]
    new_status = None
    success_text = ""

    def post(self, request, pk):
        spot = get_object_or_404(Spot, pk=pk)
        spot.status = self.new_status
        spot.save(update_fields=["status", "updated_at"])
        messages.success(request, f'"{spot.name}" {self.success_text}')
        return redirect("spots:review_queue")