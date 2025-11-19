# apps/authentication/services/EmailService.py

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Centralized Email Service for Bond Platform
    Handles all email sending operations with templates and logging
    """
    
    DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', 'kajalkhatri9373@gmail.com')
    
    @staticmethod
    def send_registration_success_email(user, company):
        """
        Send email when registration is auto-verified (SUCCESS)
        
        Args:
            user: User instance
            company: CompanyInformation instance
        """
        subject = "🎉 Registration Successful - Bond Platform"
        
        context = {
            'company_name': company.company_name,
            'user_email': user.email,
            'user_mobile': user.mobile_number,
            'cin': company.corporate_identification_number,
            'pan': company.company_pan_number,
            'sector': company.get_sector_display(),
            'entity_type': company.get_entity_type_display(),
            'company_id': str(company.company_id),
        }
        
        # HTML email template
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 5px; margin-top: 20px; }}
                .details {{ background-color: white; padding: 15px; border-left: 4px solid #4CAF50; margin: 20px 0; }}
                .details-row {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
                .details-row:last-child {{ border-bottom: none; }}
                .label {{ font-weight: bold; color: #555; }}
                .footer {{ text-align: center; margin-top: 30px; color: #777; font-size: 12px; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #4CAF50; 
                          color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Registration Successful!</h1>
                </div>
                
                <div class="content">
                    <h2>Dear {context['company_name']},</h2>
                    
                    <p>Congratulations! Your registration with the <strong>Bond Platform</strong> has been successfully completed and verified.</p>
                    
                    <div class="details">
                        <h3>Company Details</h3>
                        <div class="details-row">
                            <span class="label">Company ID:</span> {context['company_id']}
                        </div>
                        <div class="details-row">
                            <span class="label">CIN:</span> {context['cin']}
                        </div>
                        <div class="details-row">
                            <span class="label">PAN:</span> {context['pan']}
                        </div>
                        <div class="details-row">
                            <span class="label">Entity Type:</span> {context['entity_type']}
                        </div>
                        <div class="details-row">
                            <span class="label">Sector:</span> {context['sector']}
                        </div>
                    </div>
                    
                    <div class="details">
                        <h3>Login Credentials</h3>
                        <div class="details-row">
                            <span class="label">Email:</span> {context['user_email']}
                        </div>
                        <div class="details-row">
                            <span class="label">Mobile:</span> {context['user_mobile']}
                        </div>
                    </div>
                    
                    <p><strong>You can now log in and start using the Bond Platform!</strong></p>
                    
                    <center>
                        <a href="{settings.FRONTEND_URL}/login" class="button">Login to Dashboard</a>
                    </center>
                    
                    <p style="margin-top: 30px; color: #666;">
                        If you have any questions or need assistance, please don't hesitate to contact our support team.
                    </p>
                </div>
                
                <div class="footer">
                    <p>© 2024 Bond Platform. All rights reserved.</p>
                    <p>This is an automated email. Please do not reply to this message.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        plain_message = f"""
        Registration Successful - Bond Platform
        
        Dear {context['company_name']},
        
        Congratulations! Your registration has been successfully completed and verified.
        
        Company Details:
        - Company ID: {context['company_id']}
        - CIN: {context['cin']}
        - PAN: {context['pan']}
        - Entity Type: {context['entity_type']}
        - Sector: {context['sector']}
        
        Login Credentials:
        - Email: {context['user_email']}
        - Mobile: {context['user_mobile']}
        
        You can now log in and start using the Bond Platform.
        
        Best regards,
        Bond Platform Team
        """
        
        return EmailService._send_html_email(
            subject=subject,
            html_content=html_message,
            plain_content=plain_message,
            recipient_email=user.email
        )
    
    @staticmethod
    def send_registration_pending_email(user, company):
        """
        Send email when registration requires manual verification (PENDING)
        
        Args:
            user: User instance
            company: CompanyInformation instance
        """
        subject = "⏳ Registration Pending Verification - Bond Platform"
        
        context = {
            'company_name': company.company_name,
            'user_email': user.email,
            'cin': company.corporate_identification_number,
            'pan': company.company_pan_number,
            'company_id': str(company.company_id),
        }
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #FF9800; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 5px; margin-top: 20px; }}
                .details {{ background-color: white; padding: 15px; border-left: 4px solid #FF9800; margin: 20px 0; }}
                .details-row {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
                .details-row:last-child {{ border-bottom: none; }}
                .label {{ font-weight: bold; color: #555; }}
                .info-box {{ background-color: #FFF3E0; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #777; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⏳ Registration Pending Verification</h1>
                </div>
                
                <div class="content">
                    <h2>Dear {context['company_name']},</h2>
                    
                    <p>Thank you for registering with the <strong>Bond Platform</strong>.</p>
                    
                    <div class="info-box">
                        <strong>📋 Status:</strong> Your registration is currently under manual review by our team.
                    </div>
                    
                    <p>Our verification team will carefully review your details and notify you once the verification is complete.</p>
                    
                    <div class="details">
                        <h3>Submitted Company Details</h3>
                        <div class="details-row">
                            <span class="label">Company ID:</span> {context['company_id']}
                        </div>
                        <div class="details-row">
                            <span class="label">CIN:</span> {context['cin']}
                        </div>
                        <div class="details-row">
                            <span class="label">PAN:</span> {context['pan']}
                        </div>
                        <div class="details-row">
                            <span class="label">Email:</span> {context['user_email']}
                        </div>
                    </div>
                    
                    <div class="info-box">
                        <strong>⏱️ Timeline:</strong> Verification typically takes 1-2 business days.
                    </div>
                    
                    <p><strong>What happens next?</strong></p>
                    <ul>
                        <li>Our team will verify your company documents</li>
                        <li>You'll receive an email once verification is complete</li>
                        <li>Upon approval, you can log in and start using the platform</li>
                    </ul>
                    
                    <p style="margin-top: 30px; color: #666;">
                        If you have any questions, please contact our support team at support@bondplatform.com
                    </p>
                </div>
                
                <div class="footer">
                    <p>© 2024 Bond Platform. All rights reserved.</p>
                    <p>This is an automated email. Please do not reply to this message.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        Registration Pending Verification - Bond Platform
        
        Dear {context['company_name']},
        
        Thank you for registering with the Bond Platform.
        
        Status: Your registration is currently under manual review.
        
        Submitted Company Details:
        - Company ID: {context['company_id']}
        - CIN: {context['cin']}
        - PAN: {context['pan']}
        - Email: {context['user_email']}
        
        Timeline: Verification typically takes 1-2 business days.
        
        What happens next?
        - Our team will verify your company documents
        - You'll receive an email once verification is complete
        - Upon approval, you can log in and start using the platform
        
        If you have questions, contact: support@bondplatform.com
        
        Best regards,
        Bond Platform Team
        """
        
        return EmailService._send_html_email(
            subject=subject,
            html_content=html_message,
            plain_content=plain_message,
            recipient_email=user.email
        )
    
    @staticmethod
    def send_verification_approved_email(user, company):
        """
        Send email when manual verification is approved
        
        Args:
            user: User instance
            company: CompanyInformation instance
        """
        subject = "✅ Verification Approved - Bond Platform"
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 5px; margin-top: 20px; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #4CAF50; 
                          color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #777; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Verification Approved!</h1>
                </div>
                
                <div class="content">
                    <h2>Dear {company.company_name},</h2>
                    
                    <p>Great news! Your company verification has been <strong>approved</strong>.</p>
                    
                    <p>You can now access all features of the Bond Platform and start managing your bonds.</p>
                    
                    <center>
                        <a href="{settings.FRONTEND_URL}/login" class="button">Login to Dashboard</a>
                    </center>
                    
                    <p style="margin-top: 30px;">
                        Welcome aboard! If you need any assistance, our support team is here to help.
                    </p>
                </div>
                
                <div class="footer">
                    <p>© 2024 Bond Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        Verification Approved - Bond Platform
        
        Dear {company.company_name},
        
        Great news! Your company verification has been approved.
        
        You can now log in and access all features of the Bond Platform.
        
        Login at: {settings.FRONTEND_URL}/login
        
        Welcome aboard!
        
        Best regards,
        Bond Platform Team
        """
        
        return EmailService._send_html_email(
            subject=subject,
            html_content=html_message,
            plain_content=plain_message,
            recipient_email=user.email
        )
    
    @staticmethod
    def send_verification_rejected_email(user, company, reason=""):
        """
        Send email when manual verification is rejected
        
        Args:
            user: User instance
            company: CompanyInformation instance
            reason: Reason for rejection
        """
        subject = "❌ Verification Rejected - Bond Platform"
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #F44336; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 5px; margin-top: 20px; }}
                .reason-box {{ background-color: #FFEBEE; padding: 15px; border-left: 4px solid #F44336; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #777; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Verification Rejected</h1>
                </div>
                
                <div class="content">
                    <h2>Dear {company.company_name},</h2>
                    
                    <p>We regret to inform you that your company verification could not be approved at this time.</p>
                    
                    {f'<div class="reason-box"><strong>Reason:</strong> {reason}</div>' if reason else ''}
                    
                    <p><strong>Next Steps:</strong></p>
                    <ul>
                        <li>Review the reason for rejection above</li>
                        <li>Prepare the necessary corrections or documents</li>
                        <li>Contact our support team for guidance</li>
                        <li>Resubmit your application with correct information</li>
                    </ul>
                    
                    <p>For assistance, please contact: <strong>support@bondplatform.com</strong></p>
                </div>
                
                <div class="footer">
                    <p>© 2024 Bond Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        Verification Rejected - Bond Platform
        
        Dear {company.company_name},
        
        We regret to inform you that your company verification could not be approved.
        
        {f'Reason: {reason}' if reason else ''}
        
        Next Steps:
        - Review the reason for rejection
        - Prepare necessary corrections
        - Contact support@bondplatform.com for guidance
        - Resubmit your application
        
        Best regards,
        Bond Platform Team
        """
        
        return EmailService._send_html_email(
            subject=subject,
            html_content=html_message,
            plain_content=plain_message,
            recipient_email=user.email
        )
    
    @staticmethod
    def send_otp_email(email, otp, purpose="verification"):
        """
        Send OTP for email verification
        
        Args:
            email: Recipient email
            otp: OTP code
            purpose: Purpose of OTP (verification/password_reset)
        """
        subject = f"🔐 Your OTP for {purpose.replace('_', ' ').title()}"
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 5px; margin-top: 20px; }}
                .otp-box {{ background-color: white; padding: 20px; text-align: center; 
                           font-size: 32px; font-weight: bold; letter-spacing: 8px; 
                           border: 2px dashed #2196F3; border-radius: 5px; margin: 20px 0; }}
                .warning {{ background-color: #FFF3E0; padding: 15px; border-radius: 5px; 
                           margin-top: 20px; color: #E65100; }}
                .footer {{ text-align: center; margin-top: 30px; color: #777; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 OTP Verification</h1>
                </div>
                
                <div class="content">
                    <p>Hello,</p>
                    
                    <p>Your One-Time Password (OTP) for <strong>{purpose.replace('_', ' ')}</strong> is:</p>
                    
                    <div class="otp-box">
                        {otp}
                    </div>
                    
                    <p style="text-align: center; color: #666;">
                        This OTP is valid for <strong>10 minutes</strong>
                    </p>
                    
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong><br>
                        • Do not share this OTP with anyone<br>
                        • Bond Platform will never ask for your OTP via phone or email<br>
                        • If you didn't request this OTP, please ignore this email
                    </div>
                </div>
                
                <div class="footer">
                    <p>© 2024 Bond Platform. All rights reserved.</p>
                    <p>This is an automated email. Please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        OTP Verification - Bond Platform
        
        Your One-Time Password (OTP) is: {otp}
        
        This OTP is valid for 10 minutes.
        
        Security Notice:
        - Do not share this OTP with anyone
        - If you didn't request this, ignore this email
        
        Bond Platform Team
        """
        
        return EmailService._send_html_email(
            subject=subject,
            html_content=html_message,
            plain_content=plain_message,
            recipient_email=email
        )
    
    @staticmethod
    def _send_html_email(subject, html_content, plain_content, recipient_email):
        """
        Internal method to send HTML email with plain text fallback
        
        Args:
            subject: Email subject
            html_content: HTML version of email
            plain_content: Plain text version
            recipient_email: Recipient email address
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_content,
                from_email=EmailService.DEFAULT_FROM_EMAIL,
                to=[recipient_email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"Email sent successfully to {recipient_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            return False
    
    @staticmethod
    def send_simple_email(subject, message, recipient_email):
        """
        Send a simple plain text email
        
        Args:
            subject: Email subject
            message: Email body
            recipient_email: Recipient email
            
        Returns:
            bool: True if sent successfully
        """
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=EmailService.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False
            )
            logger.info(f"Simple email sent to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send simple email: {str(e)}")
            return False