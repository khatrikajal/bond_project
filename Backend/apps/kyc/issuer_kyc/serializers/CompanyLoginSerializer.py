import logging
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

User = get_user_model()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CompanyLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        # 1. Validate user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.warning(f"[COMPANY LOGIN] User not found: {email}")
            raise serializers.ValidationError({"email": "Invalid credentials"})

        # 2. Authenticate
        user = authenticate(email=email, password=password)
        if not user:
            logger.warning(f"[COMPANY LOGIN] Incorrect password for: {email}")
            raise serializers.ValidationError({"password": "Invalid credentials"})

        # 3. Validate account status
        if not user.is_active:
            logger.warning(f"[COMPANY LOGIN] Inactive user attempted login: {email}")
            raise serializers.ValidationError({"email": "Account disabled. Contact support."})

        attrs["user"] = user
        return attrs