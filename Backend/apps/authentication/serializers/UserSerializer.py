from apps.authentication.models import User
from rest_framework import serializers
from apps.authentication.services.verification_store import VerificationStore



class CreateUserSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6)
    role = serializers.CharField()

    def validate(self, attrs):
        request = self.context["request"]

        mobile = request.data.get("mobile_number")
        email = request.data.get("email")

        if not VerificationStore.is_mobile_verified(request, mobile):
            raise serializers.ValidationError("Mobile not verified")

        if not VerificationStore.is_email_verified(request, email):
            raise serializers.ValidationError("Email not verified")

        return attrs

