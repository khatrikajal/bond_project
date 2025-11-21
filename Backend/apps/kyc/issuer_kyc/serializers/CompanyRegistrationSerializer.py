# from rest_framework import serializers
# from django.db import transaction
# from django.core.files.base import File
# from django.conf import settings
# import os

# from apps.authentication.models.UserModel import User
# from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
# from apps.authentication.services.EmailService import EmailService
# from apps.authentication.services.verification_store import VerificationStore


# # -------------------------------------------------------------------
# # Load PAN file from temporary folder
# # -------------------------------------------------------------------
# def load_temp_pan_file(token):
#     file_path = os.path.join(settings.MEDIA_ROOT, "temp_pan", f"{token}.pdf")
#     if not os.path.exists(file_path):
#         return None
#     return open(file_path, "rb")


# class CompanyRegistrationSerializer(serializers.Serializer):
#     """
#     Final Step — Registers User + Creates Company + Saves PAN file + Sends Email
#     """

#     # ------------------ USER FIELDS ------------------
#     mobile_number = serializers.CharField(max_length=15, required=True)
#     email = serializers.EmailField(required=True)
#     password = serializers.CharField(min_length=6, required=True)
#     role = serializers.CharField(required=True)

#     # ------------------ COMPANY FIELDS ------------------
#     corporate_identification_number = serializers.CharField(max_length=21, required=True)
#     company_name = serializers.CharField(max_length=255, required=True)
#     gstin = serializers.CharField(max_length=15, required=True)
#     date_of_incorporation = serializers.DateField(required=True)

#     city_of_incorporation = serializers.CharField(max_length=100, required=True)
#     state_of_incorporation = serializers.CharField(max_length=100, required=True)
#     country_of_incorporation = serializers.CharField(max_length=100, required=True)

#     entity_type = serializers.ChoiceField(
#         choices=CompanyInformation.COMPANY_TYPE_CHOICES,
#         required=True
#     )
#     sector = serializers.CharField(max_length=50, required=True)

#     company_pan_number = serializers.CharField(max_length=10, required=True)
#     pan_holder_name = serializers.CharField(max_length=255, required=True)
#     date_of_birth = serializers.DateField(required=True)

#     msme_udyam_registration_no = serializers.CharField(
#         max_length=50, required=False, allow_blank=True
#     )

#     # ⭐ Required for PAN file
#     file_token = serializers.CharField(required=True)

#     human_intervention = serializers.BooleanField(required=True)

#     # ============================================================
#     # VALIDATION
#     # ============================================================
#     def validate(self, attrs):
#         request = self.context["request"]

#         # 1️⃣ Check required fields
#         required_fields = [
#             "mobile_number", "email", "password", "role",
#             "corporate_identification_number", "company_name", "gstin",
#             "date_of_incorporation", "city_of_incorporation",
#             "state_of_incorporation", "country_of_incorporation",
#             "entity_type", "sector", "company_pan_number",
#             "pan_holder_name", "date_of_birth", "file_token"
#         ]

#         missing = [f for f in required_fields if not attrs.get(f)]
#         if missing:
#             raise serializers.ValidationError({
#                 "non_field_errors": [f"{', '.join(missing)} field(s) are required."]
#             })

#         mobile = attrs["mobile_number"]
#         email = attrs["email"]

#         # 2️⃣ Cache-based mobile verification
#         if not VerificationStore.is_mobile_verified(request, mobile):
#             raise serializers.ValidationError({
#                 "non_field_errors": ["Mobile number is not verified."]
#             })

#         # 3️⃣ Cache-based email verification
#         if not VerificationStore.is_email_verified(request, email):
#             raise serializers.ValidationError({
#                 "non_field_errors": ["Email is not verified."]
#             })

#         # 4️⃣ PAN name match
#         if attrs["pan_holder_name"].lower() not in attrs["company_name"].lower():
#             raise serializers.ValidationError({
#                 "non_field_errors": ["PAN holder name does not match company name."]
#             })

