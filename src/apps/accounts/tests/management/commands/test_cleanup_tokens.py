from datetime import timedelta
from io import StringIO
from uuid import uuid4

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.accounts.models.jwt_token_blacklist import TokenBlacklist


@pytest.mark.django_db
class TestCleanupTokensCommand:
    """Tests for the clean up management command."""

    @pytest.fixture(autouse=True)
    def setup(self, user_factory):
        self.user = user_factory()
        self.out = StringIO()

    def create_blacklist_token(self, expires_days: int):
        """Generate a custom black list token."""
        return TokenBlacklist.objects.create(
            user=self.user,
            jti="test_jti" + str(uuid4()),
            expires_at=timezone.now() + timedelta(expires_days),
            reason="logout",
        )

    def test_no_expired_tokens(self):
        self.create_blacklist_token(expires_days=7)  # valid token

        call_command("cleanup_tokens", stdout=self.out)

        output = self.out.getvalue()
        assert "No expired tokens to clean up" in output
        assert TokenBlacklist.objects.count() == 1

    def test_dry_run_shows_count_without_deleting(self):
        self.create_blacklist_token(expires_days=-1)  # expired
        self.create_blacklist_token(expires_days=-2)  # expired
        self.create_blacklist_token(expires_days=1)  # active

        call_command("cleanup_tokens", "--dry-run", stdout=self.out)

        output = self.out.getvalue()

        assert "[DRY RUN] Would delete 2 expired token entries" in output
        assert "Total tokens in blacklist: 3" in output
        assert TokenBlacklist.objects.count() == 3  # nothing has been deleted

    def test_actual_cleanup_deletes_only_expired_tokens(self):
        expired1 = self.create_blacklist_token(expires_days=-5)
        expired2 = self.create_blacklist_token(expires_days=-1)
        active = self.create_blacklist_token(expires_days=3)

        call_command("cleanup_tokens", stdout=self.out)

        output = self.out.getvalue()
        assert "Successfully deleted 2 expired token entries" in output
        assert "Total tokens in blacklist: 1" in output

        assert not TokenBlacklist.objects.filter(
            pk__in=[expired1.pk, expired2.pk]
        ).exists()
        assert TokenBlacklist.objects.filter(pk=active.pk).exists()
        assert TokenBlacklist.objects.count() == 1
