# apps/authentication/services/otp/otp_service.py
import random
import logging
from django.utils import timezone

from ...models.OtpModel import Otp
from .resolver import OtpStrategyResolver

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class OtpService:

    @staticmethod
    def _generate_otp():
        # 6-digit numeric OTP
        return str(random.randint(100000, 999999))

    @classmethod
    def send_mobile_otp(cls, mobile: str, ttl_minutes: int = 5):
        strategy = OtpStrategyResolver.resolve_for_mobile()
        override = strategy.get_otp_override()
        otp = override if override is not None else cls._generate_otp()

        # persist in DB
        Otp.create_otp(mobile, otp, "MOBILE", ttl_minutes)

        # send using strategy
        strategy.send_otp(mobile, otp)

        logger.info(f"[OTP-MOBILE] sent to {mobile} using {strategy.__class__.__name__}")
        return True

    @classmethod
    def send_email_otp(cls, email: str, ttl_minutes: int = 5):
        strategy = OtpStrategyResolver.resolve_for_email()
        override = strategy.get_otp_override()
        otp = override if override is not None else cls._generate_otp()

        Otp.create_otp(email, otp, "EMAIL", ttl_minutes)
        strategy.send_otp(email, otp)

        logger.info(f"[OTP-EMAIL] sent to {email} using {strategy.__class__.__name__}")
        return True

    @staticmethod
    def verify_otp(recipient: str, otp: str, otp_type: str):
        # latest unused matching OTP
        try:
            record = Otp.objects.filter(
                recipient=recipient,
                otp_code=otp,
                otp_type=otp_type,
                is_used=False
            ).latest("created_at")
        except Otp.DoesNotExist:
            return False, "Invalid OTP"

        if record.is_expired():
            return False, "OTP expired"

        # mark used
        record.is_used = True
        record.save(update_fields=["is_used"])

        return True, "OTP verified"
