import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models.jwt_token_blacklist import TokenBlacklist


@pytest.mark.django_db
class TestUserViewSet:
    @pytest.fixture(autouse=True)
    def setup(self, api_client, user_factory, admin_user):
        self.client = api_client
        self.user = user_factory(password="oldpass123")
        self.other_user = user_factory()
        self.admin = admin_user
        self.url = "/api/v1/users/"

    def test_user_can_register(self):
        data = {
            "email": "newuser@example.com",
            "password": "userpassword123",
            "retype_password": "userpassword123",
            "first_name": "first name",
            "last_name": "last name",
        }
        response = self.client.post(self.url, data)
        assert response.status_code == 201
        assert response.data["email"] == "newuser@example.com"

    def test_register_passwords_do_not_match(self):
        data = {
            "email": "test@example.com",
            "password": "pass123",
            "retype_password": "different123",
            "first_name": "Test",
            "last_name": "User",
        }
        response = self.client.post(self.url, data)
        assert response.status_code == 400

    def test_user_can_update_own_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            f"{self.url}{self.user.id}/",
            {"first_name": "UpdatedName"},
        )
        assert response.status_code == 200
        assert response.data["first_name"] == "UpdatedName"

    def test_user_cannot_update_other_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            f"{self.url}{self.other_user.id}/",
            {"first_name": "Hack"},
        )
        assert response.status_code == 403

    def test_only_admin_can_list_users(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        assert response.status_code == 403

        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_user_can_retrieve_own_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(f"{self.url}{self.user.id}/")
        assert response.status_code == 200

    def test_user_cannot_retrieve_other_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(f"{self.url}{self.other_user.id}/")
        assert response.status_code == 403

    def test_change_password_success(self):
        self.client.force_authenticate(self.user)
        data = {
            "old_password": "oldpass123",
            "new_password": "NewPass123!!!",
            "retype_password": "NewPass123!!!",
        }
        response = self.client.post(f"{self.url}change_password/", data)
        assert response.status_code == 200

        self.user.refresh_from_db()
        assert self.user.check_password("NewPass123!!!")

    def test_wrong_old_password_in_password_change(self):
        self.client.force_authenticate(self.user)
        data = {
            "old_password": "wrongpass",
            "new_password": "newpass123",
            "retype_password": "newpass123",
        }
        response = self.client.post(f"{self.url}change_password/", data)
        assert response.status_code == 400
        assert response.data["old_password"][0] == "Wrong Password"

    def test_change_password_retype_mismatch(self):
        self.client.force_authenticate(self.user)
        data = {
            "old_password": "oldpass123",
            "new_password": "newpass123",
            "retype_password": "different123",
        }
        response = self.client.post(f"{self.url}change_password/", data)
        assert response.status_code == 400

    def test_change_password_same_as_old(self):
        self.client.force_authenticate(self.user)
        data = {
            "old_password": "oldpass123",
            "new_password": "oldpass123",
            "retype_password": "oldpass123",
        }
        response = self.client.post(f"{self.url}change_password/", data)
        assert response.status_code == 400


@pytest.mark.django_db
class TestLogoutEndpoint:
    """Test logout endpoint functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.logout_url = "/api/v1/users/logout/"

    def test_logout_success(self, user_factory):
        user = user_factory()
        refresh = RefreshToken.for_user(user)
        self.client.force_authenticate(user=user)
        response = self.client.post(
            self.logout_url, {"refresh": str(refresh)}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "detail" in response.data
        assert "logged out" in response.data["detail"].lower()

    def test_logout_blacklists_token(self, user_factory):
        user = user_factory()
        refresh = RefreshToken.for_user(user)
        jti = refresh.get("jti")
        self.client.force_authenticate(user=user)
        assert not TokenBlacklist.is_blacklisted(jti)
        self.client.post(self.logout_url, {"refresh": str(refresh)}, format="json")
        assert TokenBlacklist.is_blacklisted(jti)

    def test_logout_invalid_token(self, user_factory):
        user = user_factory()
        self.client.force_authenticate(user=user)
        response = self.client.post(
            self.logout_url, {"refresh": "invalid-token"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "refresh" in response.data

    def test_logout_already_blacklisted(self, user_factory):
        user = user_factory()
        refresh = RefreshToken.for_user(user)
        self.client.force_authenticate(user=user)
        response1 = self.client.post(
            self.logout_url, {"refresh": str(refresh)}, format="json"
        )
        assert response1.status_code == status.HTTP_200_OK
        response2 = self.client.post(
            self.logout_url, {"refresh": str(refresh)}, format="json"
        )
        assert response2.status_code == status.HTTP_200_OK
        assert "already blacklisted" in response2.data.get("detail", "").lower()

    def test_logout_requires_authentication(self):
        refresh = RefreshToken()
        response = self.client.post(
            self.logout_url, {"refresh": str(refresh)}, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_missing_refresh_field(self, user_factory):
        user = user_factory()
        self.client.force_authenticate(user=user)
        response = self.client.post(self.logout_url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "refresh" in response.data
