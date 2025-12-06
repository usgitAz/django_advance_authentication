import pytest


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
