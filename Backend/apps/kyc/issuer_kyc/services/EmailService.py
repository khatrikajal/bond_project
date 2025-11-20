# apps/authentication/services/EmailService.py

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:

    DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', 'kajalkhatri9373@gmail.com')

    # ----------------------------------------------------
    #  SUCCESS EMAIL (AUTO VERIFIED)
    # ----------------------------------------------------
    @staticmethod
    def send_registration_success_email(user, company):

        subject = "🎉 Registration Successful - Bond Platform"

        login_url = "http://93.127.206.37:3000/issuer/login"

        html_message = f"""
        <html><body style="font-family:Arial">
            <h2>Registration Successful</h2>
            <p>Dear {company.company_name},</p>
            <p>Your company registration has been <b>successfully completed.</b></p>

            <h3>Company Details</h3>
            <p><b>Company ID:</b> {company.company_id}</p>
            <p><b>CIN:</b> {company.corporate_identification_number}</p>
            <p><b>PAN:</b> {company.company_pan_number}</p>

            <br>
            <a href="{login_url}" 
               style="padding:10px 20px;background:#4CAF50;color:white;text-decoration:none">
               Login to Dashboard
            </a>

            <br><br>
            <p>Regards,<br>Bond Platform Team</p>
        </body></html>
        """

        plain_message = f"""
        Registration Successful

        Dear {company.company_name},

        Your registration has been successfully completed.

        Login here: {login_url}
        """

        return EmailService._send_html_email(subject, html_message, plain_message, user.email)

    # ----------------------------------------------------
    #  PENDING VERIFICATION EMAIL
    # ----------------------------------------------------
    @staticmethod
    def send_registration_pending_email(user, company):

        subject = "⏳ Registration Pending Verification - Bond Platform"

        html_message = f"""
        <html><body style="font-family:Arial">
            <h2>Registration Under Manual Review</h2>
            <p>Dear {company.company_name},</p>
            <p>Your registration is currently under manual verification.</p>

            <h3>Company Details</h3>
            <p><b>Company ID:</b> {company.company_id}</p>
            <p><b>CIN:</b> {company.corporate_identification_number}</p>
            <p><b>PAN:</b> {company.company_pan_number}</p>

            <p>Our team will notify you once verification is complete.</p>

            <br><br>
            <p>Regards,<br>Bond Platform Team</p>
        </body></html>
        """

        plain_message = f"""
        Registration Pending Verification

        Dear {company.company_name},

        Your registration is currently under manual review.
        """

        return EmailService._send_html_email(subject, html_message, plain_message, user.email)

    # ----------------------------------------------------
    #  VERIFICATION APPROVED EMAIL
    # ----------------------------------------------------
    @staticmethod
    def send_verification_approved_email(user, company):

        subject = "✅ Verification Approved - Bond Platform"

        login_url = "http://93.127.206.37:3000/issuer"

        html_message = f"""
        <html><body style="font-family:Arial">
            <h2>Verification Approved!</h2>
            <p>Dear {company.company_name},</p>
            <p>Your company verification is approved. You can now access your dashboard.</p>

            <a href="{login_url}" 
                style="padding:10px 20px;background:#4CAF50;color:white;text-decoration:none">
                Login Now
            </a>

            <br><br>
            <p>Regards,<br>Bond Platform Team</p>
        </body></html>
        """

        plain_message = f"""
        Verification Approved

        Dear {company.company_name},

        Your verification is approved. Login here:
        {login_url}
        """

        return EmailService._send_html_email(subject, html_message, plain_message, user.email)

    # ----------------------------------------------------
    #  VERIFICATION REJECTED EMAIL
    # ----------------------------------------------------
    @staticmethod
    def send_verification_rejected_email(user, company, reason=""):

        subject = "❌ Verification Rejected - Bond Platform"

        html_message = f"""
        <html><body style="font-family:Arial">
            <h2>Verification Rejected</h2>
            <p>Dear {company.company_name},</p>
            <p>Your verification request has been rejected.</p>

            {f"<p><b>Reason:</b> {reason}</p>" if reason else ""}

            <p>Please correct the issues and reapply.</p>

            <br><br>
            <p>Regards,<br>Bond Platform Team</p>
        </body></html>
        """

        plain_message = f"""
        Verification Rejected
        Reason: {reason}
        """

        return EmailService._send_html_email(subject, html_message, plain_message, user.email)

    # ----------------------------------------------------
    #  EMAIL OTP
    # ----------------------------------------------------
    @staticmethod
    def send_otp_email(email, otp, purpose="verification"):

        subject = f"🔐 Your OTP for {purpose.title()}"

        html_message = f"""
        <html><body style="font-family:Arial">
            <h2>Your OTP Code</h2>
            <p>Use this OTP to complete your {purpose}:</p>

            <div style="font-size:30px;font-weight:bold;
                        border:2px dashed #2196F3;padding:10px;width:150px;
                        text-align:center;">
                {otp}
            </div>

            <p>Valid for 10 minutes.</p>
        </body></html>
        """

        plain_message = f"Your OTP is {otp}"

        return EmailService._send_html_email(subject, html_message, plain_message, email)

    # ----------------------------------------------------
    #  INTERNAL EMAIL SENDER
    # ----------------------------------------------------
    @staticmethod
    def _send_html_email(subject, html_content, plain_content, recipient_email):

        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_content,
                from_email=EmailService.DEFAULT_FROM_EMAIL,
                to=[recipient_email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            logger.info(f"Email sent to {recipient_email}")
            return True

        except Exception as e:
            logger.error(f"Email send failed: {str(e)}")
            return False
