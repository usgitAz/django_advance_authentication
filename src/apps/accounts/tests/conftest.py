import pytest
from pytest_factoryboy import register

from .factories import UserFactory

register(UserFactory)


@pytest.fixture
def admin_user(user_factory):
    """admin user fixture"""
    return user_factory(is_staff=True, is_superuser=True)
