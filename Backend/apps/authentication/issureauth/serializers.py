# authentication/issuerauth/serializers.py

from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import User,Otp
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
# from .utils import log_activity,raise_validation_error
from rest_framework.permissions import IsAuthenticated
from apps.kyc.issuer_kyc.models.CompanyOnboardingApplicationModel import CompanyOnboardingApplication
# from ..models import Otp  


class MobileOtpRequestSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=15)

    def validate_mobile_number(self, value):
        """Validate that mobile number is a valid Indian number."""
        value = value.strip()

        # Remove country code if included
        if value.startswith("+91"):
            value = value[3:]
        elif value.startswith("91") and len(value) == 12:
            value = value[2:]

        # Validate: must be 10 digits and start with 6–9
        if not (value.isdigit() and len(value) == 10 and value[0] in "6789"):
            
            
            
            raise serializers.ValidationError("Enter a valid 10-digit Indian mobile number.")
        

        # Return standardized format
        return f"+91{value}"

    def create(self, validated_data):
        mobile_number = validated_data['mobile_number']

        # ✅ Create or get user with mobile number
        user, created = User.objects.get_or_create(
            mobile_number=mobile_number,
            defaults={'is_active': True}
        )

        # ✅ Create static OTP (1111)
        otp_obj = Otp.objects.create(
            user=user,
            otp_code="1111",  # static for now
            otp_type="SMS",
            expiry_time=timezone.now() + timedelta(minutes=5)
        )
  
        return {
            "user_id": user.user_id,
            "mobile_number": user.mobile_number,
            "otp_id": otp_obj.otp_id,
            "message": "OTP sent successfully to your mobile number."
        }
    
class VerifyMobileOtpSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=15)
    otp_code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        mobile_number = attrs.get("mobile_number")
        otp_code = attrs.get("otp_code")

        # Normalize mobile number
        if mobile_number.startswith("+91"):
            mobile_number = mobile_number[3:]
        elif mobile_number.startswith("91") and len(mobile_number) == 12:
            mobile_number = mobile_number[2:]

        if not (mobile_number.isdigit() and len(mobile_number) == 10 and mobile_number[0] in "6789"):
            raise serializers.ValidationError("Enter a valid 10-digit Indian mobile number.")
        mobile_number = f"+91{mobile_number}"

        # Find user
        try:
            user = User.objects.get(mobile_number=mobile_number)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")

        # Find OTP record
        try:
            otp_obj = (
                Otp.objects.filter(
                    user=user,
                    otp_type="SMS",
                    is_used=False,
                    is_del=False
                ).latest("created_at")
            )
        except Otp.DoesNotExist:
            raise serializers.ValidationError("No active OTP found. Please request a new one.")

        # Validate OTP
        if otp_obj.otp_code != otp_code:
            raise serializers.ValidationError("Invalid OTP code.")

        if otp_obj.is_expired():
            raise serializers.ValidationError("OTP has expired. Please request a new one.")

        attrs["user"] = user
        attrs["otp_obj"] = otp_obj
        return attrs

    def create(self, validated_data):
        otp_obj = validated_data["otp_obj"]
        user = validated_data["user"]

        # Mark OTP as used
        otp_obj.is_used = True
        otp_obj.save(update_fields=["is_used"])

        # Mark mobile as verified
        user.mobile_verified = True
        user.save(update_fields=["mobile_verified"])

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Check email verification status
        email_verified = getattr(user, "email_verified", False)

        # Get onboarding record if exists
        onboarding = CompanyOnboardingApplication.objects.filter(user=user).first()

        last_accessed_step = 0
        company_information_id = None

        if onboarding:
            last_accessed_step = onboarding.last_accessed_step
            company_information_id = (
                str(onboarding.company_information.company_id)
                if onboarding.company_information
                else None
            )

        # ✅ If email not verified yet, reset progress
        if not email_verified:
            last_accessed_step = 1

        # ✅ Build response payload
        response_data = {
            "user_id": user.user_id,
            "mobile_number": user.mobile_number,
            "email": user.email,
            "email_verified": email_verified,
            "last_accessed_step": last_accessed_step,
            "company_information_id": company_information_id,
            "access_token": access_token,
            "message": "Mobile number verified successfully.",
        }
        return response_data

# class VerifyMobileOtpSerializer(serializers.Serializer):
#     mobile_number = serializers.CharField(max_length=15)
#     otp_code = serializers.CharField(max_length=6)

#     def validate(self,attrs):
#         mobile_number = attrs.get('mobile_number')
#         otp_code = attrs.get('otp_code')

