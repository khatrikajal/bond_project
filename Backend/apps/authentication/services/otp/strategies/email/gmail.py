from ..base import BaseOtpStrategy

class DummyOtpStrategy(BaseOtpStrategy):

    def get_otp_override(self):
        return "1111"  # ONLY for dev mode

    def send_otp(self, recipient, otp):
        print(f"[DUMMY OTP] Sending OTP {otp} to {recipient}")
