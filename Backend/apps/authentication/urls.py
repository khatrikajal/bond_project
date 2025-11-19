# Backend/apps/authentication/urls.py
from django.urls import path,include


from .views.OtpViews import (
    SendMobileOtpView,
    VerifyMobileOtpView,
    SendEmailOtpView,
    VerifyEmailOtpView,
)


app_name = 'authentication'

urlpatterns = [
    # OTP endpoints
    path("send-mobile-otp/", SendMobileOtpView.as_view(), name="send_mobile_otp"),
    path("verify-mobile-otp/", VerifyMobileOtpView.as_view(), name="verify_mobile_otp"),
    path("send-email-otp/", SendEmailOtpView.as_view(), name="send_email_otp"),
    path("verify-email-otp/", VerifyEmailOtpView.as_view(), name="verify_email_otp"),


    # path('v1/',include('apps.authentication.issureauth.urls',namespace='issureauth')),
   
]