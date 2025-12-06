import pytest

from apps.accounts.api.v1.serializers import (
    ChangePasswordSerializer,
    UserCreateSerializer,
)


@pytest.mark.django_db
class TestUserCreateSerializer:
    """Test user creation with correct value and hashed password."""

    def test_passwords_must_match(self):
        data = {
            "email": "test@example.com",
            "password": "password123",
            "retype_password": "different",
            "first_name": "user_first_name",
            "last_name": "user_last_name",
        }

        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert serializer.errors.get("password")[0] == "Passwords do not match"

    def test_user_create_hases_password(self):
        data = {
            "email": "test@example.com",
            "password": "password123",
            "retype_password": "password123",
            "first_name": "user_first_name",
            "last_name": "user_last_name",
        }

        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid()
        user = serializer.save()
        assert user.check_password("password123")
        assert user.email == "test@example.com"


class TestChangePasswordSerializer:
    """Test user change password serializer in all situations."""

    def test_new_password_can_not_be_same_as_old(self):
        data = {
            "old_password": "oldpass123",
            "new_password": "oldpass123",
            "retype_password": "oldpass123",
        }
        serilizer = ChangePasswordSerializer(data=data)
        assert not serilizer.is_valid()
        assert (
            serilizer.errors.get("new_password")[0] == "New password must be different"
        )

    def test_change_passwords_must_be_match(self):
        data = {
            "old_password": "oldpass123",
            "new_password": "newpass123",
            "retype_password": "diffrent",
        }

        serializer = ChangePasswordSerializer(data=data)
        assert not serializer.is_valid()

    def test_valid_change_password(self):
        data = {
            "old_password": "oldpass123",
            "new_password": "newpass123",
            "retype_password": "newpass123",
        }
        serializer = ChangePasswordSerializer(data=data)
        assert serializer.is_valid()
        validated = serializer.validated_data
        assert validated["new_password"] == "newpass123"
