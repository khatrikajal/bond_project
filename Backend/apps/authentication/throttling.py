# apps/authentication/throttling.py
from ipaddress import ip_address, ip_network
from rest_framework.throttling import SimpleRateThrottle
from django.conf import settings


class OtpThrottle(SimpleRateThrottle):
    """
    Throttle OTP requests by recipient (mobile_number or email).
    Falls back to IP when recipient not provided.
    Can be customized per-view by setting `throttle_scope` or `otp_throttle_scope`.
    """

    # default scope name to pick rate from REST_FRAMEWORK.DEFAULT_THROTTLE_RATES
    scope = "otp"

    # optional: list of CIDR networks to ALWAYS allow (internal/test IPs)
    INTERNAL_ALLOWLIST = getattr(settings, "OTP_THROTTLE_INTERNAL_ALLOWLIST", [])

    def get_recipient_from_request(self, request):
        # prefer mobile_number, else email
        return request.data.get("mobile_number") or request.data.get("email")

    def is_internal_ip(self, request):
        # optional bypass for internal IPs
        try:
            client_ip = request.META.get("REMOTE_ADDR")
            if not client_ip:
                return False
            ip = ip_address(client_ip)
            for net in self.INTERNAL_ALLOWLIST:
                if ip in ip_network(net):
                    return True
        except Exception:
            return False
        return False

    def get_cache_key(self, request, view):
        # bypass throttle for staff
        user = getattr(request, "user", None)
        if getattr(user, "is_staff", False) or self.is_internal_ip(request):
            return None

        recipient = self.get_recipient_from_request(request)
        if recipient:
            # normalize recipient (lowercase email, strip spaces)
            key = recipient.strip().lower()
            return f"throttle_otp_{self.scope}_{key}"

        # fallback to IP address (still better than no throttle)
        ip = request.META.get("REMOTE_ADDR")
        if not ip:
            return None
        return f"throttle_otp_{self.scope}_ip_{ip}"
