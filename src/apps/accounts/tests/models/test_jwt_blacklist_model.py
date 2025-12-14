import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.accounts.models.jwt_token_blacklist import TokenBlacklist


@pytest.mark.django_db
class TestTokenBlacklistModel:
    """Test TokenBlacklist model functionality."""

    def test_blacklist_token_creation_and_str(self, user_factory):
        user = user_factory()
        jti = "test-jti-1"
        exp = timezone.now() + timezone.timedelta(days=1)
        exp_timestamp = int(exp.timestamp())
        entry = TokenBlacklist.blacklist_token(
            user=user, jti=jti, exp_timestamp=exp_timestamp, reason="logout"
        )
        assert entry.jti == jti
        assert entry.user == user
        assert entry.reason == "logout"
        assert user.email in str(entry)
        assert entry.expires_at.tzinfo is not None

    def test_is_blacklisted_true_false(self, user_factory):
        user = user_factory()
        jti = "test-jti-2"
        exp = timezone.now() + timezone.timedelta(days=1)
        exp_timestamp = int(exp.timestamp())
        assert not TokenBlacklist.is_blacklisted(jti)
        TokenBlacklist.blacklist_token(user=user, jti=jti, exp_timestamp=exp_timestamp)
        assert TokenBlacklist.is_blacklisted(jti)

    def test_duplicate_blacklist_prevention(self, user_factory):
        user = user_factory()
        jti = "test-jti-3"
        exp = timezone.now() + timezone.timedelta(days=1)
        exp_timestamp = int(exp.timestamp())
        TokenBlacklist.blacklist_token(user=user, jti=jti, exp_timestamp=exp_timestamp)
        with pytest.raises(IntegrityError):
            TokenBlacklist.blacklist_token(
                user=user, jti=jti, exp_timestamp=exp_timestamp
            )

    def test_cleanup_expired_tokens(self, user_factory):
        user = user_factory()
        # expired
        past_exp = timezone.now() - timezone.timedelta(days=1)
        past_exp_timestamp = int(past_exp.timestamp())
        TokenBlacklist.blacklist_token(
            user=user, jti="expired-jti", exp_timestamp=past_exp_timestamp
        )
        # valid
        future_exp = timezone.now() + timezone.timedelta(days=7)
        future_exp_timestamp = int(future_exp.timestamp())
        TokenBlacklist.blacklist_token(
            user=user, jti="valid-jti", exp_timestamp=future_exp_timestamp
        )
        deleted_count, _ = TokenBlacklist.cleanup_expired()
        assert deleted_count >= 1
        assert not TokenBlacklist.is_blacklisted("expired-jti")
        assert TokenBlacklist.is_blacklisted("valid-jti")
