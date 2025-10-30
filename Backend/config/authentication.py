from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        """
        Authenticate the user based on either a JWT token in the Authorization header
        (Bearer token) or in the cookies.
        If a Bearer token is present, that will be used otherwise, the cookie
        is checked.
        Returns a two-tuple of `User` and token if valid, otherwise raises an exception.
        """
        auth_header = self.get_header(request)
        if auth_header:
            return super().authenticate(request)
        raw_token = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE"], None)
        if not raw_token:
            return None  # No token provided, authentication skipped.

        try:
            validated_token = self.get_validated_token(raw_token)
        except TokenError:
            self._raise_authentication_error("Invalid or expired token.")

        return self.get_user(validated_token), validated_token

    def _raise_authentication_error(self, message):
        """
        Raises an AuthenticationFailed exception with the provided message.
        """
        raise AuthenticationFailed(detail=message)