#         if mobile_number.startswith('+91'):
#             mobile_number = mobile_number[3:]
#         elif mobile_number.startswith("91") and len(mobile_number) == 12:
#             mobile_number = mobile_number[2:]
#         if not (mobile_number.isdigit() and len(mobile_number)==10 and mobile_number[0] in "6789"):
#             raise serializers.ValidationError("Enter a valid 10-digit Indian mobile number.")
#         mobile_number = f"+91{mobile_number}"

# # user find
#         try:
#             user = User.objects.get(mobile_number=mobile_number)
#         except User.DoesNotExist:
#             raise serializers.ValidationError("User does not exist")
#             # raise_validation_error(
#             #     "Invalid user_id. User not found.",
#             #     activity_type="LOGIN_FAILED",
#             #     severity="ERROR",
#             #     request=request,
#             #     metadata={"user_id": user_id, "otp_type": otp_type}
#             # )
        
#         # otp check
#         try:
#             otp_obj =(
#                 Otp.objects.filter(user=user,otp_type="SMS", is_used=False, is_del=False).latest('created_at')
#             )
#         except Otp.DoesNotExist:
#             raise serializers.ValidationError("No active OTP found. Please request a new one.")
        
#         # validate otp
#         if otp_obj.otp_code != otp_code:
#             raise serializers.ValidationError("Invalid OTP code.")
        
#         if otp_obj.is_expired():
#             raise serializers.ValidationError("OTP has expired. Please request a new one.")
        
#         attrs["user"] = user
#         attrs['otp_obj'] = otp_obj
#         return attrs
    
#     def create(self, validated_data):
#         otp_obj = validated_data["otp_obj"]
#         user = validated_data["user"]

#         otp_obj.is_used = True
#         otp_obj.save(update_fields=["is_used"])

#         user.mobile_verified = True
#         user.save(update_fields=["mobile_verified"])

#         return {
#             "user_id": user.user_id,
#             "mobile_number": user.mobile_number,
#             "message": "Mobile number verified successfully.",
#         }
    

class EmailOtpRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField(max_length=255)

    def validate_email(self, value):
        """Ensure email is lowercase and properly formatted."""
        return value.strip().lower()

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None
        email = attrs.get("email")

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required to send OTP.")

        # ✅ Ensure email not taken by another user
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("This email is already registered with another account.")

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        name = validated_data["name"]
        email = validated_data["email"]

        # ✅ Update user’s email and name (if field exists)
        user.email = email
        if hasattr(user, "name"):
            user.name = name
        user.save(update_fields=["email"] + (["name"] if hasattr(user, "name") else []))

        # ✅ Create OTP (you can switch to random if needed)
        otp_obj = Otp.objects.create(
            user=user,
            otp_code="1111",  # static for now — can replace with random
            otp_type="EMAIL",
            expiry_time=timezone.now() + timedelta(minutes=5),
        )

        return {
            "user_id": user.user_id,
            "email": user.email,
            "otp_id": otp_obj.otp_id,
            "message": f"OTP sent successfully to {user.email}.",
        }
# class EmailOtpRequestSerializer(serializers.Serializer):
#     user_id = serializers.IntegerField()
#     name = serializers.CharField(max_length=255)
#     email = serializers.EmailField(max_length=255)

#     def validate_email(self, value):
#         """Ensure email is lowercase and properly formatted."""
#         return value.strip().lower()

#     def validate(self, attrs):
#         user_id = attrs.get("user_id")
#         email = attrs.get("email")

#         # ✅ Ensure user exists
#         try:
#             user = User.objects.get(user_id=user_id, is_del=0)
#         except User.DoesNotExist:
#             raise serializers.ValidationError("Invalid user_id. User does not exist.")

#         # ✅ Ensure email not taken by another user
#         if User.objects.filter(email=email).exclude(user_id=user_id).exists():
#             raise serializers.ValidationError("This email is already registered with another account.")

#         attrs["user"] = user
#         return attrs

#     def create(self, validated_data):
#         user = validated_data["user"]
#         name = validated_data["name"]
#         email = validated_data["email"]

#         # ✅ Update user’s email and (if present) name
#         user.email = email
#         if hasattr(user, "name"):
#             user.name = name
#         user.save(update_fields=["email"] + (["name"] if hasattr(user, "name") else []))

#         # ✅ Create static OTP (1111) for email
#         otp_obj = Otp.objects.create(
#             user=user,
#             otp_code="1111",  # static OTP
#             otp_type="EMAIL",
#             expiry_time=timezone.now() + timedelta(minutes=5)
#         )

