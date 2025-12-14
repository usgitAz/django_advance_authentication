import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models.jwt_token_blacklist import TokenBlacklist


@pytest.mark.django_db
class TestJWTBlacklistBehavior:
    """Tests for logout and refresh token blacklisting."""

    def test_logout_blacklists_refresh_token(self, api_client, user_factory):
        user = user_factory()
        refresh = RefreshToken.for_user(user)
        old_jti = refresh["jti"]

        api_client.force_authenticate(user=user)
        response = api_client.post(
            "/api/v1/users/logout/", {"refresh": str(refresh)}, format="json"
        )

        assert response.status_code == 200
        assert response.json()["detail"] == "Successfully logged out"
        assert TokenBlacklist.objects.filter(jti=old_jti, reason="logout").exists()

    def test_refresh_blacklists_old_token(self, api_client, user_factory):
        user = user_factory()
        refresh = RefreshToken.for_user(user)
        old_jti = refresh["jti"]

        response = api_client.post(
            "/api/v1/token/refresh/", {"refresh": str(refresh)}, format="json"
        )

        assert response.status_code == 200
        assert "access" in response.json()
        assert TokenBlacklist.objects.filter(jti=old_jti, reason="rotation").exists()

    def test_refresh_does_not_duplicate_blacklist(self, api_client, user_factory):
        user = user_factory()
        refresh = RefreshToken.for_user(user)
        old_jti = refresh["jti"]

        # first save in black list manualy
        TokenBlacklist.blacklist_token(
            user=user,
            jti=old_jti,
            exp_timestamp=refresh["exp"],
            reason="rotation",
        )

        initial_count = TokenBlacklist.objects.count()

        # now refreshed
        api_client.post(
            "/api/v1/token/refresh/", {"refresh": str(refresh)}, format="json"
        )

        # The number should not increase
        assert TokenBlacklist.objects.count() == initial_count

    def test_refresh_with_already_blacklisted_token_fails(
        self, api_client, user_factory
    ):
        user = user_factory()
        refresh = RefreshToken.for_user(user)

        TokenBlacklist.blacklist_token(
            user=user,
            jti=refresh["jti"],
            exp_timestamp=refresh["exp"],
            reason="manual",
        )

        response = api_client.post(
            "/api/v1/token/refresh/", {"refresh": str(refresh)}, format="json"
        )

        assert response.status_code == 401
        assert "Token has been revoked" in str(response.content)
