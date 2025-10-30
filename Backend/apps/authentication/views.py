# # Backend/apps/authentication/views.py
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import AllowAny
# from rest_framework.throttling import AnonRateThrottle
# from django.utils.decorators import method_decorator
# from django.views.decorators.cache import cache_page
# from django.core.validators import ValidationError
# from phonenumber_field.phonenumber import PhoneNumber
# import logging

# from .otp_helpers import OTPService
# from .serializers import SendOTPSerializer, VerifyOTPSerializer, ResendOTPSerializer
# from config.throttling import OTPThrottle

# logger = logging.getLogger(__name__)

# class SendOTPAPIView(APIView):
#     """
#     Send OTP to phone number
    
#     This endpoint allows users to request an OTP for various purposes like
#     registration, login, password reset, etc.
#     """
#     permission_classes = [AllowAny]
#     throttle_classes = [OTPThrottle, AnonRateThrottle]
    
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.otp_service = OTPService()
    
#     def post(self, request):
#         """Send OTP to the provided phone number"""
#         serializer = SendOTPSerializer(data=request.data)
        
#         if not serializer.is_valid():
#             return Response(
#                 {"error": serializer.errors},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         phone_number = serializer.validated_data['phone_number']
#         purpose = serializer.validated_data.get('purpose', 'registration')
        
#         try:
#             # Check cooldown period
#             cooldown_check = self.otp_service.can_resend_otp(str(phone_number), purpose)
#             if not cooldown_check['can_resend']:
#                 return Response(
#                     {
#                         "error": cooldown_check['message'],
#                         "cooldown_remaining": cooldown_check['cooldown_remaining']
#                     },
#                     status=status.HTTP_429_TOO_MANY_REQUESTS
#                 )
            
#             # Send OTP
#             result = self.otp_service.send_otp(
#                 phone_number=str(phone_number),
#                 purpose=purpose,
#                 request=request
#             )
            
#             if result['success']:
#                 response_data = {
#                     "message": result['message'],
#                     "request_id": result['request_id'],
#                     "expires_in": result['expires_in']
#                 }
                
#                 # Only include static OTP in development mode
#                 if result.get('static_otp'):
#                     response_data['static_otp'] = result['static_otp']
                
#                 logger.info(f"OTP sent successfully to {phone_number} for {purpose}")
#                 return Response(response_data, status=status.HTTP_200_OK)
            
#             else:
#                 logger.warning(f"Failed to send OTP to {phone_number}: {result.get('error')}")
#                 return Response(
#                     {"error": result['error']},
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )
                
#         except Exception as e:
#             logger.error(f"Unexpected error in SendOTPAPIView: {str(e)}")
#             return Response(
#                 {"error": "An unexpected error occurred. Please try again."},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# class VerifyOTPAPIView(APIView):
#     """
#     Verify OTP for phone number
    
#     This endpoint allows users to verify the OTP they received
#     """
#     permission_classes = [AllowAny]
#     throttle_classes = [AnonRateThrottle]
    
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.otp_service = OTPService()
    
#     def post(self, request):
#         """Verify the OTP code"""
#         serializer = VerifyOTPSerializer(data=request.data)
        
#         if not serializer.is_valid():
#             return Response(
#                 {"error": serializer.errors},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         phone_number = serializer.validated_data['phone_number']
#         otp_code = serializer.validated_data['otp_code']
#         purpose = serializer.validated_data.get('purpose', 'registration')
        
#         try:
#             # Verify OTP
#             result = self.otp_service.verify_otp(
#                 phone_number=str(phone_number),
#                 otp_code=otp_code,
#                 purpose=purpose,
#                 request=request
#             )
            
#             if result['success']:
#                 logger.info(f"OTP verified successfully for {phone_number} - {purpose}")
#                 return Response(
#                     {
#                         "message": result['message'],
#                         "request_id": result.get('request_id')
#                     },
#                     status=status.HTTP_200_OK
#                 )
#             else:
#                 # Log failed verification attempt
#                 logger.warning(f"OTP verification failed for {phone_number}: {result['error']}")
                
#                 response_data = {"error": result['error']}
#                 if 'remaining_attempts' in result:
#                     response_data['remaining_attempts'] = result['remaining_attempts']
                
#                 return Response(
#                     response_data,
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
                
#         except Exception as e:
#             logger.error(f"Unexpected error in VerifyOTPAPIView: {str(e)}")
#             return Response(
#                 {"error": "An unexpected error occurred. Please try again."},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# class ResendOTPAPIView(APIView):
#     """
#     Resend OTP to phone number
    
