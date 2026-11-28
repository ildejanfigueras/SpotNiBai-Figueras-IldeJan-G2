import io
from decimal import Decimal

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import CustomUser

from .models import Category, Spot, SpotPhoto

PASSWORD = "Coconut-Tree-8821"

# Photos go to memory during tests, never to the real Supabase bucket
TEST_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


def make_image(name="photo.png", image_format="PNG"):
    """Build a tiny real image so the form's Pillow check passes (or fails on purpose)."""
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), "teal").save(buffer, image_format)
    content_type = f"image/{image_format.lower()}"
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


@override_settings(STORAGES=TEST_STORAGES)
class SpotTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Food")
        cls.owner = CustomUser.objects.create_user(
            username="owner", email="owner@example.com", password=PASSWORD
        )
        cls.other = CustomUser.objects.create_user(
            username="other", email="other@example.com", password=PASSWORD
        )
        cls.admin = CustomUser.objects.create_user(
            username="admin1", email="admin1@example.com", password=PASSWORD,
            role=CustomUser.Role.ADMIN,
        )

    def make_spot(self, owner=None, status=Spot.Status.PENDING, **kwargs):
        values = {
            "owner": owner or self.owner,
            "category": self.category,
            "name": "Carbon Market",
            "description": "A busy public market with local food and goods.",
            "latitude": Decimal("10.295000"),
            "longitude": Decimal("123.899000"),
            "address": "M. C. Briones St, Cebu City",
            "status": status,
        }
        values.update(kwargs)
        return Spot.objects.create(**values)

    def valid_data(self, **overrides):
        data = {
            "name": "Magellan Cross",
            "category": self.category.pk,
            "description": "Historic cross housed in a small chapel in the city centre.",
            "address": "Magallanes St, Cebu City",
            "latitude": "10.293700",
            "longitude": "123.902100",
        }
        data.update(overrides)
        return data


