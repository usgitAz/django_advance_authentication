from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import TokenBlacklist, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "is_staff", "is_active"]
    list_filter = ["is_staff", "is_active"]

    search_fields = ("email", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )

    readonly_fields = ["date_joined", "updated_at", "id"]


@admin.register(TokenBlacklist)
class TokenBlacklistAdmin(admin.ModelAdmin):
    """Admin interface for managing blacklisted tokens."""

    list_display = ["user", "jti_short", "reason", "blacklisted_at", "expires_at"]
    list_filter = ["reason", "blacklisted_at", "expires_at"]
    search_fields = ["user__email", "jti"]
    readonly_fields = ["id", "blacklisted_at", "jti"]

    fieldsets = (
        (None, {"fields": ("id", "user", "jti")}),
        (_("Reason & Timing"), {"fields": ("reason", "blacklisted_at", "expires_at")}),
    )

    def jti_short(self, obj):
        """Display shortened JTI for readability."""
        if len(obj.jti) > 20:
            return f"{obj.jti[:20]}..."
        return obj.jti

    jti_short.short_description = "JWT ID"

    def has_add_permission(self, request):
        """Don't allow manual creation via admin."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow admin to delete blacklist entries."""
        return request.user.is_superuser

    actions = ["cleanup_expired_tokens"]

    def cleanup_expired_tokens(self, request, queryset):
        """Admin action to cleanup expired tokens."""
        deleted_count, _ = TokenBlacklist.cleanup_expired()
        self.message_user(request, f"Deleted {deleted_count} expired token entries.")

    cleanup_expired_tokens.short_description = "Clean up expired tokens"
