from celery import shared_task


@shared_task
def send_mobile_otp_task(mobile, ttl):
    from apps.authentication.services.otp.otp_service import OtpService
    OtpService._send_mobile_otp_internal(mobile, ttl)


@shared_task
def send_email_otp_task(email, ttl):
    from apps.authentication.services.otp.otp_service import OtpService
    return OtpService._send_email_otp_internal(email, ttl)


@shared_task
def cleanup_expired_otps():
    from apps.authentication.models import Otp
    from django.utils import timezone

    deleted, _ = Otp.objects.filter(expires_at__lt=timezone.now()).delete()
    return f"Deleted {deleted} expired OTPs"