#         # 5️⃣ File token check
#         file_path = os.path.join(settings.MEDIA_ROOT, "temp_pan", f"{attrs['file_token']}.pdf")
#         if not os.path.exists(file_path):
#             raise serializers.ValidationError({
#                 "file_token": ["Invalid or expired file token."]
#             })

#         return attrs

#     # ============================================================
#     # CREATE USER + COMPANY
#     # ============================================================
#     @transaction.atomic
#     def create(self, validated_data):

#         mobile = validated_data["mobile_number"]
#         email = validated_data["email"]

#         # 1️⃣ Duplicate user check
#         if User.objects.filter(mobile_number=mobile).exists():
#             raise serializers.ValidationError({
#                 "non_field_errors": ["User with this mobile number already exists."]
#             })

#         if User.objects.filter(email=email).exists():
#             raise serializers.ValidationError({
#                 "non_field_errors": ["User with this email already exists."]
#             })

#         # 2️⃣ Create User
#         user = User.objects.create_user(
#             mobile_number=mobile,
#             email=email,
#             password=validated_data["password"],
#             role=validated_data["role"]
#         )
#         user.mobile_verified = True
#         user.email_verified = True
#         user.save()

#         # 3️⃣ Determine verification status
#         verification_status = (
#             "PENDING" if validated_data["human_intervention"] else "SUCCESS"
#         )

#         # 4️⃣ Create Company
#         company = CompanyInformation.objects.create(
#             user=user,
#             corporate_identification_number=validated_data["corporate_identification_number"],
#             company_name=validated_data["company_name"],
#             gstin=validated_data["gstin"],
#             date_of_incorporation=validated_data["date_of_incorporation"],
#             city_of_incorporation=validated_data["city_of_incorporation"],
#             state_of_incorporation=validated_data["state_of_incorporation"],
#             country_of_incorporation=validated_data["country_of_incorporation"],
#             entity_type=validated_data["entity_type"],
#             sector=validated_data["sector"],
#             company_pan_number=validated_data["company_pan_number"],
#             pan_holder_name=validated_data["pan_holder_name"],
#             date_of_birth=validated_data["date_of_birth"],
#             msme_udyam_registration_no=validated_data.get("msme_udyam_registration_no", ""),
#             human_intervention=validated_data["human_intervention"],
#             verification_status=verification_status,
#         )

#         # 5️⃣ Save PAN file
#         pan_file = load_temp_pan_file(validated_data["file_token"])
#         if pan_file:
#             company.company_or_individual_pan_card_file.save(
#                 f"{validated_data['company_pan_number']}.pdf",
#                 File(pan_file)
#             )

#         # 6️⃣ Send Registration Email
#         if verification_status == "SUCCESS":
#             EmailService.send_registration_success_email(user, company)
#         else:
#             EmailService.send_registration_pending_email(user, company)

#         # 7️⃣ Return response
#         return {
#             "user": user,
#             "company": company,
#             "verification_status": verification_status
#         }
from rest_framework import serializers
from django.db import transaction
from django.core.files.base import File
from django.conf import settings
import os

from apps.authentication.models.UserModel import User
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from apps.kyc.issuer_kyc.services.EmailService import EmailService
from apps.authentication.models.UserModel import Role
# Import validators
from apps.kyc.issuer_kyc.utils.company_registration_validators import (
    validate_required_fields,
    validate_mobile_verification,
    validate_email_verification,
    validate_pan_name,
    validate_pan_file_token,
    validate_pan_number,
    validate_gstin_format,
    validate_date_of_birth,
    validate_udyam_number,
)


def load_temp_pan_file(token):
    file_path = os.path.join(settings.MEDIA_ROOT, "temp_pan", f"{token}.pdf")
    if not os.path.exists(file_path):
        return None
    return open(file_path, "rb")


