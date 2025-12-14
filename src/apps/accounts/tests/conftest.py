import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from pytest_factoryboy import register
from rest_framework.test import APIClient

from apps.accounts.admin import TokenBlacklistAdmin
from apps.accounts.models import TokenBlacklist

from .factories import TokenBlacklistFactory, UserFactory

register(UserFactory)
register(TokenBlacklistFactory)


@pytest.fixture
def admin_user(user_factory):
    """Superuser with staff access."""
    return user_factory(is_staff=True, is_superuser=True)


@pytest.fixture
def staff_user(user_factory):
    """Staff user without superuser privileges."""
    return user_factory(is_staff=True, is_superuser=False)


@pytest.fixture
def api_client():
    """Unauthenticated DRF API client."""
    return APIClient()


@pytest.fixture
def admin_client(client, admin_user):
    """Django test client logged as admin."""
    client.force_login(admin_user)
    return client


@pytest.fixture
def request_factory():
    """Django RequestFactory Instance."""
    return RequestFactory()


@pytest.fixture
def token_blacklist_admin():
    """Instance of TokenBlackListAdmin for unit testing."""
    return TokenBlacklistAdmin(TokenBlacklist, AdminSite())
