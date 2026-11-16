from django.contrib import admin

from .models import Category, Spot, SpotPhoto


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


class SpotPhotoInline(admin.TabularInline):
    model = SpotPhoto
    extra = 0


@admin.register(Spot)
class SpotAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "owner", "status", "created_at"]
    list_filter = ["status", "category"]
    search_fields = ["name", "address", "owner__username"]
    inlines = [SpotPhotoInline]