# Backend/apps/authentication/urls.py
from django.urls import path,include
# from .views import (
#     SendOTPAPIView, 
#     VerifyOTPAPIView, 
#     ResendOTPAPIView,
#     OTPStatusAPIView,
   
    

# )




app_name = 'authentication'

urlpatterns = [
    # OTP endpoints
    # path("otp/send/", SendOTPAPIView.as_view(), name="send-otp"),
    # path("otp/verify/", VerifyOTPAPIView.as_view(), name="verify-otp"),
    # path("otp/resend/", ResendOTPAPIView.as_view(), name="resend-otp"),
    # path("otp/status/", OTPStatusAPIView.as_view(), name="otp-status"),
    path('v1/',include('apps.authentication.issureauth.urls',namespace='issureauth')),
   
]