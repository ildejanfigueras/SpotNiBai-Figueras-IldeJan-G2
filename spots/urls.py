from django.urls import path
from . import views

app_name = "spots"

urlpatterns = [
    path("", views.SpotListView.as_view(), name="list"),
    path("new/", views.SpotCreateView.as_view(), name="create"),
    path("mine/", views.MySpotListView.as_view(), name="my_spots"),
    path("<int:pk>/", views.SpotDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.SpotUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.SpotDeleteView.as_view(), name="delete"),
]