from rest_framework import serializers
from django.db import transaction

from apps.authentication.models.UserModel import User
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from apps.authentication.services.EmailService import EmailService
from apps.authentication.services.verification_store import VerificationStore


class CompanyRegistrationSerializer(serializers.Serializer):

    # USER FIELDS
    mobile_number = serializers.CharField(max_length=15)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6)
    role = serializers.CharField()

    # COMPANY FIELDS
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

    msme_udyam_registration_no = serializers.CharField(
        max_length=50, required=False, allow_blank=True
    )

    human_intervention = serializers.BooleanField(required=True)

    # --------------------------------------------------------------
    # VALIDATE USING CACHE-BASED VERIFICATION
    # --------------------------------------------------------------
    def validate(self, attrs):
        request = self.context["request"]
        
        mobile = attrs.get("mobile_number")
        email = attrs.get("email")

        # 1️⃣ CHECK MOBILE VERIFICATION (FROM CACHE)
        if not VerificationStore.is_mobile_verified(request, mobile):
            raise serializers.ValidationError({
                "non_field_errors": ["Mobile number is not verified. Please verify your mobile first."]
            })

        # 2️⃣ CHECK EMAIL VERIFICATION (FROM CACHE)
        if not VerificationStore.is_email_verified(request, email):
            raise serializers.ValidationError({
                "non_field_errors": ["Email is not verified. Please verify your email first."]
            })

        # 3️⃣ PAN VALIDATION
        if attrs["pan_holder_name"].lower() not in attrs["company_name"].lower():
            raise serializers.ValidationError({
                "non_field_errors": ["PAN Holder Name does not match Company Name"]
            })

        # ❗ DO NOT check for duplicate user here
        # Validation runs again during .data and causes false duplicate error

        return attrs

    # --------------------------------------------------------------
    # CREATE USER + COMPANY (CACHE-BASED)
    # --------------------------------------------------------------
    @transaction.atomic
    def create(self, validated_data):
        mobile = validated_data["mobile_number"]
        email = validated_data["email"]

        # 1️⃣ DUPLICATE CHECK MOVED HERE (ONLY RUN ONCE)
        if User.objects.filter(mobile_number=mobile).exists():
            raise serializers.ValidationError({
                "non_field_errors": ["User with this mobile number already exists"]
            })

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({
                "non_field_errors": ["User with this email already exists"]
            })

        # 2️⃣ CREATE USER
        user = User.objects.create_user(
            mobile_number=mobile,
            email=email,
            password=validated_data["password"],
            role=validated_data["role"]
        )
        user.mobile_verified = True
        user.email_verified = True
        user.save()

        # 3️⃣ COMPANY VERIFICATION STATUS
        status = "PENDING" if validated_data["human_intervention"] else "SUCCESS"

        # 4️⃣ CREATE COMPANY
        company = CompanyInformation.objects.create(
            user=user,
            corporate_identification_number=validated_data["corporate_identification_number"],
            company_name=validated_data["company_name"],
            gstin=validated_data["gstin"],
            date_of_incorporation=validated_data["date_of_incorporation"],
            city_of_incorporation=validated_data["city_of_incorporation"],
            state_of_incorporation=validated_data["state_of_incorporation"],
            country_of_incorporation=validated_data["country_of_incorporation"],
            entity_type=validated_data["entity_type"],
            sector=validated_data["sector"],
            company_pan_number=validated_data["company_pan_number"],
            pan_holder_name=validated_data["pan_holder_name"],
            date_of_birth=validated_data["date_of_birth"],
            msme_udyam_registration_no=validated_data.get("msme_udyam_registration_no", ""),
            human_intervention=validated_data["human_intervention"],
            verification_status=status,
        )

        # 5️⃣ SEND EMAIL
        if status == "SUCCESS":
            EmailService.send_registration_success_email(user, company)
        else:
            EmailService.send_registration_pending_email(user, company)

        return {
            "user": user,
            "company": company,
            "verification_status": status
        }
