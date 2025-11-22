import pytest
from django.utils import timezone

from apps.accounts.models import User


@pytest.mark.django_db
def test_create_user(user_factory):
    """Check creating normal user with factory"""
    new_user = user_factory(email="newuser@email.com")
    assert User.objects.count() == 1
    assert new_user.email == "newuser@email.com"
    assert new_user.check_password("password1234")
    assert not new_user.is_staff
    assert not new_user.is_superuser
    assert new_user.is_active
    assert new_user.date_joined <= timezone.now()
    assert str(new_user) == "newuser@email.com"


@pytest.mark.django_db
def test_create_superuser(admin_user):
    "Check ceating superuser with factory"
    admin = admin_user
    assert admin.is_staff
    assert admin.is_superuser
    assert admin.is_active


@pytest.mark.django_db
def test_full_name_property(user_factory):
    """Test full name property in user model"""
    sample_user = user_factory(
        first_name="sample_firstname", last_name="sample_lastname"
    )
    sample_user.first_name = "sample_firstname"
    sample_user.last_name = "sample_lastname"
    assert sample_user.full_name == "sample_firstname sample_lastname"


@pytest.mark.django_db
def test_custom_manager_create_user():
    """Check all fileds after creating normal user"""
    user = User.objects.create_user(
        email="normal@example.com",
        password="pass123",
        first_name="Normal",
    )
    assert user.email == "normal@example.com"
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.check_password("pass123") is True


@pytest.mark.django_db
def test_custom_manager_create_superuser():
    """Check all fields after creating admin/superuser with manager"""
    superuser = User.objects.create_superuser(
        email="admin@example.com",
        password="adminpass",
    )
    assert superuser.email == "admin@example.com"
    assert superuser.is_active is True
    assert superuser.is_staff is True
    assert superuser.is_superuser is True
    assert superuser.check_password("adminpass") is True


@pytest.mark.django_db
def test_create_user_manager_without_emails():
    """Ensure get a value error when have a empty email field"""
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="pass123")


@pytest.mark.django_db
def test_superuser_manager_rules():
    """Check superuser rules (is_staff , is_super user)"""
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="superusermanager@mail.com", password="pass123", is_superuser=False
        )
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="superusermanager@mail.com",
            password="pass123",
            is_staff=False,
            is_superuser=False,
        )


@pytest.mark.django_db
def test_create_batch_users(user_factory):
    """Verify create_batch() creates the correct number of active users."""
    users = user_factory.create_batch(5)
    assert User.objects.count() == 5
    assert all(user.is_active for user in users)
