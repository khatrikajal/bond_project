from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import Throttled

from ..serializers.OtpSerilizer import (
    SendMobileOtpSerializer,
    VerifyMobileOtpSerializer,
    SendEmailOtpSerializer,
    VerifyEmailOtpSerializer,
)

from config.common.response import APIResponse
from ..throttling import OtpThrottle



class SendMobileOtpView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OtpThrottle]

    def post(self, request):
        serializer = SendMobileOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()

        return APIResponse.success(message=data["message"], data=data)


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
        serializer = SendEmailOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()

        return APIResponse.success(message="OTP sent", data=data)


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
