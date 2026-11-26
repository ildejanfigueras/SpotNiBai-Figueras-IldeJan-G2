from decimal import Decimal

from django import forms
from django.db import transaction

from .models import Spot, SpotPhoto


# Approximate bounding box that covers the province of Cebu
CEBU_LAT_MIN, CEBU_LAT_MAX = Decimal("9.30"), Decimal("11.50")
CEBU_LNG_MIN, CEBU_LNG_MAX = Decimal("123.10"), Decimal("124.40")
MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG"}


class SpotForm(forms.ModelForm):
    photo = forms.ImageField(
        required=False,
        label="Cover photo",
        help_text="Optional. JPG or PNG, up to 5 MB.",
    )

    class Meta:
        model = Spot
        fields = ("name", "category", "description", "address", "latitude", "longitude")
        labels = {
            "name": "Spot name",
            "address": "Address or landmark",
        }
        help_texts = {
            "latitude": "Must be within Cebu (between 9.30 and 11.50).",
            "longitude": "Must be within Cebu (between 123.10 and 124.40).",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "latitude": forms.NumberInput(attrs={"placeholder": "10.315700"}),
            "longitude": forms.NumberInput(attrs={"placeholder": "123.885400"}),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner
        self.fields["category"].empty_label = "Select a category"

    def clean_name(self):
        name = self.cleaned_data["name"]
        if len(name) < 3:
            raise forms.ValidationError("The spot name must be at least 3 characters long.")
        return name

    def clean_description(self):
        description = self.cleaned_data["description"]
        if len(description) < 20:
            raise forms.ValidationError("Please describe the spot in at least 20 characters.")
        return description

    def clean_latitude(self):
        latitude = self.cleaned_data["latitude"]
        if not (CEBU_LAT_MIN <= latitude <= CEBU_LAT_MAX):
            raise forms.ValidationError("Latitude must be within Cebu (between 9.30 and 11.50).")
        return latitude

    def clean_longitude(self):
        longitude = self.cleaned_data["longitude"]
        if not (CEBU_LNG_MIN <= longitude <= CEBU_LNG_MAX):
            raise forms.ValidationError("Longitude must be within Cebu (between 123.10 and 124.40).")
        return longitude

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if photo:
            if photo.size > MAX_PHOTO_SIZE:
                raise forms.ValidationError("The photo must be 5 MB or smaller.")
            # forms.ImageField has already opened the file with Pillow, so the
            # real format is known (not just the file extension)
            if photo.image.format not in ALLOWED_IMAGE_FORMATS:
                raise forms.ValidationError("Upload a JPG or PNG image.")
        return photo

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        address = cleaned_data.get("address")
        if name and address and self.owner is not None:
            duplicates = Spot.objects.filter(
                owner=self.owner, name__iexact=name, address__iexact=address
            )
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise forms.ValidationError(
                    "You have already submitted a spot with this name and address."
                )
        return cleaned_data

    def save(self, commit=True):
        spot = super().save(commit=False)
        if spot.owner_id is None and self.owner is not None:
            spot.owner = self.owner
        if commit:
            # The spot and its cover photo are saved together or not at all
            with transaction.atomic():
                spot.save()
                photo = self.cleaned_data.get("photo")
                if photo:
                    spot.photos.filter(is_cover=True).delete()   # replace the old cover photo
                    SpotPhoto.objects.create(spot=spot, image=photo, is_cover=True)
        return spot