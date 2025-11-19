import logging
from rest_framework import serializers
from apps.authentication.services.otp.otp_service import OtpService
from apps.authentication.services.session_manager import VerificationSession


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



class SendMobileOtpSerializer(serializers.Serializer):
    mobile_number = serializers.CharField()

    def validate_mobile_number(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Invalid mobile number")
        return value

    def create(self, validated_data):
        OtpService.send_mobile_otp(validated_data["mobile_number"])
        return {"message": "OTP sent", "mobile_number": validated_data["mobile_number"]}

class VerifyMobileOtpSerializer(serializers.Serializer):
    mobile_number = serializers.CharField()
    otp = serializers.CharField()

    def validate(self, attrs):
        ok, message = OtpService.verify_otp(
            attrs["mobile_number"],
            attrs["otp"],
            "MOBILE"
        )

        if not ok:
            raise serializers.ValidationError(message)

        return attrs

    def save(self):
        request = self.context["request"]
        mobile = self.validated_data["mobile_number"]

        VerificationSession.set_mobile_verified(request, mobile)

        return {
            "mobile_verified": True,
            "mobile_number": mobile
        }






class SendEmailOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def create(self, validated_data):
        OtpService.send_email_otp(validated_data["email"])
        return {"email": validated_data["email"], "message": "OTP sent"}

class VerifyEmailOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()

    def validate(self, attrs):
        ok, message = OtpService.verify_otp(
            attrs["email"],
            attrs["otp"],
            "EMAIL"
        )

        if not ok:
            raise serializers.ValidationError(message)

        return attrs

    def save(self):
        request = self.context["request"]
        email = self.validated_data["email"]

        VerificationSession.set_email_verified(request, email)

        return {
            "email_verified": True,
            "email": email
        }
