import structlog
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models.jwt_token_blacklist import TokenBlacklist
from apps.accounts.models.user import User
from core.email import send_verification_email

logger = structlog.getLogger(__name__)


class UserCreateSerializer(serializers.ModelSerializer):
    """Serialize user data with password validation and use save method to hashing password."""

    password = serializers.CharField(
        min_length=8, write_only=True, style={"input_type": "password"}
    )
    retype_password = serializers.CharField(
        min_length=8, write_only=True, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "password",
            "retype_password",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]

    def validate(self, attrs):
        """Check password, retype_password fields be the same."""
        if attrs.get("password") != attrs.get("retype_password"):
            raise serializers.ValidationError(
                {
                    "password": ["Passwords do not match"],
                    "retype_password": ["Passwords do not match"],
                }
            )
        return attrs

    def create(self, validate_data):
        validate_data.pop("retype_password", None)
        password = validate_data.pop("password")
        user = User.objects.create_user(
            password=password, email_verified=False, **validate_data
        )
        # Send verification email (non-blocking failure)
        try:
            send_verification_email(user)
        except Exception:
            # Already logged in send_verification_email
            logger.warning(
                "user created but verification email failed",
                user_id=user.pk,
            )
            # Don't fail user creation if email fails

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Only first_name and last_name can be change."""

    class Meta:
        model = User
        fields = ["first_name", "last_name"]


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "date_joined",
            "is_active",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Change authenticated user password.

    Check new_password & retype password be thes same &
    Check that the new password is not the same as the previous password.
    """

    old_password = serializers.CharField(min_length=8, write_only=True)
    new_password = serializers.CharField(min_length=8, write_only=True)
    retype_password = serializers.CharField(min_length=8, write_only=True)

    def validate(self, attrs):
        if attrs.get("new_password") != attrs.get("retype_password"):
            raise serializers.ValidationError(
                {
                    "new_password": ["Passwords do not match"],
                    "retype_password": ["Passwords do not match"],
                }
            )
        if attrs.get("new_password") == attrs.get("old_password"):
            raise serializers.ValidationError(
                {"new_password": ["New password must be different"]}
            )
        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data["new_password"])
        instance.save(update_fields=["password"])
        return instance


class LogoutSerializer(serializers.Serializer):
    """Logout serializer to blacklist refresh token.

    Validates the refresh token and prepares it for blacklisting.
    """

    refresh = serializers.CharField(
        write_only=True,
        help_text="Refresh token to be blacklisted",
    )

    def validate_refresh(self, value):
        """Validate the refresh token."""
        try:
            RefreshToken(value)
        except Exception as e:
            raise serializers.ValidationError(f"Invalid refresh token: {str(e)}") from e
        return value

    def save(self, user):
        """Blacklist the refresh token."""
        refresh_token = RefreshToken(self.validated_data["refresh"])

        # Get token claims
        jti = refresh_token.get("jti")
        exp = refresh_token.get("exp")

        if not jti or not exp:
            raise serializers.ValidationError(
                "Invalid token structure - missing jti or exp claim"
            )

        # Check if already blacklisted
        if TokenBlacklist.is_blacklisted(jti):
            return {"detail": "Token already blacklisted"}

        # Blacklist the token
        TokenBlacklist.blacklist_token(
            user=user,
            jti=jti,
            exp_timestamp=exp,
            reason="logout",
        )

        return {"detail": "Successfully logged out"}


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh_token_str = attrs["refresh"]
        refresh = RefreshToken(refresh_token_str)

        jti = refresh["jti"]
        # check refresh token alreay in blacklist?
        if TokenBlacklist.is_blacklisted(jti):
            raise TokenError("Token has been revoked/blacklisted.")

        # generate new token
        data = super().validate(attrs)

        # extract user_id from jwt payload
        user_id = refresh.payload.get("user_id")
        user = User.objects.filter(id=user_id).first()

        # save old token in to blacklist
        TokenBlacklist.blacklist_token(
            user=user,
            jti=jti,
            exp_timestamp=refresh["exp"],
            reason="rotation",
        )

        return data
