# apps/authentication/services/otp/strategies/email/gmail.py
from ...strategies.base import BaseOtpStrategy

class GmailOtpStrategy(BaseOtpStrategy):

    def send_otp(self, email, otp):
        # integrate with email provider or SMTP here
        print(f"[GMAIL OTP] sending {otp} to {email}")