#     #     log_activity(
#     #     user=user,
#     #     activity_type="EMAIL_OTP_SENT",
#     #     description=f"OTP sent to email {user.email}",
#     #     severity="INFO",
#     #     related_table="otp",
#     #     related_record_id=otp_obj.otp_id,
#     #     metadata={"otp_type": "EMAIL"}
#     # )

#         return {
#             "user_id": user.user_id,   # actual integer value
#             "email": user.email,
#             "otp_id": otp_obj.otp_id,
#             "message": "OTP sent successfully to your email address."
#         }


class VerifyEmailOtpSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    otp_code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required to verify OTP.")

        email = attrs.get("email").strip().lower()
        otp_code = attrs.get("otp_code")

        # ✅ Email match check
        if user.email.strip().lower() != email:
            raise serializers.ValidationError("Email does not match the logged-in user.")

        # ✅ Get latest active OTP
        otp_obj = (
            Otp.objects.filter(
                user=user,
                otp_type="EMAIL",
                is_used=False,
                is_del=False
            ).order_by("-created_at").first()
        )

        if not otp_obj:
            raise serializers.ValidationError("No active OTP found. Please request a new one.")

        if otp_obj.is_expired():
            raise serializers.ValidationError("OTP has expired. Please request a new one.")

        if otp_obj.otp_code != otp_code:
            raise serializers.ValidationError("Invalid OTP code.")

        attrs["user"] = user
        attrs["otp_obj"] = otp_obj
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        otp_obj = validated_data["otp_obj"]

        # ✅ Mark OTP used
        otp_obj.is_used = True
        otp_obj.updated_at = timezone.now()
        otp_obj.save(update_fields=["is_used", "updated_at"])

        # ✅ Mark user email verified
        user.email_verified = True
        user.updated_at = timezone.now()
        user.save(update_fields=["email_verified", "updated_at"])

        # ✅ Generate JWT Access Token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return {
            "user_id": user.user_id,
            "email": user.email,
            "email_verified": user.email_verified,
            "mobile_number": user.mobile_number,
            # "kyc_status": user.kyc_status,
            "access_token": access_token,
            "message": "Email verified successfully."
        }
# class VerifyEmailOtpSerializer(serializers.Serializer):
#     user_id = serializers.IntegerField()
#     email = serializers.EmailField(max_length=255)
#     otp_code = serializers.CharField(max_length=6)

#     def validate(self,attrs):
#         user_id = attrs.get('user_id')
#         email = attrs.get("email").strip().lower()
#         otp_code = attrs.get('otp_code')

#         try:
#             user = User.objects.get(user_id=user_id,is_del=0)
#         except User.DoesNotExist:
#             raise serializers.ValidationError("Invalid user_id. User not found.")
        
#         if user.email != email:
#             raise serializers.ValidationError("Email does not match the registered user.")
        
#         otp_obj = (
#             Otp.objects.filter(user=user,otp_type="EMAIL",is_used=False,is_del=False).order_by("-created_at").first()
        
#         )

#         if not otp_obj:
#             raise serializers.ValidationError("No active OTP found. Please request a new one.")
        
#         if otp_obj.is_expired():
#             raise serializers.ValidationError("OTP has expired. Please request a new one.")
        
#         if otp_obj.otp_code != otp_code:
#             raise serializers.ValidationError("Invalid OTP code.")
        
              
#         attrs['user']=user
#         attrs["otp_obj"]= otp_obj

#         return attrs
    
#     def create(self,validated_data):
#         user = validated_data["user"]
#         otp_obj = validated_data["otp_obj"]
        
#         otp_obj.is_used = True
#         otp_obj.save(update_fields=["is_used", "updated_at"])
#         user.email_verified = True
#         user.save(update_fields=["email_verified", "updated_at"])
#         refresh = RefreshToken.for_user(user)
#         access_token= str(refresh.access_token)

#     #     log_activity(
#     #     user=user,
#     #     activity_type="EMAIL_OTP_VERIFIED",
#     #     description="Email verified successfully.",
#     #     severity="INFO",
#     #     related_table="otp",
#     #     related_record_id=otp_obj.otp_id,
#     #     metadata={"otp_type": "EMAIL"}
#     # )


#         return {
#             "user_id": user.user_id,
#             "email": user.email,
#             "email_verified": user.email_verified,
#             "mobile_number":user.mobile_number,
#             "kyc_status":user.kyc_status,
#             "access_token":access_token,
#             "message": "Email verified successfully."
#         }
    

