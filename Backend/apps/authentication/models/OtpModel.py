from django.db import models
from django.utils import timezone
from datetime import timedelta


class Otp(models.Model):
    OTP_TYPE = (
        ("MOBILE", "Mobile OTP"),
        ("EMAIL", "Email OTP"),
    )

    recipient = models.CharField(max_length=255)  # email or mobile number
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=10, choices=OTP_TYPE)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.expires_at

    @staticmethod
    def create_otp(recipient, code, otp_type):
        return Otp.objects.create(
            recipient=recipient,
            otp_code=code,
            otp_type=otp_type,
            expires_at=timezone.now() + timedelta(minutes=5)
        )
