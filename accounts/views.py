from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import RegistrationForm


class SignUpView(SuccessMessageMixin, CreateView):
    form_class = RegistrationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("accounts:login")
    success_message = "Account created successfully. You can now log in."

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors below and try again.")
        return super().form_invalid(form)