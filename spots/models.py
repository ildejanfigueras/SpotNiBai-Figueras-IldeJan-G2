from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Spot(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="spots"
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="spots"
    )
    name = models.CharField(max_length=150)
    description = models.TextField()
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    address = models.CharField(max_length=255)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    avg_rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def cover_photo(self):
        photos = list(self.photos.all())
        for photo in photos:
            if photo.is_cover:
                return photo
        return photos[0] if photos else None


class SpotPhoto(models.Model):
    spot = models.ForeignKey(Spot, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="spot_photos/", max_length=255)
    is_cover = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo of {self.spot.name}"


@receiver(post_delete, sender=SpotPhoto)
def delete_photo_file(sender, instance, **kwargs):
    """Remove the image file once its database row is gone (fixes ISS-02)."""
    if instance.image:
        storage, name = instance.image.storage, instance.image.name
        transaction.on_commit(lambda: storage.delete(name))