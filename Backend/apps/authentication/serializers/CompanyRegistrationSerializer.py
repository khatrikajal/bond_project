# apps/authentication/serializers/CompanyRegistrationSerializer.py

from rest_framework import serializers
from django.db import transaction
from apps.authentication.issureauth.models import User
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from apps.authentication.services.EmailService import EmailService


class CompanyRegistrationSerializer(serializers.Serializer):
    """
    Final Registration Step:
    Creates User + CompanyInformation with human_intervention flag logic.
    """

    # ---------- USER FIELDS ----------
    mobile_number = serializers.CharField(max_length=15)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6)
    role = serializers.CharField()

    # ---------- COMPANY FIELDS ----------
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

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------
    def validate(self, attrs):
        mobile = attrs.get("mobile_number")
        email = attrs.get("email")

        # Normalize mobile → +91XXXXXXXXXX
        if mobile.startswith("+91"):
            formatted_mobile = mobile
        else:
            formatted_mobile = "+91" + mobile[-10:]

        # ---------------------------- MOBILE VERIFIED CHECK ----------------------------
        if not User.objects.filter(
            mobile_number=formatted_mobile,
            mobile_verified=True,
            is_del=0
        ).exists():
            raise serializers.ValidationError({
                "non_field_errors": ["Mobile number is not verified"]
            })

        # ---------------------------- EMAIL VERIFIED CHECK ----------------------------
        if not User.objects.filter(
            email=email,
            email_verified=True,
            is_del=0
        ).exists():
            raise serializers.ValidationError({
                "non_field_errors": ["Email is not verified"]
            })

        # ---------------------------- PAN HOLDER VALIDATION ----------------------------
        pan_holder_name = attrs.get("pan_holder_name", "").lower()
        company_name = attrs.get("company_name", "").lower()

        if pan_holder_name not in company_name:
            raise serializers.ValidationError({
                "non_field_errors": ["PAN Holder Name does not match Company Name"]
            })

        return attrs

    # ------------------------------------------------------------------
    # CREATE USER + COMPANY USING TRANSACTION
    # ------------------------------------------------------------------
    @transaction.atomic
    def create(self, validated_data):
        formatted_mobile = validated_data["mobile_number"]
        if not formatted_mobile.startswith("+91"):
            formatted_mobile = "+91" + formatted_mobile[-10:]

        # ---------------------------- GET VERIFIED USER ----------------------------
        user = User.objects.get(
            mobile_number=formatted_mobile,
            email=validated_data["email"],
            is_del=0
        )

        # Update password & role
        user.set_password(validated_data["password"])
        user.role = validated_data["role"]
        user.mobile_verified = True
        user.email_verified = True
        user.save()

        # ---------------------------- COMPANY VERIFICATION STATUS ----------------------------
        human_intervention = validated_data["human_intervention"]
        verification_status = "PENDING" if human_intervention else "SUCCESS"

        # ---------------------------- CREATE COMPANY ----------------------------
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
            human_intervention=human_intervention,
            verification_status=verification_status,
        )

        # ---------------------------- SEND EMAIL NOTIFICATION ----------------------------
        if verification_status == "SUCCESS":
            EmailService.send_registration_success_email(user, company)
        else:
            EmailService.send_registration_pending_email(user, company)

        return {
            "user": user,
            "company": company,
            "verification_status": verification_status
        }




# with session

# from rest_framework import serializers
# from django.db import transaction
# from apps.authentication.issureauth.models import User
# from apps.authentication.services.session_manager import VerificationSession
# from apps.authentication.services.EmailService import EmailService
# from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
# from apps.kyc.issuer_kyc.models.TempUploadedFileModel import TempUploadedFile


# class CompanyRegistrationSerializer(serializers.Serializer):
#     """
#     Register user + company.
#     PAN file is taken ONLY from file_token.
#     """

