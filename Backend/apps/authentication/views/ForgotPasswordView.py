# apps/authentication/views/ForgotPasswordView.py

import logging
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from apps.authentication.serializers.ForgotPasswordSerializer import (
    ForgotPasswordRequestSerializer,
    ForgotPasswordResetSerializer,
)
from config.common.response import APIResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ForgotPasswordRequestOtpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()

        logger.info(f"[FORGOT PASSWORD OTP VIEW] OTP sent to {data['identifier']}")
        return APIResponse.success(data=data, message="OTP sent")


class ForgotPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()

        logger.info("[FORGOT PASSWORD RESET VIEW] Password reset successful")
        return APIResponse.success(data=data, message="Password reset successful")
