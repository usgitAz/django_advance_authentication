from datetime import timedelta

import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import TokenBlacklist


@pytest.mark.django_db
class TestTokenBlacklistAdmin:
    """Tests for TokenBlacklistAdmin customizations."""

    def test_jti_short_short_jti(self, token_blacklist_admin):
        """Short JTI should be returned unchanged."""
        obj = type("obj", (), {"jti": "shortjti"})()
        assert token_blacklist_admin.jti_short(obj) == "shortjti"

    def test_jti_short_long_jti(self, token_blacklist_admin):
        """Long JTI should be truncated with ellipsis."""
        obj = type("obj", (), {"jti": "a" * 30})()
        assert token_blacklist_admin.jti_short(obj) == "a" * 20 + "..."

    def test_has_add_permission(
        self, token_blacklist_admin, request_factory, admin_user
    ):
        """Manual addition should be disabled."""
        request = request_factory.get("/")
        request.user = admin_user
        assert token_blacklist_admin.has_add_permission(request) is False

    def test_has_delete_permission_superuser(
        self, token_blacklist_admin, request_factory, admin_user
    ):
        """Superuser should have delete permission."""
        request = request_factory.get("/")
        request.user = admin_user
        assert token_blacklist_admin.has_delete_permission(request) is True

    def test_has_delete_permission_staff_only(
        self, token_blacklist_admin, request_factory, staff_user
    ):
        """Non-superuser staff should not have delete permission."""
        request = request_factory.get("/")
        request.user = staff_user
        assert token_blacklist_admin.has_delete_permission(request) is False

    def test_cleanup_expired_tokens(
        self,
        token_blacklist_admin,
        request_factory,
        admin_user,
        token_blacklist_factory,
    ):
        """Custom action should delete expired tokens and show correct message."""
        token_blacklist_factory(
            expires_at=timezone.now() - timedelta(days=1)
        )  # expired
        token_blacklist_factory(expires_at=timezone.now() + timedelta(days=1))  # active

        request = request_factory.post("/")
        request.user = admin_user
        request.session = "session"
        messages = FallbackStorage(request)
        request._messages = messages

        queryset = TokenBlacklist.objects.all()
        token_blacklist_admin.cleanup_expired_tokens(request, queryset)

        message = list(messages)[0].message
        assert "Deleted 1 expired token entries" in message
        assert TokenBlacklist.objects.count() == 1

    def test_changelist_view_loads_and_displays_short_jti(
        self, admin_client, token_blacklist_factory
    ):
        """Changelist page should load and display shortened JTI."""
        long_jti = "x" * 40
        token_blacklist_factory(jti=long_jti)
        url = reverse("admin:accounts_tokenblacklist_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert "JWT ID" in str(response.content)
        assert ("x" * 20 + "...") in str(response.content)

    def test_add_button_not_present(self, admin_client):
        """Add button should be absent due to has_add_permission=False."""
        url = reverse("admin:accounts_tokenblacklist_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert b"Add token blacklist" not in response.content

    def test_search_by_user_email(self, admin_client, token_blacklist_factory):
        """Search should work on user__email field."""
        token_blacklist_factory(user__email="searchtest@example.com")
        url = (
            reverse("admin:accounts_tokenblacklist_changelist")
            + "?q=searchtest@example.com"
        )
        response = admin_client.get(url)
        assert response.status_code == 200
        assert "searchtest@example.com" in str(response.content)