#     # ------------------------ USER FIELDS ------------------------
#     mobile_number = serializers.CharField(max_length=15)
#     email = serializers.EmailField()
#     password = serializers.CharField(min_length=6)
#     role = serializers.CharField()

#     # ------------------------ COMPANY FIELDS ------------------------
#     corporate_identification_number = serializers.CharField(max_length=21)
#     company_name = serializers.CharField(max_length=255)
#     gstin = serializers.CharField(max_length=15)
#     date_of_incorporation = serializers.DateField()

#     city_of_incorporation = serializers.CharField(max_length=100)
#     state_of_incorporation = serializers.CharField(max_length=100)
#     country_of_incorporation = serializers.CharField(max_length=100)

#     entity_type = serializers.ChoiceField(choices=CompanyInformation.COMPANY_TYPE_CHOICES)
#     sector = serializers.CharField(max_length=50)

#     company_pan_number = serializers.CharField(max_length=10)
#     pan_holder_name = serializers.CharField(max_length=255)
#     date_of_birth = serializers.DateField()

#     msme_udyam_registration_no = serializers.CharField(max_length=50)

#     human_intervention = serializers.BooleanField(required=True)

#     # ------------------------ ONLY TOKEN ------------------------
#     file_token = serializers.CharField(required=True)

#     def validate(self, attrs):
#         request = self.context.get("request")

#         # 1. Must have verified mobile + email
#         if not VerificationSession.is_mobile_verified(request):
#             raise serializers.ValidationError({"non_field_errors": ["Mobile number is not verified"]})

#         if not VerificationSession.is_email_verified(request):
#             raise serializers.ValidationError({"non_field_errors": ["Email is not verified"]})

#         # 2. PAN holder name check
#         if attrs["pan_holder_name"].lower() not in attrs["company_name"].lower():
#             raise serializers.ValidationError(
#                 {"non_field_errors": ["PAN holder name must be part of company name"]}
#             )

#         # 3. Single-company rule
#         if User.objects.filter(mobile_number=attrs["mobile_number"]).exists():
#             user = User.objects.get(mobile_number=attrs["mobile_number"])

#             if CompanyInformation.objects.filter(user=user, del_flag=0).exists():
#                 raise serializers.ValidationError(
#                     {"non_field_errors": ["This user has already registered a company."]}
#                 )

#         # 4. Validate file_token
#         token = attrs["file_token"]
#         try:
#             temp = TempUploadedFile.objects.get(file_token=token, is_used=False)
#             attrs["pan_file"] = temp.file
#         except TempUploadedFile.DoesNotExist:
#             raise serializers.ValidationError(
#                 {"file_token": ["Invalid or expired file token"]}
#             )

#         return attrs

#     @transaction.atomic
#     def create(self, validated_data):
#         request = self.context.get("request")

#         # ------------------------ USER ------------------------
#         user = User.objects.create_user(
#             mobile_number=validated_data["mobile_number"],
#             email=validated_data["email"],
#             password=validated_data["password"],
#             role=validated_data["role"]
#         )
#         user.mobile_verified = True
#         user.email_verified = True
#         user.save()

#         # ------------------------ COMPANY ------------------------
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
#             msme_udyam_registration_no=validated_data["msme_udyam_registration_no"],
#             human_intervention=validated_data["human_intervention"],
#             verification_status="PENDING" if validated_data["human_intervention"] else "SUCCESS",
#             company_or_individual_pan_card_file=validated_data["pan_file"]
#         )

#         # ------------------------ Mark Token Used ------------------------
#         TempUploadedFile.objects.filter(file_token=validated_data["file_token"]).update(is_used=True)

#         # ------------------------ Email ------------------------
#         if company.verification_status == "SUCCESS":
#             EmailService.send_registration_success_email(user, company)
#         else:
#             EmailService.send_registration_pending_email(user, company)

#         return {
#             "user": user,
#             "company": company,
#             "verification_status": company.verification_status
#         }
