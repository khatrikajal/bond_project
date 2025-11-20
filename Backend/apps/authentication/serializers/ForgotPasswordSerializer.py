# apps/authentication/serializers/ForgotPasswordSerializer.py

import logging
from rest_framework import serializers
from apps.authentication.models import User
from apps.authentication.services.otp.otp_service import OtpService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ForgotPasswordRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField()

    def validate(self, attrs):
        identifier = attrs["identifier"]

        user = (
            User.objects.filter(mobile_number=identifier).first() or
            User.objects.filter(email=identifier).first()
        )

        if not user:
            logger.warning(f"[FORGOT PASSWORD] User not found for {identifier}")
            raise serializers.ValidationError("User not found")

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        identifier = validated_data["identifier"]

        if identifier == user.mobile_number:
            OtpService.send_mobile_otp(identifier)
        else:
            OtpService.send_email_otp(identifier)

        logger.info(f"[FORGOT PASSWORD] OTP sent to {identifier}")
        return {"message": "OTP sent successfully", "identifier": identifier}


class ForgotPasswordResetSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    otp = serializers.CharField()
    new_password = serializers.CharField(min_length=6)

    def validate(self, attrs):
        identifier = attrs["identifier"]
        otp = attrs["otp"]

        user = (
            User.objects.filter(mobile_number=identifier).first()
            or User.objects.filter(email=identifier).first()
        )

        if not user:
            logger.warning(f"[RESET PASSWORD] User not found for {identifier}")
            raise serializers.ValidationError("User not found")

        otp_type = "MOBILE" if user.mobile_number == identifier else "EMAIL"

        ok, msg = OtpService.verify_otp(identifier, otp, otp_type)
        if not ok:
            logger.warning(f"[RESET PASSWORD] OTP failed for {identifier}: {msg}")
            raise serializers.ValidationError(msg)

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        new_password = validated_data["new_password"]

        user.set_password(new_password)
        user.save()

        logger.info(f"[RESET PASSWORD] Password reset successful for user={user.id}")

        return {"message": "Password reset successful"}
