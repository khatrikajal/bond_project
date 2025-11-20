class BaseOtpStrategy:
    """
    Base class for all OTP strategies.
    Production-grade and extensible.
    """

    def get_otp_override(self):
        """
        Default: no override.
        DummyStrategy overrides this only for development.
        """
        return None

    def send_otp(self, recipient, otp):
        """
        must be implemented by all child strategies.
        """
        raise NotImplementedError("send_otp() must be implemented in strategy.")
