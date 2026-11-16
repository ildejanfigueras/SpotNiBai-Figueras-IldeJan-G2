from django.db import migrations

DEFAULT_CATEGORIES = [
    ("Food & Restaurants", "Local eats, restaurants and street food"),
    ("Cafes & Coffee", "Coffee shops, bakeries and dessert places"),
    ("Parks & Nature", "Parks, gardens, viewpoints and outdoor places"),
    ("Beaches & Resorts", "Beaches, resorts and island getaways"),
    ("Historical & Heritage", "Churches, museums and heritage sites"),
    ("Shopping & Markets", "Malls, markets and local shops"),
    ("Nightlife & Entertainment", "Bars, clubs, music and activities"),
    ("Hidden Gems", "Lesser-known places worth discovering"),
]


def add_categories(apps, schema_editor):
    Category = apps.get_model("spots", "Category")
    for name, description in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(name=name, defaults={"description": description})


def remove_categories(apps, schema_editor):
    Category = apps.get_model("spots", "Category")
    Category.objects.filter(name__in=[name for name, _ in DEFAULT_CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("spots", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_categories, remove_categories),
    ]