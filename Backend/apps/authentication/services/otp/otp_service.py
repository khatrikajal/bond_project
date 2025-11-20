# apps/authentication/services/otp/otp_service.py
import random
import logging
from django.utils import timezone
from django.conf import settings
from ...models.OtpModel import Otp
from .resolver import OtpStrategyResolver

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class OtpService:

    @staticmethod
    def _generate_otp():
        return str(random.randint(100000, 999999))

    # INTERNAL (used by Celery OR direct)
    @classmethod
    def _send_mobile_otp_internal(cls, mobile, ttl):
        strategy = OtpStrategyResolver.resolve_for_mobile()
        
        override = strategy.get_otp_override()
        otp = override if override is not None else cls._generate_otp()

        Otp.create_otp(mobile, otp, "MOBILE", ttl)
        strategy.send_otp(mobile, otp)

        logger.info(f"[OTP-MOBILE] OTP sent to {mobile} (override={override})")


    @classmethod
    def _send_email_otp_internal(cls, email, ttl):
        strategy = OtpStrategyResolver.resolve_for_email()

        override = strategy.get_otp_override()
        otp = override if override is not None else cls._generate_otp()

        Otp.create_otp(email, otp, "EMAIL", ttl)
        strategy.send_otp(email, otp)

        logger.info(f"[OTP-EMAIL] OTP sent to {email} (override={override})")


    # PUBLIC API (used by serializers/views)
    @classmethod
    def send_mobile_otp(cls, mobile, ttl_minutes=5):
        if getattr(settings, "USE_CELERY_FOR_OTP", False):
            from apps.authentication.tasks import send_mobile_otp_task
            send_mobile_otp_task.delay(mobile, ttl_minutes)
        else:
            cls._send_mobile_otp_internal(mobile, ttl_minutes)

        return True

    @classmethod
    def send_email_otp(cls, email, ttl_minutes=5):
        if getattr(settings, "USE_CELERY_FOR_OTP", False):
            from apps.authentication.tasks import send_email_otp_task
            send_email_otp_task.delay(email, ttl_minutes)
        else:
            cls._send_email_otp_internal(email, ttl_minutes)

        return True

    @staticmethod
    def verify_otp(recipient: str, otp: str, otp_type: str):
        # match the exact OTP user entered
        record = (
            Otp.objects.filter(
                recipient=recipient,
                otp_code=otp,
                otp_type=otp_type,
                is_used=False,
                expires_at__gte=timezone.now()   # <--- Very important
            )
            .order_by("-created_at")
            .first()
        )

       


        if not record:
            return False, "Invalid OTP"

        if record.is_expired():
            return False, "OTP expired"

        record.is_used = True
        record.save(update_fields=["is_used"])

        return True, "OTP verified"

