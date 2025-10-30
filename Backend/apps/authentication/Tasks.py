# Backend/apps/authentication/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from .otp_helpers import OTPService
from .models import OTPRequest, OTPAttempt

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def cleanup_expired_otp_requests(self):
    """
    Periodic task to cleanup expired OTP requests
    Should be run every 15-30 minutes
    """
    try:
        otp_service = OTPService()
        expired_count = otp_service.cleanup_expired_requests()
        
        logger.info(f"Cleaned up {expired_count} expired OTP requests")
        return {"status": "success", "cleaned_up": expired_count}
        
    except Exception as e:
        logger.error(f"Error in cleanup_expired_otp_requests task: {str(e)}")
        
        # Retry with exponential backoff
        retry_in = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
        raise self.retry(countdown=retry_in, exc=e)


@shared_task(bind=True, max_retries=3)
def cleanup_old_otp_records(self, days_old=30):
    """
    Task to cleanup old OTP records from database
    Should be run daily or weekly
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        # Delete old OTP attempts first (foreign key constraint)
        deleted_attempts = OTPAttempt.objects.filter(
            attempted_at__lt=cutoff_date
        ).count()
        
        OTPAttempt.objects.filter(attempted_at__lt=cutoff_date).delete()
        
        # Delete old OTP requests
        deleted_requests = OTPRequest.objects.filter(
            created_at__lt=cutoff_date
        ).count()
        
        OTPRequest.objects.filter(created_at__lt=cutoff_date).delete()
        
        logger.info(f"Cleaned up {deleted_requests} old OTP requests and {deleted_attempts} attempts")
        
        return {
            "status": "success", 
            "deleted_requests": deleted_requests,
            "deleted_attempts": deleted_attempts
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_otp_records task: {str(e)}")
        
        # Retry with exponential backoff
        retry_in = 60 * (2 ** self.request.retries)
        raise self.retry(countdown=retry_in, exc=e)


@shared_task(bind=True)
def generate_otp_analytics_report(self, days=7):
    """
    Generate OTP analytics report for monitoring
    Should be run daily
    """
    try:
        otp_service = OTPService()
        stats = otp_service.get_otp_statistics(days=days)
        
        # Log important metrics
        logger.info(f"OTP Analytics ({days} days): "
                   f"Total: {stats['total_requests']}, "
                   f"Success Rate: {stats['success_rate']:.1f}%, "
                   f"Verified: {stats['verified_count']}, "
                   f"Failed: {stats['failed_count']}, "
                   f"Expired: {stats['expired_count']}")
        
        # You can extend this to send to monitoring services like DataDog, NewRelic, etc.
        # or store in a separate analytics table
        
        return {"status": "success", "analytics": stats}
        
    except Exception as e:
        logger.error(f"Error in generate_otp_analytics_report task: {str(e)}")
        return {"status": "error", "error": str(e)}


@shared_task(bind=True, max_retries=2)
def send_otp_async(self, phone_number, purpose='registration', **kwargs):
    """
    Async task for sending OTP (for heavy operations or external API calls)
    Currently not used but can be useful for Twilio integration
    """
    try:
        otp_service = OTPService()
        result = otp_service.send_otp(phone_number, purpose)
        
        if result['success']:
            logger.info(f"Async OTP sent successfully to {phone_number}")
            return {"status": "success", "request_id": result.get('request_id')}
        else:
            logger.error(f"Async OTP send failed for {phone_number}: {result['error']}")
            return {"status": "failed", "error": result['error']}
            
    except Exception as e:
        logger.error(f"Error in send_otp_async task: {str(e)}")
        
        # Retry with delay
        raise self.retry(countdown=30, exc=e)