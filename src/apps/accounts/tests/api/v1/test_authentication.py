import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models.jwt_token_blacklist import TokenBlacklist


@pytest.mark.django_db
class TestBlacklistAuthentication:
    """Test JWT authentication with blacklist checking."""

    def test_authenticated_user_with_valid_token(self, user_factory):
        user = user_factory()
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = client.get("/api/v1/users/")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]

    def test_authenticated_user_with_blacklisted_token(self, user_factory):
        user = user_factory()
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        jti = access.get("jti")
        exp_timestamp = int((timezone.now() + timezone.timedelta(hours=1)).timestamp())
        TokenBlacklist.blacklist_token(user=user, jti=jti, exp_timestamp=exp_timestamp)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = client.get("/api/v1/users/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_rotation_blacklisting(self, user_factory):
        user = user_factory()
        refresh1 = RefreshToken.for_user(user)
        jti1 = refresh1.get("jti")
        refresh2 = RefreshToken.for_user(user)
        jti2 = refresh2.get("jti")
        assert jti1 != jti2
        exp_timestamp = int((timezone.now() + timezone.timedelta(days=7)).timestamp())
        TokenBlacklist.blacklist_token(
            user=user, jti=jti1, exp_timestamp=exp_timestamp, reason="rotation"
        )
        assert TokenBlacklist.is_blacklisted(jti1)
        assert not TokenBlacklist.is_blacklisted(jti2)
