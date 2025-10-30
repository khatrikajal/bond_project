from django.core.cache import cache  # noqa: I001
from rest_framework.request import Request
from typing import Union
from rest_framework.throttling import AnonRateThrottle
from rest_framework.throttling import (
    BaseThrottle,
    SimpleRateThrottle,
)


class OpenAPIsThrottle(SimpleRateThrottle):
    scope = "open_apis"

    def get_cache_key(self, request: Request, view) -> Union[str, None]:  # noqa: UP007
        """
        It returns the cache key for the OpenAPIsThrottle.
        The cache key is used to identify the throttle rate for the view.
        """
        return self.get_ident(request)


class OTPThrottle(AnonRateThrottle):
    """
    This throttle class is used to limit the OTP request
    rate for the registration
    OTP view. The rate is limited to 5 requests per hour.
    """
    scope = "registration_otp"

    def allow_request(self, request, view):
        if request.method != "POST": # work only in Post method
            return True
        return super().allow_request(request, view)


class RegistrationOTPThrottle(BaseThrottle):
    """
    This throttle class is used to limit the OTP request
      rate for the registration
    OTP view. The rate is limited to 5 requests per hour.
    """

    def allow_request(self, request, view):
        """
        This method checks if the request is allowed based on the
          throttle rate.
        """
        if request.method != "POST":
            return True

        to = request.data.get("to")

        if not to:
            return False

        cache_key = f"registration_otp_throttle_{to}"
        num_requests = cache.get(cache_key, 0)

        if num_requests >= 5:  # noqa: PLR2004
            return False  # Block the request if limit exceeded

        cache.set(cache_key, num_requests + 1, timeout=3600)  # 1 hour timeout
        return True

    def wait(self):
        """
        This method is not implemented for this throttle class.
        """
        return 5 * 60 # Return a default wait time of 5 minutes
