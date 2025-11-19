from apps.authentication.models import User
from apps.authentication.services.session_manager import VerificationSession
from rest_framework import serializers

class CreateUserSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6)
    role = serializers.CharField()

    def validate(self, attrs):
        request = self.context["request"]

        if not VerificationSession.is_mobile_verified(request):
            raise serializers.ValidationError("Mobile not verified")

        if not VerificationSession.is_email_verified(request):
            raise serializers.ValidationError("Email not verified")

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        mobile = request.session["verified_mobile"]
        email = request.session["verified_email"]

        user = User.objects.create_user(
            mobile_number=mobile,
            email=email,
            password=validated_data["password"],
            role=validated_data["role"]
        )

        user.mobile_verified = True
        user.email_verified = True
        user.save()

        return user
