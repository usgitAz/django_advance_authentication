import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient

from .factories import UserFactory

register(UserFactory)


@pytest.fixture
def admin_user(user_factory):
    return user_factory(is_staff=True, is_superuser=True)


@pytest.fixture
def api_client():
    return APIClient()
