from django.urls import path
from . import views
from .models import Spot

app_name = "spots"

urlpatterns = [
    path("", views.SpotListView.as_view(), name="list"),
    path("new/", views.SpotCreateView.as_view(), name="create"),
    path("mine/", views.MySpotListView.as_view(), name="my_spots"),
    path("review/", views.ReviewQueueView.as_view(), name="review_queue"),
    path("<int:pk>/", views.SpotDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.SpotUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.SpotDeleteView.as_view(), name="delete"),
    path(
        "<int:pk>/approve/",
        views.SpotReviewActionView.as_view(
            new_status=Spot.Status.APPROVED, success_text="was approved."
        ),
        name="approve",
    ),
    path(
        "<int:pk>/reject/",
        views.SpotReviewActionView.as_view(
            new_status=Spot.Status.REJECTED, success_text="was rejected."
        ),
        name="reject",
    ),
]