class LoginRequestSerializer(serializers.Serializer):
    email_or_mobile = serializers.CharField(max_length=255)

    def validate(self,attrs):
        email_or_mobile = attrs.get("email_or_mobile").strip().lower()

        user = None

        if "@" in email_or_mobile:
            try:
                user = User.objects.get(email=email_or_mobile,is_del=0)
            except User.DoesNotExist:
                raise serializers.ValidationError("No user found with this email address.")
            
        else:
            if email_or_mobile.startswith("+91"):
                email_or_mobile = email_or_mobile[3:]
            elif email_or_mobile.startswith("91") and len(email_or_mobile) == 12:
                email_or_mobile = email_or_mobile[2:]

            if not (email_or_mobile.isdigit() and len(email_or_mobile) == 10 and email_or_mobile[0] in "6789"):
                raise serializers.ValidationError("Enter a valid 10-digit Indian mobile number.")
            formatted_mobile = f"+91{email_or_mobile}"
            try:

                user = User.objects.get(mobile_number=formatted_mobile, is_del=0)
            except User.DoesNotExist:
                raise serializers.ValidationError("No user found with this mobile number.")
        attrs['user'] = user
        return attrs
            
            
    def create(self, validated_data):
            user = validated_data['user']

            if validated_data["email_or_mobile"].isdigit() or validated_data["email_or_mobile"].startswith("+91"):
                otp_type = "SMS"
            else:
                otp_type = "EMAIL"

            otp_obj = Otp.objects.create(
            user=user,
            otp_code="1111",
            otp_type=otp_type,
            expiry_time=timezone.now() + timedelta(minutes=5)
        )
            
    #         log_activity(
    #     user=user,
    #     activity_type="LOGIN_OTP_SENT",
    #     description=f"Login OTP sent via {otp_type}",
    #     severity="INFO",
    #     related_table="otp",
    #     related_record_id=otp_obj.otp_id,
    #     metadata={"otp_type": otp_type}
    # )
            return {
            "user_id": user.user_id,
            "email": user.email,
            "mobile_number": user.mobile_number,
            "otp_type": otp_type,
            "otp_id": otp_obj.otp_id,
            "message": f"OTP sent successfully to your {'email' if otp_type == 'EMAIL' else 'mobile number'}."
        }
    
class VerifyLoginOtpSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    otp_code = serializers.CharField(max_length=6)
    otp_type = serializers.ChoiceField(choices=["SMS", "EMAIL"])
    # otp_type = serializers.ChoiceField(choices=["SMS", "EMAIL"], default="SMS")

    def validate(self, attrs):
        user_id = attrs.get("user_id")
        otp_code = attrs.get("otp_code")
        otp_type = attrs.get("otp_type")

        # ✅ Fetch user
        try:
            user = User.objects.get(user_id=user_id, is_del=0)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid user_id. User not found.")

        # ✅ Fetch OTP based on type (SMS or EMAIL)
        otp_obj = (
            Otp.objects.filter(
                user=user,
                otp_type=otp_type,  # 🔥 dynamic filter instead of hardcoded EMAIL
                is_used=False,
                is_del=False
            )
            .order_by("-created_at")
            .first()
        )

        if not otp_obj:
            raise serializers.ValidationError("No active OTP found. Please request a new one.")

        if otp_obj.is_expired():
            raise serializers.ValidationError("OTP has expired. Please request a new one.")

        if otp_obj.otp_code != otp_code:
            raise serializers.ValidationError("Invalid OTP code.")

        attrs["user"] = user
        attrs["otp_obj"] = otp_obj
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        otp_obj = validated_data["otp_obj"]

        # ✅ Mark OTP as used
        otp_obj.is_used = True
        otp_obj.save(update_fields=["is_used", "updated_at"])

        refresh = RefreshToken.for_user(user)
        access_token= str(refresh.access_token)

    #     log_activity(
    #     user=user,
    #     activity_type="LOGIN_SUCCESS",
    #     description=f"User logged in using {otp_obj.otp_type} OTP.",
    #     severity="INFO",
    #     related_table="otp",
    #     related_record_id=otp_obj.otp_id,
    #     metadata={"otp_type": otp_obj.otp_type}
    # )
        # refresh = RefreshToken.for_user(user)
        # access_token = str(refresh.access_token)

        return {
            "user_id": user.user_id,
            "email": user.email,
            "mobile_number": user.mobile_number,
            "access_token":access_token,
            "kyc_status":user.kyc_status,
            # "access_token": access_token,
            # "refresh_token": str(refresh),
            "message": "Login successful."
        }



        
        


            
            

    


        
