from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email_or_username = (attrs.pop("email", "") or "").strip()
        username = (attrs.get("username", "") or "").strip()

        if not email_or_username and not username:
            raise serializers.ValidationError(
                {"detail": "Provide an email or username with your password."}
            )

        if email_or_username and not username:
            if "@" in email_or_username:
                try:
                    user = User.objects.get(email__iexact=email_or_username)
                    attrs["username"] = user.get_username()
                except User.DoesNotExist:
                    attrs["username"] = email_or_username
            else:
                attrs["username"] = email_or_username
        elif username:
            attrs["username"] = username

        return super().validate(attrs)
