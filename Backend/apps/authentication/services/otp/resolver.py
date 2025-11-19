from django.conf import settings
from .registry import OtpStrategyRegistry


class OtpStrategyResolver:

    @staticmethod
    def resolve_for_mobile():
        strategy_name = getattr(settings, "OTP_MOBILE_STRATEGY", "dummy")
        return OtpStrategyRegistry.get_strategy(strategy_name)

    @staticmethod
    def resolve_for_email():
        strategy_name = getattr(settings, "OTP_EMAIL_STRATEGY", "dummy")
        return OtpStrategyRegistry.get_strategy(strategy_name)