class CompanyRegistrationSerializer(serializers.Serializer):

    # USER FIELDS
    mobile_number = serializers.CharField(max_length=15, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(min_length=6, required=True)

    # COMPANY FIELDS
    corporate_identification_number = serializers.CharField(max_length=21, required=True)
    company_name = serializers.CharField(max_length=255, required=True)
    gstin = serializers.CharField(max_length=15, required=True)
    date_of_incorporation = serializers.DateField(required=True)

    city_of_incorporation = serializers.CharField(max_length=100, required=True)
    state_of_incorporation = serializers.CharField(max_length=100, required=True)
    country_of_incorporation = serializers.CharField(max_length=100, required=True)

    entity_type = serializers.ChoiceField(choices=CompanyInformation.COMPANY_TYPE_CHOICES)
    sector = serializers.CharField(max_length=50, required=True)

    company_pan_number = serializers.CharField(max_length=10, required=True)
    pan_holder_name = serializers.CharField(max_length=255, required=True)
    date_of_birth = serializers.DateField(required=True)

    msme_udyam_registration_no = serializers.CharField(
        max_length=50, required=False, allow_blank=True
    )

    file_token = serializers.CharField(required=True)
    human_intervention = serializers.BooleanField(required=True)

    # =================================================================
    # VALIDATION
    # =================================================================
    def validate(self, attrs):
        request = self.context["request"]

        required_fields = [
            "mobile_number", "email", "password",
            "corporate_identification_number", "company_name", "gstin",
            "date_of_incorporation", "city_of_incorporation",
            "state_of_incorporation", "country_of_incorporation",
            "entity_type", "sector", "company_pan_number",
            "pan_holder_name", "date_of_birth", "file_token"
        ]

        # Basic required field validation
        validate_required_fields(attrs, required_fields)

        # OTP verification (cache-based)
        validate_mobile_verification(request, attrs["mobile_number"])
        validate_email_verification(request, attrs["email"])

        # PAN → Company Name strict match
        validate_pan_name(attrs["pan_holder_name"], attrs["company_name"])

        # PAN file token
        validate_pan_file_token(attrs["file_token"])

        # Strict format validations
        validate_pan_number(attrs["company_pan_number"])
        validate_gstin_format(attrs["gstin"])
        validate_date_of_birth(attrs["date_of_birth"])
        validate_udyam_number(attrs.get("msme_udyam_registration_no"))

        return attrs

    # =================================================================
    # CREATE USER + COMPANY
    # =================================================================
    @transaction.atomic
    def create(self, validated_data):

        mobile = validated_data["mobile_number"]
        email = validated_data["email"]

        # Duplicate users
        if User.objects.filter(mobile_number=mobile).exists():
            raise serializers.ValidationError({
                "non_field_errors": ["User with this mobile number already exists."]
            })

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({
                "non_field_errors": ["User with this email already exists."]
            })

        # Create user (default role = ISSUER)
        # Fetch ISSUER role object
        issuer_role = Role.objects.get(name="ISSUER")

        # Create user
        user = User.objects.create_user(
            mobile_number=mobile,
            email=email,
            password=validated_data["password"],
        )

        user.mobile_verified = True
        user.email_verified = True
        user.save()
        # Assign the role (M2M)
        user.roles.add(issuer_role)

        # Verification status
        status = "PENDING" if validated_data["human_intervention"] else "SUCCESS"

        # Create company
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

        # Save PAN file
        pan_file = load_temp_pan_file(validated_data["file_token"])
        if pan_file:
            company.company_or_individual_pan_card_file.save(
                f"{validated_data['company_pan_number']}.pdf",
                File(pan_file)
            )

        # Send email
        if status == "SUCCESS":
            EmailService.send_registration_success_email(user, company)
        else:
            EmailService.send_registration_pending_email(user, company)

        return {
            "user": user,
            "company": company,
            "verification_status": status
        }
