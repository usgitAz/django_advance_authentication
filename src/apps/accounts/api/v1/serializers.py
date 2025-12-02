from rest_framework import serializers

from apps.accounts.models.user import User


class UserCreateSerializer(serializers.ModelSerializer):
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
        user = User.objects.create_user(password=password, **validate_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
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
