# apps/authentication/serializers/CompanyRegistrationSerializer.py

from rest_framework import serializers
from django.db import transaction
from apps.authentication.issureauth.models import User
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation 
from apps.authentication.services.session_manager import VerificationSession
from apps.authentication.services.EmailService import EmailService


class CompanyRegistrationSerializer(serializers.Serializer):
    """
    Handles complete registration: User + Company KYC
    Stage 2 of the registration flow
    """
    
    # User fields
    mobile_number = serializers.CharField(max_length=10)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6)
    role = serializers.CharField()
    
    # Company KYC fields
    corporate_identification_number = serializers.CharField(max_length=21)
    company_name = serializers.CharField(max_length=255)
    gstin = serializers.CharField(max_length=15)
    date_of_incorporation = serializers.DateField()
    
    city_of_incorporation = serializers.CharField(max_length=100)
    state_of_incorporation = serializers.CharField(max_length=100)
    country_of_incorporation = serializers.CharField(max_length=100)
    
    entity_type = serializers.ChoiceField(choices=CompanyInformation.COMPANY_TYPE_CHOICES)
    sector = serializers.CharField(max_length=50)
    
    company_pan_number = serializers.CharField(max_length=10)
    pan_holder_name = serializers.CharField(max_length=255)
    date_of_birth = serializers.DateField()
    
    msme_udyam_registration_no = serializers.CharField(max_length=50, allow_blank=True, required=False)
    
    # Human intervention flag
    human_intervention = serializers.BooleanField(required=True)
    
    def validate(self, attrs):
        """
        1. Validate session verification
        2. Validate PAN holder name vs Company name
        """
        request = self.context.get("request")
        
        # Step 1: Session verification check
        if not VerificationSession.is_mobile_verified(request):
            raise serializers.ValidationError({
                "non_field_errors": ["Mobile number is not verified"]
            })
        
        if not VerificationSession.is_email_verified(request):
            raise serializers.ValidationError({
                "non_field_errors": ["Email is not verified"]
            })
        
        # Step 2: PAN holder name validation
        pan_holder_name = attrs.get("pan_holder_name", "").lower()
        company_name = attrs.get("company_name", "").lower()
        
        if pan_holder_name not in company_name:
            raise serializers.ValidationError({
                "non_field_errors": ["PAN Holder Name does not match Company Name"]
            })
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Transaction-safe creation of User + CompanyInformation
        """
        request = self.context.get("request")
        
        # Extract user data
        user_data = {
            "mobile_number": validated_data["mobile_number"],
            "email": validated_data["email"],
            "password": validated_data["password"],
            "role": validated_data["role"],
        }
        
        # Step 1: Create User
        user = User.objects.create_user(**user_data)
        user.mobile_verified = True
        user.email_verified = True
        user.save()
        
        # Step 2: Determine verification status based on human_intervention
        human_intervention = validated_data.get("human_intervention", False)
        verification_status = "PENDING" if human_intervention else "SUCCESS"
        
        # Step 3: Create CompanyInformation
        company_data = {
            "user": user,
            "corporate_identification_number": validated_data["corporate_identification_number"],
            "company_name": validated_data["company_name"],
            "gstin": validated_data["gstin"],
            "date_of_incorporation": validated_data["date_of_incorporation"],
            "city_of_incorporation": validated_data["city_of_incorporation"],
            "state_of_incorporation": validated_data["state_of_incorporation"],
            "country_of_incorporation": validated_data["country_of_incorporation"],
            "entity_type": validated_data["entity_type"],
            "sector": validated_data["sector"],
            "company_pan_number": validated_data["company_pan_number"],
            "pan_holder_name": validated_data["pan_holder_name"],
            "date_of_birth": validated_data["date_of_birth"],
            "msme_udyam_registration_no": validated_data.get("msme_udyam_registration_no", ""),
            "human_intervention": human_intervention,
            "verification_status": verification_status,
        }
        
        company = CompanyInformation.objects.create(**company_data)
        
        # Step 4: Send email based on verification status
        self._send_registration_email(user, company, verification_status)
        
        # Return both user and company for response
        return {
            "user": user,
            "company": company,
            "verification_status": verification_status
        }
    
    def _send_registration_email(self, user, company, verification_status):
        """
        Send appropriate email based on verification status using EmailService
        """
        if verification_status == "SUCCESS":
            EmailService.send_registration_success_email(user, company)
        elif verification_status == "PENDING":
            EmailService.send_registration_pending_email(user, company)