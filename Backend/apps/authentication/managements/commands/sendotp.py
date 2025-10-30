# Backend/apps/authentication/management/commands/sendotp.py
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from phonenumber_field.phonenumber import PhoneNumber
from apps.authentication.otp_helpers import OTPService
from apps.authentication.models import OTPRequest


class Command(BaseCommand):
    help = "OTP management commands - send, verify, cleanup, and analytics"

    def add_arguments(self, parser):
        # Subcommands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Send OTP command
        send_parser = subparsers.add_parser('send', help='Send OTP to phone number')
        send_parser.add_argument('phone_number', type=str, help='Phone number with country code')
        send_parser.add_argument('--purpose', type=str, default='registration', 
                               choices=['registration', 'login', 'password_reset', 'phone_verification'],
                               help='Purpose of OTP')
        send_parser.add_argument('--otp', type=str, help='Custom OTP code (development only)')
        
        # Verify OTP command  
        verify_parser = subparsers.add_parser('verify', help='Verify OTP code')
        verify_parser.add_argument('phone_number', type=str, help='Phone number with country code')
        verify_parser.add_argument('otp_code', type=str, help='OTP code to verify')
        verify_parser.add_argument('--purpose', type=str, default='registration',
                                 choices=['registration', 'login', 'password_reset', 'phone_verification'],
                                 help='Purpose of OTP')
        
        # Cleanup command
        cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup expired OTP requests')
        cleanup_parser.add_argument('--days', type=int, default=30, 
                                  help='Delete records older than this many days')
        cleanup_parser.add_argument('--dry-run', action='store_true',
                                  help='Show what would be deleted without actually deleting')
        
        # Analytics command
        analytics_parser = subparsers.add_parser('analytics', help='Show OTP analytics')
        analytics_parser.add_argument('--days', type=int, default=7,
                                    help='Number of days to analyze')
        analytics_parser.add_argument('--phone', type=str, help='Filter by phone number')
        
        # Status command
        status_parser = subparsers.add_parser('status', help='Check OTP status for phone number')
        status_parser.add_argument('phone_number', type=str, help='Phone number to check')
        status_parser.add_argument('--purpose', type=str, default='registration')

    def handle(self, *args, **options):
        command = options.get('command')
        
        if not command:
            self.stdout.write(self.style.ERROR('Please specify a command: send, verify, cleanup, analytics, or status'))
            return
        
        # Initialize OTP service
        otp_service = OTPService()
        
        if command == 'send':
            self._handle_send(otp_service, options)
        elif command == 'verify':
            self._handle_verify(otp_service, options)
        elif command == 'cleanup':
            self._handle_cleanup(otp_service, options)
        elif command == 'analytics':
            self._handle_analytics(otp_service, options)
        elif command == 'status':
            self._handle_status(otp_service, options)

    def _handle_send(self, otp_service, options):
        """Handle send OTP command"""
        phone_number = options['phone_number']
        purpose = options['purpose']
        custom_otp = options.get('otp')
        
        try:
            # Validate phone number
            parsed_phone = PhoneNumber.from_string(phone_number)
            if not parsed_phone.is_valid():
                raise CommandError(f'Invalid phone number format: {phone_number}')
            
            # Send OTP
            result = otp_service.send_otp(
                phone_number=str(parsed_phone),
                purpose=purpose
            )
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ OTP sent successfully to {parsed_phone}")
                )
                self.stdout.write(f"Request ID: {result['request_id']}")
                self.stdout.write(f"Expires in: {result['expires_in']} seconds")
                
                if result.get('static_otp'):
                    self.stdout.write(
                        self.style.WARNING(f"Development OTP: {result['static_otp']}")
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(f"✗ Failed to send OTP: {result['error']}")
                )
                
        except Exception as e:
            raise CommandError(f'Error sending OTP: {str(e)}')

    def _handle_verify(self, otp_service, options):
        """Handle verify OTP command"""
        phone_number = options['phone_number']
        otp_code = options['otp_code']
        purpose = options['purpose']
        
        try:
            # Validate phone number
            parsed_phone = PhoneNumber.from_string(phone_number)
            if not parsed_phone.is_valid():
                raise CommandError(f'Invalid phone number format: {phone_number}')
            
            # Verify OTP
            result = otp_service.verify_otp(
                phone_number=str(parsed_phone),
                otp_code=otp_code,
                purpose=purpose
            )
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ OTP verified successfully for {parsed_phone}")
                )
                self.stdout.write(f"Request ID: {result.get('request_id')}")
            else:
                self.stdout.write(
                    self.style.ERROR(f"✗ OTP verification failed: {result['error']}")
                )
                if 'remaining_attempts' in result:
                    self.stdout.write(f"Remaining attempts: {result['remaining_attempts']}")
                    
        except Exception as e:
            raise CommandError(f'Error verifying OTP: {str(e)}')

    def _handle_cleanup(self, otp_service, options):
        """Handle cleanup command"""
        days = options['days']
        dry_run = options['dry_run']
        
        try:
            from datetime import timedelta
            from apps.authentication.models import OTPAttempt
            
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # Count records to be deleted
            old_attempts = OTPAttempt.objects.filter(attempted_at__lt=cutoff_date)
            old_requests = OTPRequest.objects.filter(created_at__lt=cutoff_date)
            
            attempts_count = old_attempts.count()
            requests_count = old_requests.count()
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f"DRY RUN - Would delete:")
                )
                self.stdout.write(f"  - {requests_count} OTP requests older than {days} days")
                self.stdout.write(f"  - {attempts_count} OTP attempts older than {days} days")
                self.stdout.write(f"  - Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
                return
            
            # Actually delete records
            old_attempts.delete()
            old_requests.delete()
            
            # Also cleanup expired requests
            expired_count = otp_service.cleanup_expired_requests()
            
            self.stdout.write(
                self.style.SUCCESS(f"✓ Cleanup completed:")
            )
            self.stdout.write(f"  - Deleted {requests_count} old OTP requests")
            self.stdout.write(f"  - Deleted {attempts_count} old OTP attempts") 
            self.stdout.write(f"  - Marked {expired_count} requests as expired")
            
        except Exception as e:
            raise CommandError(f'Error during cleanup: {str(e)}')

    def _handle_analytics(self, otp_service, options):
        """Handle analytics command"""
        days = options['days']
        phone_number = options.get('phone')
        
        try:
            # Get statistics
            stats = otp_service.get_otp_statistics(phone_number, days)
            
            self.stdout.write(
                self.style.SUCCESS(f"📊 OTP Analytics (Last {days} days)")
            )
            
            if phone_number:
                self.stdout.write(f"Phone Number: {phone_number}")
            
            self.stdout.write("=" * 50)
            self.stdout.write(f"Total Requests: {stats['total_requests']}")
            self.stdout.write(f"Verified: {stats['verified_count']}")
            self.stdout.write(f"Failed: {stats['failed_count']}")
            self.stdout.write(f"Expired: {stats['expired_count']}")
            self.stdout.write(f"Success Rate: {stats['success_rate']:.1f}%")
            
            # Additional breakdown by purpose
            purpose_stats = OTPRequest.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=days)
            )
            
            if phone_number:
                try:
                    parsed_phone = PhoneNumber.from_string(phone_number)
                    purpose_stats = purpose_stats.filter(phone_number=str(parsed_phone))
                except:
                    pass
            
            purpose_breakdown = purpose_stats.values('purpose').annotate(
                count=Count('id')
            ).order_by('-count')
            
            if purpose_breakdown:
                self.stdout.write("\n📋 Breakdown by Purpose:")
                for item in purpose_breakdown:
                    purpose_display = dict(OTPRequest.PurposeChoices.choices)[item['purpose']]
                    self.stdout.write(f"  - {purpose_display}: {item['count']}")
                    
        except Exception as e:
            raise CommandError(f'Error generating analytics: {str(e)}')

    def _handle_status(self, otp_service, options):
        """Handle status check command"""
        phone_number = options['phone_number']
        purpose = options['purpose']
        
        try:
            # Validate phone number
            parsed_phone = PhoneNumber.from_string(phone_number)
            if not parsed_phone.is_valid():
                raise CommandError(f'Invalid phone number format: {phone_number}')
            
            # Check cooldown status
            cooldown_check = otp_service.can_resend_otp(str(parsed_phone), purpose)
            
            self.stdout.write(
                self.style.SUCCESS(f"📱 OTP Status for {parsed_phone}")
            )
            self.stdout.write("=" * 50)
            
            if cooldown_check['can_resend']:
                self.stdout.write("✓ Can request new OTP")
            else:
                self.stdout.write(
                    f"⏳ Cooldown active - wait {cooldown_check['cooldown_remaining']} seconds"
                )
            
            # Get recent requests
            recent_requests = OTPRequest.objects.filter(
                phone_number=str(parsed_phone),
                purpose=purpose,
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).order_by('-created_at')[:5]
            
            if recent_requests:
                self.stdout.write(f"\n📋 Recent Requests (Last 24 hours):")
                for req in recent_requests:
                    status_icon = {
                        'sent': '📤',
                        'verified': '✅', 
                        'expired': '⏰',
                        'failed': '❌'
                    }.get(req.status, '❓')
                    
                    self.stdout.write(
                        f"  {status_icon} {req.created_at.strftime('%H:%M:%S')} - "
                        f"{req.get_status_display()} (Attempts: {req.attempt_count})"
                    )
            else:
                self.stdout.write("\n📋 No recent requests found")
                
            # Show current settings
            self.stdout.write(f"\n⚙️  Settings:")
            self.stdout.write(f"  - Expiry Time: {otp_service.EXPIRY_TIME}s")
            self.stdout.write(f"  - Resend Cooldown: {otp_service.RESEND_COOLDOWN}s")
            self.stdout.write(f"  - Max Attempts: {otp_service.MAX_ATTEMPTS}")
            self.stdout.write(f"  - Use Static OTP: {otp_service.USE_STATIC_OTP}")
            
        except Exception as e:
            raise CommandError(f'Error checking status: {str(e)}')