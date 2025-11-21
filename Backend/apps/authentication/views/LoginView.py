# apps/authentication/views/LoginView.py

import logging
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from apps.authentication.serializers.LoginSerializer import (
    LoginRequestOtpSerializer,
    LoginVerifyOtpSerializer,
)
from config.common.response import APIResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LoginRequestOtpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginRequestOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        logger.info(f"[LOGIN OTP VIEW] OTP sent to {data['identifier']}")
        data.pop("message")
        return APIResponse.success(data=data, message="OTP sent")


class LoginVerifyOtpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginVerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        logger.info(f"[LOGIN VERIFY VIEW] Login successful for user={data['user_id']}")
        data.pop("message", None)
        return APIResponse.success(data=data, message="Login successful")
