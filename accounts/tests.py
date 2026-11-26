from django.test import TestCase
from django.urls import reverse

from .models import CustomUser

PASSWORD = "Coconut-Tree-8821"

SIGNUP_DATA = {
    "username": "ana",
    "email": "ana@example.com",
    "first_name": "Ana",
    "last_name": "Reyes",
    "contact_number": "09171234567",
    "password1": PASSWORD,
    "password2": PASSWORD,
}


class RegistrationTests(TestCase):
    def test_valid_signup_creates_a_regular_user(self):
        response = self.client.post(reverse("accounts:signup"), SIGNUP_DATA)
        self.assertRedirects(response, reverse("accounts:login"))
        user = CustomUser.objects.get(username="ana")
        self.assertEqual(user.role, CustomUser.Role.USER)

    def test_signup_cannot_grant_admin_rights(self):
        data = dict(SIGNUP_DATA, role="ADMIN", is_staff="on", is_superuser="on")
        self.client.post(reverse("accounts:signup"), data)
        user = CustomUser.objects.get(username="ana")
        self.assertEqual(user.role, CustomUser.Role.USER)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_signup_rejects_duplicate_email_in_any_case(self):
        CustomUser.objects.create_user(
            username="first", email="ana@example.com", password=PASSWORD
        )
        data = dict(SIGNUP_DATA, username="second", email="ANA@Example.com")
        response = self.client.post(reverse("accounts:signup"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"], "email", "An account with this email already exists."
        )
        self.assertFalse(CustomUser.objects.filter(username="second").exists())

    def test_signup_rejects_invalid_contact_number(self):
        data = dict(SIGNUP_DATA, contact_number="abc!!!")
        response = self.client.post(reverse("accounts:signup"), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["contact_number"])
        self.assertFalse(CustomUser.objects.filter(username="ana").exists())

    def test_signup_rejects_mismatched_passwords(self):
        data = dict(SIGNUP_DATA, password2="Different-Pass-1234")
        response = self.client.post(reverse("accounts:signup"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username="ana").exists())


class LoginLogoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username="ana", email="ana@example.com", password=PASSWORD
        )
        cls.admin = CustomUser.objects.create_user(
            username="boss", email="boss@example.com", password=PASSWORD,
            role=CustomUser.Role.ADMIN,
        )

    def test_login_with_correct_password_works(self):
        response = self.client.post(
            reverse("accounts:login"), {"username": "ana", "password": PASSWORD}
        )
        self.assertRedirects(
            response, reverse("dashboard:home"), fetch_redirect_response=False
        )
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_with_wrong_password_fails_with_an_error(self):
        response = self.client.post(
            reverse("accounts:login"), {"username": "ana", "password": "wrong-password"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_works_with_post(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(
            response, reverse("accounts:login"), fetch_redirect_response=False
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_rejects_get_requests(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 405)

    def test_dashboard_sends_each_role_to_its_own_dashboard(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard:home"))
        self.assertRedirects(
            response, reverse("dashboard:user_dashboard"), fetch_redirect_response=False
        )
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard:home"))
        self.assertRedirects(
            response, reverse("dashboard:admin_dashboard"), fetch_redirect_response=False
        )

    def test_dashboards_are_limited_to_their_own_role(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard:admin_dashboard"))
        self.assertEqual(response.status_code, 403)
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard:user_dashboard"))
        self.assertEqual(response.status_code, 403)


class ProfileTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username="ana", email="ana@example.com", password=PASSWORD,
            first_name="Ana", last_name="Reyes",
        )
        cls.other = CustomUser.objects.create_user(
            username="ben", email="ben@example.com", password=PASSWORD
        )

    def profile_data(self, **overrides):
        data = {
            "first_name": "Ana",
            "last_name": "Cruz",
            "email": "ana@example.com",
            "contact_number": "09179998888",
        }
        data.update(overrides)
        return data

    def test_profile_pages_require_login(self):
        login_url = reverse("accounts:login")
        for name in ("profile", "profile_edit"):
            url = reverse(f"accounts:{name}")
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(
                    response, f"{login_url}?next={url}", fetch_redirect_response=False
                )

    def test_user_can_update_their_own_profile(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:profile_edit"), self.profile_data())
        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_name, "Cruz")
        self.assertEqual(self.user.contact_number, "09179998888")

    def test_profile_rejects_email_used_by_another_account(self):
        self.client.force_login(self.user)
        data = self.profile_data(email="BEN@example.com")
        response = self.client.post(reverse("accounts:profile_edit"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"], "email", "This email is already used by another account."
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "ana@example.com")

    def test_profile_edit_only_changes_the_logged_in_user(self):
        self.client.force_login(self.user)
        self.client.post(reverse("accounts:profile_edit"), self.profile_data())
        self.other.refresh_from_db()
        self.assertEqual(self.other.email, "ben@example.com")
        self.assertEqual(self.other.last_name, "")