#     This endpoint allows users to request a new OTP if they didn't receive
#     the previous one or if it expired
#     """
#     permission_classes = [AllowAny]
#     throttle_classes = [OTPThrottle, AnonRateThrottle]
    
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.otp_service = OTPService()
    
#     def post(self, request):
#         """Resend OTP to the provided phone number"""
#         serializer = ResendOTPSerializer(data=request.data)
        
#         if not serializer.is_valid():
#             return Response(
#                 {"error": serializer.errors},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         phone_number = serializer.validated_data['phone_number']
#         purpose = serializer.validated_data.get('purpose', 'registration')
        
#         try:
#             # Use the same send_otp method as it handles cooldown internally
#             result = self.otp_service.send_otp(
#                 phone_number=str(phone_number),
#                 purpose=purpose,
#                 request=request
#             )
            
#             if result['success']:
#                 response_data = {
#                     "message": "OTP resent successfully",
#                     "request_id": result['request_id'],
#                     "expires_in": result['expires_in']
#                 }
                
#                 # Only include static OTP in development mode
#                 if result.get('static_otp'):
#                     response_data['static_otp'] = result['static_otp']
                
#                 logger.info(f"OTP resent successfully to {phone_number} for {purpose}")
#                 return Response(response_data, status=status.HTTP_200_OK)
            
#             else:
#                 logger.warning(f"Failed to resend OTP to {phone_number}: {result.get('error')}")
#                 response_data = {"error": result['error']}
                
#                 if 'cooldown_remaining' in result:
#                     response_data['cooldown_remaining'] = result['cooldown_remaining']
#                     return Response(response_data, status=status.HTTP_429_TOO_MANY_REQUESTS)
                
#                 return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
#         except Exception as e:
#             logger.error(f"Unexpected error in ResendOTPAPIView: {str(e)}")
#             return Response(
#                 {"error": "An unexpected error occurred. Please try again."},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# class OTPStatusAPIView(APIView):
#     """
#     Check OTP status and get statistics (for debugging/monitoring)
#     """
#     permission_classes = [AllowAny]  # Change to IsAuthenticated in production
    
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.otp_service = OTPService()
    
#     @method_decorator(cache_page(60 * 2))  # Cache for 2 minutes
#     def get(self, request):
#         """Get OTP statistics and status"""
#         phone_number = request.query_params.get('phone_number')
#         days = int(request.query_params.get('days', 7))
        
#         try:
#             # Get statistics
#             stats = self.otp_service.get_otp_statistics(phone_number, days)
            
#             # Check if user can request OTP
#             can_request = True
#             cooldown_info = {}
            
#             if phone_number:
#                 try:
#                     # Validate phone number format
#                     parsed_phone = PhoneNumber.from_string(phone_number)
#                     if parsed_phone.is_valid():
#                         cooldown_check = self.otp_service.can_resend_otp(
#                             str(parsed_phone), 'registration'
#                         )
#                         can_request = cooldown_check['can_resend']
#                         if not can_request:
#                             cooldown_info = {
#                                 'cooldown_remaining': cooldown_check['cooldown_remaining']
#                             }
#                 except:
#                     pass
            
#             return Response({
#                 "statistics": stats,
#                 "can_request_otp": can_request,
#                 "cooldown_info": cooldown_info,
#                 "otp_settings": {
#                     "expiry_time": self.otp_service.EXPIRY_TIME,
#                     "resend_cooldown": self.otp_service.RESEND_COOLDOWN,
#                     "max_attempts": self.otp_service.MAX_ATTEMPTS,
#                     "use_static_otp": self.otp_service.USE_STATIC_OTP
#                 }
#             }, status=status.HTTP_200_OK)
            
#         except Exception as e:
#             logger.error(f"Error in OTPStatusAPIView: {str(e)}")
#             return Response(
#                 {"error": "Failed to fetch OTP status"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )



# Backend/apps/authentication/views.py
import logging
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle

from .otp_helpers import OTPService
from .serializers import SendOTPSerializer, VerifyOTPSerializer, ResendOTPSerializer
from config.throttling import OTPThrottle

logger = logging.getLogger(__name__)


