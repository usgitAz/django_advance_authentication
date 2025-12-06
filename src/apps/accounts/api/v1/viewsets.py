from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.permissions import IsOwnerOrStaff

from .serializers import (
    ChangePasswordSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

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
