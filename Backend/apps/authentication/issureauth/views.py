from rest_framework.views import APIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import MobileOtpRequestSerializer,VerifyMobileOtpSerializer,EmailOtpRequestSerializer,VerifyEmailOtpSerializer,LoginRequestSerializer,VerifyLoginOtpSerializer
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
class SendMobileOtpView(APIView):
    permission_classes = [AllowAny]
    def post(self,request):
        serializer = MobileOtpRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save()

            return Response(
                {
                    "status": "success",
                    "message": data["message"],
                    "data": {
                        "user_id": data["user_id"],
                        "mobile_number": data["mobile_number"],
                        "otp_id": data["otp_id"]
                    }
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
class VerifyMobileOtpView(APIView):
    permission_classes =[AllowAny]

    def post(self,request):
        serializer = VerifyMobileOtpSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.save()
            return Response({"status": "success", "message": data["message"], "data": {
                "user_id":data["user_id"],
                "mobile_number":data["mobile_number"],
                "email":data["email"],
                "email_verified":data["email_verified"],
                "last_accessed_step":data["last_accessed_step"],
                "access_token":data["access_token"],
            }},
                status=status.HTTP_200_OK,)
        
        return Response({"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,)
    
# class SendEmailOtpView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def post(self,request):
#         serializer = EmailOtpRequestSerializer(data=request.data)
#         if serializer.is_valid():
#             data = serializer.save()

#             return  Response(
#                 {
#                     "status": "success",
#                     "message": data["message"],
#                     "data": {
#                         "user_id": data["user_id"],
#                         "email": data["email"],
#                         "otp_id": data["otp_id"],
#                     },
#                 },
#                 status=status.HTTP_201_CREATED,
#             )
#         return Response(
#             {"status": "error", "errors": serializer.errors},
#             status=status.HTTP_400_BAD_REQUEST,
#         )

class SendEmailOtpView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EmailOtpRequestSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            data = serializer.save()
            return Response(
                {
                    "status": "success",
                    "message": data["message"],
                    "data": {
                        "user_id": data["user_id"],
                        "email": data["email"],
                        "otp_id": data["otp_id"],
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    

class VerifyEmailOtpView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyEmailOtpSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            data = serializer.save()
            return Response(
                {
                    "status": "success",
                    "message": data["message"],
                    "last_accessed_step":0,
                    "data": {
                        "user_id": data["user_id"],
                        "email": data["email"],
                        "email_verified": data["email_verified"],
                        "mobile_number": data["mobile_number"],
                        # "kyc_status": data["kyc_status"],
                        # "access_token": data["access_token"],
                    },
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
# class VerifyEmailOtpView(APIView):

#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def post(self,request):
#         serializer = VerifyEmailOtpSerializer(data=request.data)

#         if serializer.is_valid():
#             data = serializer.save()

#             return Response(
#                 {
#                     "status": "success",
#                     "message": data["message"],
#                     "data": {
#                         "user_id": data["user_id"],
#                         "email": data["email"],
#                         "email_verified": data["email_verified"],
#                         "mobile_number":data["mobile_number"],
#                         "kyc_status":data['kyc_status'],
#                         "access_token": data['access_token']
#                     }
#                 },
#                 status=status.HTTP_200_OK
#             )
#         return Response(
#             {"status": "error", "errors": serializer.errors},
#             status=status.HTTP_400_BAD_REQUEST
#         )
    
class LoginRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self,request):
        serializer = LoginRequestSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.save()

            return Response(
                {
                    "status": "success",
                    "message": data["message"],
                    "data": {
                        "user_id": data["user_id"],
                        "email": data["email"],
                        "mobile_number": data["mobile_number"],
                        "otp_type": data["otp_type"],
                        "otp_id": data["otp_id"]
                    }
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    

class VerifyLoginOtpView(APIView):
    """
    Verifies login OTP and returns access tokens.
    """
    permission_classes = []  # Public endpoint

    def post(self, request):
        serializer = VerifyLoginOtpSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save()
            return Response(
                {
                    "status": "success",
                    "message": data["message"],
                    "data": {
                        "user_id": data["user_id"],
                        "email": data["email"],
                        "mobile_number": data["mobile_number"],
                        "kyc_status":data['kyc_status'],
                        "access_token": data['access_token']
                        # "access_token": data["access_token"],
                        # "refresh_token": data["refresh_token"]
                    },
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

        
    
            

    

    