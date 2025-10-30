# Backend/apps/authentication/otp_helpers.py
import logging
import random
import hashlib
from datetime import timedelta
from typing import Dict, Any, Optional

from django.core.cache import caches
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from .models import OTPRequest, OTPAttempt

# Use Twilio only when not in static mode
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

logger = logging.getLogger(__name__)

class OTPService:
    """
    Hybrid OTP service that uses Redis for OTP storage and PostgreSQL for audit logging.
    Easily switchable between static OTP (development) and Twilio (production).
    """
    
    def __init__(self):
        self.otp_cache = caches['otp']
        self.otp_settings = getattr(settings, 'OTP_SETTINGS', {})
        
        # OTP Configuration
        self.USE_STATIC_OTP = self.otp_settings.get('USE_STATIC_OTP', True)
        self.STATIC_OTP = self.otp_settings.get('STATIC_OTP', '00000')
        self.EXPIRY_TIME = self.otp_settings.get('EXPIRY_TIME', 600)  # 10 minutes
        self.RESEND_COOLDOWN = self.otp_settings.get('RESEND_COOLDOWN', 60)  # 1 minute
        self.MAX_ATTEMPTS = self.otp_settings.get('MAX_ATTEMPTS', 5)
        self.OTP_LENGTH = self.otp_settings.get('OTP_LENGTH', 5)
        
        # Twilio Configuration
        self.TWILIO_ACCOUNT_SID = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.TWILIO_AUTH_TOKEN = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.TWILIO_PHONE_NUMBER = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
        
        # Initialize Twilio client if not using static OTP
        if not self.USE_STATIC_OTP and TWILIO_AVAILABLE and all([
            self.TWILIO_ACCOUNT_SID, 
            self.TWILIO_AUTH_TOKEN, 
            self.TWILIO_PHONE_NUMBER
        ]):
            self.twilio_client = Client(self.TWILIO_ACCOUNT_SID, self.TWILIO_AUTH_TOKEN)
        else:
            self.twilio_client = None
    
    def _generate_cache_key(self, phone_number: str, purpose: str = 'default') -> str:
        """Generate cache key for OTP storage"""
        return f"otp:{purpose}:{phone_number}"
    
    def _generate_cooldown_key(self, phone_number: str, purpose: str = 'default') -> str:
        """Generate cache key for resend cooldown"""
        return f"otp_cooldown:{purpose}:{phone_number}"
    
    def _generate_otp(self) -> str:
        """Generate a random OTP code"""
        if self.USE_STATIC_OTP:
            return self.STATIC_OTP
        return f"{random.randint(0, 10**self.OTP_LENGTH - 1):0{self.OTP_LENGTH}d}"
    
    def _get_client_info(self, request=None) -> Dict[str, Any]:
        """Extract client information from request"""
        if not request:
            return {'ip_address': None, 'user_agent': None}
        
        # Handle proxy forwarding
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or \
                    request.META.get('REMOTE_ADDR', None)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        return {
            'ip_address': ip_address,
            'user_agent': user_agent[:500]  # Limit user agent length
        }
    
    def can_resend_otp(self, phone_number: str, purpose: str = 'default') -> Dict[str, Any]:
        """Check if OTP can be resent (cooldown period)"""
        cooldown_key = self._generate_cooldown_key(phone_number, purpose)
        cooldown_remaining = self.otp_cache.get(cooldown_key)
        
        if cooldown_remaining:
            return {
                'can_resend': False,
                'cooldown_remaining': cooldown_remaining,
                'message': f'Please wait {cooldown_remaining} seconds before requesting another OTP'
            }
        
        return {'can_resend': True}
    
    @transaction.atomic
    def send_otp(
        self, 
        phone_number: str, 
        purpose: str = 'registration',
        request=None
    ) -> Dict[str, Any]:
        """
        Send OTP to phone number with proper caching and database logging
        """
        try:
            # Check resend cooldown
            cooldown_check = self.can_resend_otp(phone_number, purpose)
            if not cooldown_check['can_resend']:
                return {
                    'success': False,
                    'error': cooldown_check['message'],
                    'cooldown_remaining': cooldown_check['cooldown_remaining']
                }
            
            # Generate OTP
            otp_code = self._generate_otp()
            cache_key = self._generate_cache_key(phone_number, purpose)
            cooldown_key = self._generate_cooldown_key(phone_number, purpose)
            
            # Get client info
            client_info = self._get_client_info(request)
            
            # Create OTP request record in database
            expires_at = timezone.now() + timedelta(seconds=self.EXPIRY_TIME)
            otp_request = OTPRequest.objects.create(
                phone_number=phone_number,
                purpose=purpose,
                expires_at=expires_at,
                **client_info
            )
            
            # Store OTP in cache with expiry
            cache_data = {
                'otp_code': otp_code,
                'request_id': str(otp_request.id),
                'phone_number': phone_number,
                'purpose': purpose,
                'created_at': timezone.now().isoformat(),
                'attempt_count': 0
            }
            
            self.otp_cache.set(cache_key, cache_data, timeout=self.EXPIRY_TIME)
            self.otp_cache.set(cooldown_key, self.RESEND_COOLDOWN, timeout=self.RESEND_COOLDOWN)
            
            # Send OTP via appropriate channel
            if self.USE_STATIC_OTP:
                logger.info(f"[Static OTP] Generated OTP {otp_code} for {phone_number}")
                return {
                    'success': True,
                    'message': 'OTP sent successfully',
                    'request_id': str(otp_request.id),
                    'static_otp': otp_code,  # Only for development
                    'expires_in': self.EXPIRY_TIME
                }
            
            else:
                # Send via Twilio
                if not self.twilio_client:
                    raise ValueError("Twilio client not properly configured")
                
                message = self.twilio_client.messages.create(
                    body=f"Your verification code is: {otp_code}",
                    from_=self.TWILIO_PHONE_NUMBER,
                    to=phone_number,
                )
                
                # Store Twilio SID for reference
                otp_request.external_reference = message.sid
                otp_request.save(update_fields=['external_reference'])
                
                logger.info(f"[Twilio] Sent OTP to {phone_number}. SID: {message.sid}")
                
                return {
                    'success': True,
                    'message': 'OTP sent successfully',
                    'request_id': str(otp_request.id),
                    'external_reference': message.sid,
                    'expires_in': self.EXPIRY_TIME
                }
                
        except Exception as e:
            logger.error(f"Error sending OTP to {phone_number}: {str(e)}")
            
            # Mark as failed in database if request was created
            if 'otp_request' in locals():
                otp_request.status = OTPRequest.StatusChoices.FAILED
                otp_request.save(update_fields=['status'])
            
            return {
                'success': False,
                'error': 'Failed to send OTP. Please try again.',
                'details': str(e) if settings.DEBUG else None
            }
    
    @transaction.atomic
    def verify_otp(
        self, 
        phone_number: str, 
        otp_code: str, 
        purpose: str = 'registration',
        request=None
    ) -> Dict[str, Any]:
        """
        Verify OTP with proper attempt tracking and security measures
        """
        cache_key = self._generate_cache_key(phone_number, purpose)
        client_info = self._get_client_info(request)
        
        try:
            # Get cached OTP data
            cached_data = self.otp_cache.get(cache_key)
            
            if not cached_data:
                return {
                    'success': False,
                    'error': 'OTP not found or expired. Please request a new one.'
                }
            
            # Get the OTP request from database
            try:
                otp_request = OTPRequest.objects.select_for_update().get(
                    id=cached_data['request_id'],
                    phone_number=phone_number,
                    purpose=purpose
                )
            except OTPRequest.DoesNotExist:
                # Clean up cache if DB record doesn't exist
                self.otp_cache.delete(cache_key)
                return {
                    'success': False,
                    'error': 'Invalid OTP request. Please request a new OTP.'
                }
            
            # Create attempt record
            attempt = OTPAttempt.objects.create(
                otp_request=otp_request,
                **client_info
            )
            
            # Check if OTP request is expired
            if otp_request.is_expired():
                otp_request.mark_as_expired()
                self.otp_cache.delete(cache_key)
                return {
                    'success': False,
                    'error': 'OTP has expired. Please request a new one.'
                }
            
            # Check attempt limit
            if cached_data['attempt_count'] >= self.MAX_ATTEMPTS:
                otp_request.status = OTPRequest.StatusChoices.FAILED
                otp_request.save(update_fields=['status'])
                self.otp_cache.delete(cache_key)
                return {
                    'success': False,
                    'error': 'Maximum verification attempts exceeded. Please request a new OTP.'
                }
            
            # Verify OTP
            is_valid = cached_data['otp_code'] == otp_code
            
            if is_valid:
                # Mark as successful
                attempt.is_successful = True
                attempt.save(update_fields=['is_successful'])
                
                otp_request.mark_as_verified()
                
                # Clean up cache
                self.otp_cache.delete(cache_key)
                self.otp_cache.delete(self._generate_cooldown_key(phone_number, purpose))
                
                logger.info(f"[OTP Verified] {phone_number} - {purpose}")
                
                return {
                    'success': True,
                    'message': 'OTP verified successfully',
                    'request_id': str(otp_request.id)
                }
            else:
                # Increment attempt count in cache
                cached_data['attempt_count'] += 1
                self.otp_cache.set(cache_key, cached_data, timeout=self.EXPIRY_TIME)
                
                otp_request.increment_attempt()
                
                remaining_attempts = self.MAX_ATTEMPTS - cached_data['attempt_count']
                
                return {
                    'success': False,
                    'error': 'Invalid OTP code',
                    'remaining_attempts': remaining_attempts
                }
                
        except Exception as e:
            logger.error(f"Error verifying OTP for {phone_number}: {str(e)}")
            return {
                'success': False,
                'error': 'OTP verification failed. Please try again.',
                'details': str(e) if settings.DEBUG else None
            }
    
    def cleanup_expired_requests(self):
        """
        Cleanup expired OTP requests from database
        This should be called periodically via Celery task
        """
        try:
            expired_count = OTPRequest.objects.filter(
                expires_at__lt=timezone.now(),
                status=OTPRequest.StatusChoices.SENT
            ).update(status=OTPRequest.StatusChoices.EXPIRED)
            
            logger.info(f"Marked {expired_count} OTP requests as expired")
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired OTP requests: {str(e)}")
            return 0
    
    def get_otp_statistics(self, phone_number: str = None, days: int = 7) -> Dict[str, Any]:
        """
        Get OTP usage statistics for monitoring and analytics
        """
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        
        queryset = OTPRequest.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=days)
        )
        
        if phone_number:
            queryset = queryset.filter(phone_number=phone_number)
        
        stats = queryset.aggregate(
            total_requests=Count('id'),
            verified_count=Count('id', filter=Q(status=OTPRequest.StatusChoices.VERIFIED)),
            expired_count=Count('id', filter=Q(status=OTPRequest.StatusChoices.EXPIRED)),
            failed_count=Count('id', filter=Q(status=OTPRequest.StatusChoices.FAILED)),
        )
        
        # Calculate success rate
        total = stats['total_requests'] or 1
        stats['success_rate'] = (stats['verified_count'] / total) * 100
        
        return stats