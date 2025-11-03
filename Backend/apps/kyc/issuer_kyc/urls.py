# from django.urls import path
# from .views import SendMobileOtpView,VerifyMobileOtpView,SendEmailOtpView,VerifyEmailOtpView,LoginRequestView,VerifyLoginOtpView
# app_name = 'authentication.issureauth'
# urlpatterns = [
#     path('send-mobile-otp/', SendMobileOtpView.as_view(), name='send-mobile-otp'),
#     path('verify-mobile-otp/',VerifyMobileOtpView.as_view(),name='verify-mobile-otp'),
#     path('send-email-otp/',SendEmailOtpView.as_view(),name='send-email-otp'),
#     path('verify-email-otp/',VerifyEmailOtpView.as_view(),name='verify-email-otp'),
#     path('login-request/',LoginRequestView.as_view(),name='login-request'),
#     path("verify-login-otp/", VerifyLoginOtpView.as_view(), name="verify-login-otp"),
# ]

from django.urls import path
from .views.CompanyInformationCreateView import CompanyInformationCreateView

app_name = 'kyc.issuer_kyc'

urlpatterns = [
    path('company-info/', CompanyInformationCreateView.as_view(), name='company-info-create'),
]