class SpotSubmissionTests(SpotTestBase):
    """Valid and invalid input on the spot form."""

    def test_valid_submission_creates_pending_spot(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("spots:create"), self.valid_data())
        self.assertRedirects(response, reverse("spots:my_spots"))
        spot = Spot.objects.get(name="Magellan Cross")
        self.assertEqual(spot.owner, self.owner)
        self.assertEqual(spot.status, Spot.Status.PENDING)

    def test_valid_submission_with_cover_photo_saves_photo(self):
        self.client.force_login(self.owner)
        data = self.valid_data(photo=make_image())
        self.client.post(reverse("spots:create"), data)
        spot = Spot.objects.get(name="Magellan Cross")
        self.assertTrue(SpotPhoto.objects.filter(spot=spot, is_cover=True).exists())

    def test_name_that_is_too_short_is_rejected(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("spots:create"), self.valid_data(name="ab"))
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"], "name",
            "The spot name must be at least 3 characters long.",
        )
        self.assertFalse(Spot.objects.exists())

    def test_coordinates_outside_cebu_are_rejected(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("spots:create"), self.valid_data(latitude="14.599500")
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"], "latitude",
            "Latitude must be within Cebu (between 9.30 and 11.50).",
        )
        self.assertFalse(Spot.objects.exists())

    def test_gif_photo_is_rejected(self):
        self.client.force_login(self.owner)
        data = self.valid_data(photo=make_image("photo.gif", "GIF"))
        response = self.client.post(reverse("spots:create"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "photo", "Upload a JPG or PNG image.")
        self.assertFalse(Spot.objects.exists())

    def test_same_owner_cannot_submit_duplicate_spot(self):
        self.make_spot(name="Carbon Market", address="M. C. Briones St, Cebu City")
        self.client.force_login(self.owner)
        data = self.valid_data(name="CARBON MARKET", address="m. c. briones st, cebu city")
        response = self.client.post(reverse("spots:create"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"], None,
            "You have already submitted a spot with this name and address.",
        )
        self.assertEqual(Spot.objects.count(), 1)

    def test_editing_an_approved_spot_sends_it_back_to_pending(self):
        spot = self.make_spot(status=Spot.Status.APPROVED)
        self.client.force_login(self.owner)
        data = self.valid_data(name="Carbon Market Updated", address=spot.address)
        self.client.post(reverse("spots:edit", args=[spot.pk]), data)
        spot.refresh_from_db()
        self.assertEqual(spot.name, "Carbon Market Updated")
        self.assertEqual(spot.status, Spot.Status.PENDING)


class SpotAccessControlTests(SpotTestBase):
    """Login required, role checks and blocked access to other users' records."""

    def test_anonymous_users_are_redirected_to_login(self):
        spot = self.make_spot()
        urls = [
            reverse("spots:list"),
            reverse("spots:create"),
            reverse("spots:my_spots"),
            reverse("spots:review_queue"),
            reverse("spots:detail", args=[spot.pk]),
            reverse("spots:edit", args=[spot.pk]),
            reverse("spots:delete", args=[spot.pk]),
        ]
        login_url = reverse("accounts:login")
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(
                    response, f"{login_url}?next={url}", fetch_redirect_response=False
                )

    def test_admin_cannot_submit_spots(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("spots:create"))
        self.assertEqual(response.status_code, 403)

    def test_regular_user_cannot_open_review_queue(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("spots:review_queue"))
        self.assertEqual(response.status_code, 403)

    def test_regular_user_cannot_approve_a_spot(self):
        spot = self.make_spot()
        self.client.force_login(self.owner)
        response = self.client.post(reverse("spots:approve", args=[spot.pk]))
        self.assertEqual(response.status_code, 403)
        spot.refresh_from_db()
        self.assertEqual(spot.status, Spot.Status.PENDING)

    def test_user_cannot_edit_another_users_spot(self):
        spot = self.make_spot(owner=self.owner)
        self.client.force_login(self.other)
        url = reverse("spots:edit", args=[spot.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        response = self.client.post(url, self.valid_data(name="Hijacked"))
        self.assertEqual(response.status_code, 404)
        spot.refresh_from_db()
        self.assertEqual(spot.name, "Carbon Market")

    def test_user_cannot_delete_another_users_spot(self):
        spot = self.make_spot(owner=self.owner)
        self.client.force_login(self.other)
        response = self.client.post(reverse("spots:delete", args=[spot.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Spot.objects.filter(pk=spot.pk).exists())

    def test_pending_spot_is_hidden_from_other_users_but_not_owner_or_admin(self):
        spot = self.make_spot(owner=self.owner, status=Spot.Status.PENDING)
        url = reverse("spots:detail", args=[spot.pk])
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_unknown_spot_id_returns_404_not_a_crash(self):
        self.client.force_login(self.owner)
        for name in ("detail", "edit", "delete"):
            with self.subTest(view=name):
                response = self.client.get(reverse(f"spots:{name}", args=[99999]))
                self.assertEqual(response.status_code, 404)

    def test_spot_list_shows_only_approved_spots(self):
        approved = self.make_spot(
            name="Approved Place", address="Address one", status=Spot.Status.APPROVED
        )
        self.make_spot(name="Pending Place", address="Address two", status=Spot.Status.PENDING)
        self.client.force_login(self.other)
        response = self.client.get(reverse("spots:list"))
        self.assertEqual(list(response.context["spots"]), [approved])


class SpotReviewAndDeleteTests(SpotTestBase):
    """Business rules for admin review and for deleting spots."""

    def test_admin_can_approve_and_reject_pending_spots(self):
        to_approve = self.make_spot(name="First", address="Address one")
        to_reject = self.make_spot(name="Second", address="Address two")
        self.client.force_login(self.admin)
        self.client.post(reverse("spots:approve", args=[to_approve.pk]))
        self.client.post(reverse("spots:reject", args=[to_reject.pk]))
        to_approve.refresh_from_db()
        to_reject.refresh_from_db()
        self.assertEqual(to_approve.status, Spot.Status.APPROVED)
        self.assertEqual(to_reject.status, Spot.Status.REJECTED)

    def test_review_only_works_on_pending_spots(self):
        spot = self.make_spot(status=Spot.Status.APPROVED)
        self.client.force_login(self.admin)
        response = self.client.post(reverse("spots:reject", args=[spot.pk]), follow=True)
        spot.refresh_from_db()
        self.assertEqual(spot.status, Spot.Status.APPROVED)
        self.assertContains(response, "already reviewed")

    def test_review_actions_do_not_accept_get_requests(self):
        spot = self.make_spot()
        self.client.force_login(self.admin)
        response = self.client.get(reverse("spots:approve", args=[spot.pk]))
        self.assertEqual(response.status_code, 405)
        spot.refresh_from_db()
        self.assertEqual(spot.status, Spot.Status.PENDING)

    def test_delete_asks_for_confirmation_before_deleting(self):
        spot = self.make_spot()
        self.client.force_login(self.owner)
        url = reverse("spots:delete", args=[spot.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "spots/spot_confirm_delete.html")
        self.assertTrue(Spot.objects.filter(pk=spot.pk).exists())
        response = self.client.post(url)
        self.assertRedirects(response, reverse("spots:my_spots"))
        self.assertFalse(Spot.objects.filter(pk=spot.pk).exists())


class SpotDataIntegrityTests(SpotTestBase):
    """Database-level rules, foreign keys and photo cleanup (ISS-02)."""

    def test_database_blocks_duplicate_spots_for_same_owner(self):
        self.make_spot(name="Carbon Market", address="Some Street")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.make_spot(name="CARBON MARKET", address="SOME STREET")

    def test_database_blocks_rating_above_five(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.make_spot(avg_rating=Decimal("7.5"))

    def test_database_allows_only_one_cover_photo_per_spot(self):
        spot = self.make_spot()
        SpotPhoto.objects.create(spot=spot, image=make_image("one.png"), is_cover=True)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SpotPhoto.objects.create(spot=spot, image=make_image("two.png"), is_cover=True)

    def test_category_in_use_cannot_be_deleted(self):
        self.make_spot()
        with self.assertRaises(ProtectedError):
            self.category.delete()

    def test_deleting_a_spot_removes_its_photo_file(self):
        spot = self.make_spot()
        photo = SpotPhoto.objects.create(spot=spot, image=make_image(), is_cover=True)
        file_name = photo.image.name
        self.assertTrue(default_storage.exists(file_name))
        with self.captureOnCommitCallbacks(execute=True):
            spot.delete()
        self.assertFalse(default_storage.exists(file_name))
