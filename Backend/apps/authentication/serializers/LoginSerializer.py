# apps/authentication/serializers/LoginSerializer.py

import logging
from rest_framework import serializers
from apps.authentication.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from apps.authentication.services.otp.otp_service import OtpService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LoginRequestOtpSerializer(serializers.Serializer):
    identifier = serializers.CharField()   # email or mobile

    def validate(self, attrs):
        identifier = attrs["identifier"]

        user = (
            User.objects.filter(mobile_number=identifier).first() or
            User.objects.filter(email=identifier).first()
        )

        if not user:
            logger.warning(f"[LOGIN OTP] User not found for identifier={identifier}")
            raise serializers.ValidationError("User not found")

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        identifier = validated_data["identifier"]

        if identifier == user.mobile_number:
            OtpService.send_mobile_otp(identifier)
            logger.info(f"[LOGIN OTP] Mobile OTP sent to {identifier}")
        else:
            OtpService.send_email_otp(identifier)
            logger.info(f"[LOGIN OTP] Email OTP sent to {identifier}")

        return {"message": "OTP sent successfully", "identifier": identifier}


class LoginVerifyOtpSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    otp = serializers.CharField()

    def validate(self, attrs):
        identifier = attrs["identifier"]
        otp = attrs["otp"]

        if User.objects.filter(mobile_number=identifier).exists():
            otp_type = "MOBILE"
        else:
            otp_type = "EMAIL"

        ok, msg = OtpService.verify_otp(identifier, otp, otp_type)
        if not ok:
            logger.warning(f"[LOGIN VERIFY] OTP failed for {identifier}: {msg}")
            raise serializers.ValidationError(msg)

        user = (
            User.objects.filter(mobile_number=identifier).first()
            or User.objects.filter(email=identifier).first()
        )

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]

        refresh = RefreshToken.for_user(user)
        logger.info(f"[LOGIN VERIFY] OTP verified successfully for user={user.id}")

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user_id": user.id,
            "role": user.role,
            "message": "Login successful"
        }
