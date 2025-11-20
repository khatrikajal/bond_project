# apps/authentication/services/verification_store.py

from django.conf import settings
from django.core.cache import caches


class VerificationStore:

    BACKEND = getattr(settings, "OTP_VERIFICATION_BACKEND", "cache")
    TTL = 900  # 15 minutes

    @staticmethod
    def _mobile_key(mobile):
        return f"otp:mobile:{mobile}:verified"

    @staticmethod
    def _email_key(email):
        return f"otp:email:{email}:verified"

    @staticmethod
    def _get_cache():
        """
        Returns the correct cache backend.
        - redis cache → `caches["otp"]`
        - local cache → `caches["default"]`
        """
        if VerificationStore.BACKEND == "redis":
            return caches["otp"]
        return caches["default"]

    # ------------------------------
    #         SET VERIFIED
    # ------------------------------
    @classmethod
    def set_mobile_verified(cls, request, mobile):
        if cls.BACKEND == "session":
            request.session["mobile_verified"] = True
            request.session.modified = True
            return

        cache = cls._get_cache()
        key = cls._mobile_key(mobile)
        cache.set(key, True, timeout=cls.TTL)

    @classmethod
    def set_email_verified(cls, request, email):
        if cls.BACKEND == "session":
            request.session["email_verified"] = True
            request.session.modified = True
            return

        cache = cls._get_cache()
        key = cls._email_key(email)
        cache.set(key, True, timeout=cls.TTL)

    # ------------------------------
    #         CHECK VERIFIED
    # ------------------------------
    @classmethod
    def is_mobile_verified(cls, request, mobile):
        if cls.BACKEND == "session":
            return request.session.get("mobile_verified", False)

        cache = cls._get_cache()
        key = cls._mobile_key(mobile)
        return cache.get(key, False)

    @classmethod
    def is_email_verified(cls, request, email):
        if cls.BACKEND == "session":
            return request.session.get("email_verified", False)

        cache = cls._get_cache()
        key = cls._email_key(email)
        return cache.get(key, False)
