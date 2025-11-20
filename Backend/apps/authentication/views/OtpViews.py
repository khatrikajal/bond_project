from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import Throttled

from ..serializers.OtpSerilizer import (
    SendMobileOtpSerializer,
    VerifyMobileOtpSerializer,
    SendEmailOtpSerializer,
    VerifyEmailOtpSerializer,
)
from django.contrib.auth import get_user_model
from config.common.response import APIResponse
from ..throttling import OtpThrottle

User = get_user_model()


class SendMobileOtpView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OtpThrottle]

    def post(self, request):
        mobile = request.data.get("mobile_number")

        # Business rule (correct place)
        if User.objects.filter(mobile_number=mobile).exists():
            return APIResponse.error(
                message="User already exists with this mobile",
                errors={"mobile_number": "User already exists with this mobile"},
                status_code=400
            )

        serializer = SendMobileOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()

        return APIResponse.success(message=data["message"])


class VerifyMobileOtpView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OtpThrottle]

    def post(self, request):
        serializer = VerifyMobileOtpSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.save()

        return APIResponse.success(message="Mobile verified", data=data)


class SendEmailOtpView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OtpThrottle]

    def post(self, request):
        email = request.data.get("email")

        if User.objects.filter(email=email).exists():
            return APIResponse.error(
                message="User already exists with this email",
                errors={"email": "User already exists with this email"},
                status_code=400
            )

        serializer = SendEmailOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()

        return APIResponse.success(message="OTP sent")


class VerifyEmailOtpView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OtpThrottle]

    def post(self, request):
        serializer = VerifyEmailOtpSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.save()

        return APIResponse.success(message="Email verified", data=data)
