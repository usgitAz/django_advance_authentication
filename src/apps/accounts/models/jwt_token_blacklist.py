import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class TokenBlacklist(models.Model):
    """Store blacklisted refresh tokens to prevent token reuse.

    When a user logs out or a token is rotated, the token's jti (JWT ID)
    is added to this blacklist. During token validation, we check if the
    jti is in the blacklist.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="blacklisted_tokens",
        help_text=_("The user who logged out or had token rotated"),
    )
    jti = models.CharField(
        _("JWT ID"),
        max_length=255,
        unique=True,
        db_index=True,
        help_text=_("Unique JWT ID (jti claim) to identify the token"),
    )
    blacklisted_at = models.DateTimeField(
        _("blacklisted at"),
        auto_now_add=True,
        help_text=_("Timestamp when token was blacklisted"),
    )
    expires_at = models.DateTimeField(
        _("token expiry time"),
        help_text=_("Token expiration time - after this, the entry can be deleted"),
    )
    reason = models.CharField(
        _("reason for blacklist"),
        max_length=50,
        choices=[
            ("logout", _("User logged out")),
            ("rotation", _("Token rotated")),
            ("revocation", _("Token revoked by admin")),
            ("password_change", _("User changed password")),
        ],
        default="logout",
        help_text=_("Reason for token blacklist"),
    )

    class Meta:
        verbose_name = _("Token Blacklist")
        verbose_name_plural = _("Token Blacklists")
        ordering = ["-blacklisted_at"]
        indexes = [
            models.Index(fields=["user", "blacklisted_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_reason_display()}"

    @classmethod
    def is_blacklisted(cls, jti: str) -> bool:
        """Check if a JWT ID is blacklisted."""
        return cls.objects.filter(jti=jti).exists()

    @classmethod
    def blacklist_token(
        cls, user, jti: str, exp_timestamp: int, reason: str = "logout"
    ):
        """Add a token to the blacklist.

        Args:
            user: User instance
            jti: JWT ID claim from the token
            exp_timestamp: Token expiration timestamp (from 'exp' claim)
            reason: Reason for blacklisting

        """
        from datetime import datetime

        expires_at = datetime.fromtimestamp(
            exp_timestamp, tz=timezone.get_current_timezone()
        )
        return cls.objects.create(
            user=user,
            jti=jti,
            expires_at=expires_at,
            reason=reason,
        )

    @classmethod
    def cleanup_expired(cls):
        """Delete expired tokens from blacklist to save space.

        Returns:
            tuple: (deleted_count, delete_details_dict)

        """
        return cls.objects.filter(expires_at__lte=timezone.now()).delete()
