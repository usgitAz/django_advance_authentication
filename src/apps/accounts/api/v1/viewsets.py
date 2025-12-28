import structlog
from django.contrib.auth import get_user_model
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenRefreshView

from core.email import verify_email_token
from core.permissions import IsOwnerOrStaff

from .serializers import (
    ChangePasswordSerializer,
    CustomTokenRefreshSerializer,
    LogoutSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

logger = structlog.get_logger(__name__)

User = get_user_model()


class UserViewSet(ModelViewSet):
    """Manage user accounts - CRUD with strict permissions.

    - Anyone can register
    - Users can view/update only themselves
    - Only staff can list/delete
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Allow anyone to register, only admin can list/destroy."""
        if self.action == "create":
            return [AllowAny()]
        if self.action in ["list", "destroy"]:
            return [IsAdminUser()]
        if self.action in ["update", "retrieve", "partial_update"]:
            return [IsAuthenticated(), IsOwnerOrStaff()]
        return super().get_permissions()

    def get_serializer_class(self):
        """Use diffrent serilizers for create and update actions."""
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return super().get_serializer_class()

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        serializer_class=ChangePasswordSerializer,
    )
    def change_password(self, request):
        """Create change_password route to change current user password."""
        user = request.user

        if not user.check_password(request.data.get("old_password")):
            return Response(
                {"old_password": ["Wrong Password"]}, status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # update and save password with serializer updated method
        serializer.update(user, serializer.validated_data)
        return Response(
            {"detail": "Password changed successfully"}, status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        serializer_class=LogoutSerializer,
    )
    def logout(self, request):
        """Logout endpoint to blacklist the refresh token.

        This prevents the token from being reused even if compromised.
        Client should delete both access and refresh tokens from local storage.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response_data = serializer.save(user=request.user)

        return Response(response_data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Email verification token",
                required=True,
            )
        ],
        responses={
            200: {
                "description": "Email verified successfully or already verified",
                "examples": {
                    "application/json": {
                        "detail": "Email has been successfully verified."
                    }
                },
            },
            400: {
                "description": "Invalid or expired token",
                "examples": {
                    "application/json": {"detail": "The link is expired or invalid."}
                },
            },
        },
        description="Verify user email address using the token sent via email.",
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[AllowAny],
        url_path="verify-email/(?P<token>[^/.]+)",
    )
    def verify_email(self, request, token):
        """Verify user email with token."""
        try:
            user = verify_email_token(token)

            if user is None:
                logger.warning("invalid or expired token", token_preview=token[:20])
                return Response(
                    {"detail": "The link is expired or invalid."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if user.email_verified:
                logger.info("email already verified", user_id=user.id)
                return Response(
                    {"detail": "This email is already verified."},
                    status=status.HTTP_200_OK,
                )

            user.email_verified = True
            user.save(update_fields=["email_verified"])

            logger.info(
                "email verified successfully", user_id=user.id, user_email=user.email
            )

            return Response(
                {"detail": "Email has been successfully verified."},
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            logger.error("token format error", error=str(e))
            return Response(
                {"detail": "Invalid token format."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.exception(
                "verification failed - unexpected error",
                error_type=type(e).__name__,
            )
            return Response(
                {"detail": "An error occurred during verification. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer
