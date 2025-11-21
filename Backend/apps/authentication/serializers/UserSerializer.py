from apps.authentication.models import User
from rest_framework import serializers
from apps.authentication.services.verification_store import VerificationStore
from apps.authentication.models import Role



class CreateUserSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6)
    role = serializers.CharField()

    def validate(self, attrs):
        request = self.context["request"]

        mobile = request.data.get("mobile_number")
        email = request.data.get("email")

        if not mobile:
            raise serializers.ValidationError({"mobile_number": "Mobile number is required"})

        if not email:
            raise serializers.ValidationError({"email": "Email is required"})


        if not VerificationStore.is_mobile_verified(request, mobile):
            raise serializers.ValidationError("Mobile not verified")

        if not VerificationStore.is_email_verified(request, email):
            raise serializers.ValidationError("Email not verified")

        return attrs

    def create(self, validated_data):
        request = self.context["request"]

        role_name = validated_data["role"]
        role_obj = Role.objects.get(name=role_name)

        user = User.objects.create_user(
            email=request.data.get("email"),
            mobile_number=request.data.get("mobile_number"),
            password=validated_data["password"],
            role=role_obj
        )

        return user