class SendOTPAPIView(APIView):
    """
    Send OTP to a phone number (public endpoint)
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Skip global JWT auth
    throttle_classes = [OTPThrottle, AnonRateThrottle]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.otp_service = OTPService()

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        purpose = serializer.validated_data.get('purpose', 'registration')

        try:
            cooldown_check = self.otp_service.can_resend_otp(str(phone_number), purpose)
            if not cooldown_check['can_resend']:
                return Response(
                    {
                        "error": cooldown_check['message'],
                        "cooldown_remaining": cooldown_check['cooldown_remaining']
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            result = self.otp_service.send_otp(phone_number=str(phone_number), purpose=purpose, request=request)

            if result['success']:
                response_data = {
                    "message": result['message'],
                    "request_id": result['request_id'],
                    "expires_in": result['expires_in']
                }
                if result.get('static_otp'):
                    response_data['static_otp'] = result['static_otp']

                logger.info(f"OTP sent successfully to {phone_number} for {purpose}")
                return Response(response_data, status=status.HTTP_200_OK)

            logger.warning(f"Failed to send OTP to {phone_number}: {result.get('error')}")
            return Response({"error": result['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Unexpected error in SendOTPAPIView: {str(e)}")
            return Response({"error": "An unexpected error occurred. Please try again."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyOTPAPIView(APIView):
    """
    Verify OTP (public endpoint)
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.otp_service = OTPService()

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data['otp_code']
        purpose = serializer.validated_data.get('purpose', 'registration')

        try:
            result = self.otp_service.verify_otp(phone_number=str(phone_number),
                                                 otp_code=otp_code,
                                                 purpose=purpose,
                                                 request=request)
            if result['success']:
                logger.info(f"OTP verified successfully for {phone_number} - {purpose}")
                return Response({"message": result['message'], "request_id": result.get('request_id')},
                                status=status.HTTP_200_OK)

            logger.warning(f"OTP verification failed for {phone_number}: {result['error']}")
            response_data = {"error": result['error']}
            if 'remaining_attempts' in result:
                response_data['remaining_attempts'] = result['remaining_attempts']

            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Unexpected error in VerifyOTPAPIView: {str(e)}")
            return Response({"error": "An unexpected error occurred. Please try again."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResendOTPAPIView(APIView):
    """
    Resend OTP (public endpoint)
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [OTPThrottle, AnonRateThrottle]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.otp_service = OTPService()

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        purpose = serializer.validated_data.get('purpose', 'registration')

        try:
            result = self.otp_service.send_otp(phone_number=str(phone_number), purpose=purpose, request=request)

            if result['success']:
                response_data = {
                    "message": "OTP resent successfully",
                    "request_id": result['request_id'],
                    "expires_in": result['expires_in']
                }
                if result.get('static_otp'):
                    response_data['static_otp'] = result['static_otp']

                logger.info(f"OTP resent successfully to {phone_number} for {purpose}")
                return Response(response_data, status=status.HTTP_200_OK)

            logger.warning(f"Failed to resend OTP to {phone_number}: {result.get('error')}")
            response_data = {"error": result['error']}
            if 'cooldown_remaining' in result:
                response_data['cooldown_remaining'] = result['cooldown_remaining']
                return Response(response_data, status=status.HTTP_429_TOO_MANY_REQUESTS)

            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Unexpected error in ResendOTPAPIView: {str(e)}")
            return Response({"error": "An unexpected error occurred. Please try again."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OTPStatusAPIView(APIView):
    """
    OTP status / statistics (optional public endpoint)
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.otp_service = OTPService()

    @method_decorator(cache_page(60 * 2))  # Cache 2 minutes
    def get(self, request):
        phone_number = request.query_params.get('phone_number')
        days = int(request.query_params.get('days', 7))

        try:
            stats = self.otp_service.get_otp_statistics(phone_number, days)

            can_request = True
            cooldown_info = {}

            if phone_number:
                try:
                    cooldown_check = self.otp_service.can_resend_otp(str(phone_number), 'registration')
                    can_request = cooldown_check['can_resend']
                    if not can_request:
                        cooldown_info = {"cooldown_remaining": cooldown_check['cooldown_remaining']}
                except:
                    pass

            return Response({
                "statistics": stats,
                "can_request_otp": can_request,
                "cooldown_info": cooldown_info,
                "otp_settings": {
                    "expiry_time": self.otp_service.EXPIRY_TIME,
                    "resend_cooldown": self.otp_service.RESEND_COOLDOWN,
                    "max_attempts": self.otp_service.MAX_ATTEMPTS,
                    "use_static_otp": self.otp_service.USE_STATIC_OTP
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in OTPStatusAPIView: {str(e)}")
            return Response({"error": "Failed to fetch OTP status"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
