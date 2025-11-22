import re
import pytesseract
from PIL import Image
from io import BytesIO
from datetime import datetime
from rest_framework import serializers
from django.core.files.base import ContentFile
from apps.kyc.issuer_kyc.models import CompanyInformation, CompanySignatory

from ..utils.extract_files import validate_aadhaar_format,validate_pan_format,extract_aadhaar_from_file,extract_pan_from_file

class CompanySignatoryCreateSerializer(serializers.Serializer):
    """
    Serializer to create a signatory record for a given company.
    PAN and Aadhaar numbers are extracted automatically from uploaded documents using OCR.
    """

    name_of_signatory = serializers.CharField(max_length=255)
    designation = serializers.ChoiceField(choices=CompanySignatory.DESIGNATION_CHOICES)
    din = serializers.CharField(max_length=8)
    email_address = serializers.EmailField(max_length=255)

    # File uploads
    document_file_pan = serializers.FileField()
    document_file_aadhaar = serializers.FileField()
    dsc_upload = serializers.FileField(required=False, allow_null=True)

    # ---------------- VALIDATIONS ---------------- #

    def validate_din(self, value):
        if not re.match(r"^\d{8}$", value):
            raise serializers.ValidationError("DIN must be an 8-digit numeric string.")
        if CompanySignatory.objects.filter(din=value).exists():
            raise serializers.ValidationError("This DIN is already associated with another signatory.")
        return value

    def validate_document_file_pan(self, value):
        """Ensure uploaded PAN file is image or PDF."""
        if not value.name.lower().endswith((".jpg", ".jpeg", ".png", ".pdf")):
            raise serializers.ValidationError("Only image or PDF files allowed for PAN upload.")
        return value

    def validate_document_file_aadhaar(self, value):
        """Ensure uploaded Aadhaar file is image or PDF."""
        if not value.name.lower().endswith((".jpg", ".jpeg", ".png", ".pdf")):
            raise serializers.ValidationError("Only image or PDF files allowed for Aadhaar upload.")
        return value

    # ---------------- CREATE LOGIC ---------------- #

    def create(self, validated_data):
        """Create a new signatory for the given company, with OCR extraction."""
        request = self.context.get("request")
        company_id = self.context.get("company_id")

        # ✅ Verify company ownership
        try:
            company = CompanyInformation.objects.get(company_id=company_id, user=request.user)
        except CompanyInformation.DoesNotExist:
            raise serializers.ValidationError({"company": "Company not found or not accessible."})

        user = request.user

        # ✅ Read uploaded files
        pan_file = validated_data.pop("document_file_pan")
        aadhaar_file = validated_data.pop("document_file_aadhaar")
        dsc_file = validated_data.pop("dsc_upload", None)

        pan_bytes = pan_file.read()
        aadhaar_bytes = aadhaar_file.read()

        # ✅ Use helper functions for OCR extraction
        extracted_pan = extract_pan_from_file(pan_bytes)
        extracted_aadhaar = extract_aadhaar_from_file(aadhaar_bytes)

        # ✅ Validate OCR results
        if not extracted_pan or not validate_pan_format(extracted_pan):
            raise serializers.ValidationError(
                {"document_file_pan": "Unable to extract a valid PAN number. Please upload a clearer file."}
            )

        if not extracted_aadhaar or not validate_aadhaar_format(extracted_aadhaar):
            raise serializers.ValidationError(
                {"document_file_aadhaar": "Unable to extract a valid Aadhaar number. Please upload a clearer file."}
            )

        # ✅ Check for duplicates
        if CompanySignatory.objects.filter(pan_number=extracted_pan).exists():
            raise serializers.ValidationError(
                {"document_file_pan": f"This PAN number ({extracted_pan}) is already registered with another signatory."}
            )

        if CompanySignatory.objects.filter(aadhaar_number=extracted_aadhaar).exists():
            raise serializers.ValidationError(
                {"document_file_aadhaar": f"This Aadhaar number ({extracted_aadhaar}) is already registered with another signatory."}
            )

        # ✅ Save files
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        pan_file_obj = ContentFile(pan_bytes, name=f"pan_{timestamp}.pdf")
        aadhaar_file_obj = ContentFile(aadhaar_bytes, name=f"aadhaar_{timestamp}.pdf")
        dsc_file_obj = ContentFile(dsc_file.read(), name=f"dsc_{timestamp}.pdf") if dsc_file else None

        # ✅ Create signatory record
        signatory = CompanySignatory.objects.create(
            company=company,
            name_of_signatory=validated_data["name_of_signatory"],
            designation=validated_data["designation"],
            din=validated_data["din"],
            pan_number=extracted_pan,
            aadhaar_number=extracted_aadhaar,
            email_address=validated_data["email_address"],
            document_file_pan=pan_file_obj,
            document_file_aadhaar=aadhaar_file_obj,
            dsc_upload=dsc_file_obj,
            user_id_updated_by=user,
        )

        # ✅ Update onboarding (Step 5)
        # onboarding_app, created = CompanyOnboardingApplication.objects.get_or_create(
        #     user=user,
        #     defaults={
        #         "status": "IN_PROGRESS",
        #         "last_accessed_step": 6,
        #         "company_information": company,
        #         "step_completion": {},
        #     },
        # )

        # ✅ Ensure step completion & last_accessed_step update even if record exists
        # step_completion = onboarding_app.step_completion or {}
        # step_completion["6"] = {
        #     "completed": True,
        #     "record_id": str(signatory.signatory_id),
        # }

        # onboarding_app.step_completion = step_completion
        # onboarding_app.company_information = company

        # if not created and onboarding_app.last_accessed_step < 6:
        #     onboarding_app.last_accessed_step = 6

        # onboarding_app.status = "IN_PROGRESS"
        # onboarding_app.save(update_fields=["step_completion", "company_information", "last_accessed_step", "status"])

        # ✅ Return response
        return {
            "signatory_id": signatory.signatory_id,
            "company_id": company.company_id,
            "name_of_signatory": signatory.name_of_signatory,
            "designation": signatory.designation,
            "din": signatory.din,
            "pan_number": signatory.pan_number,
            "aadhaar_number": signatory.aadhaar_number,
            "email_address": signatory.email_address,
            # "last_accessed_step": onboarding_app.last_accessed_step,  # added for clarity
            "message": "Signatory added successfully with extracted PAN/Aadhaar details.",
        }
    
class CompanySignatoryListSerializer(serializers.ModelSerializer):
    """
    Serializer to list all signatories of a company.
    """

    class Meta:
        model = CompanySignatory
        fields = [
            "signatory_id",
            "name_of_signatory",
            "designation",
            "din",
            "pan_number",
            "aadhaar_number",
            "email_address",
            "status",
            "verified",
            "dsc_upload",
            "document_file_pan",
            "document_file_aadhaar",
            "created_at",
            "updated_at",
        ]
    

class CompanySignatoryUpdateSerializer(serializers.Serializer):
    name_of_signatory = serializers.CharField(max_length=100, required=False)
    designation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    din = serializers.CharField(max_length=20, required=False, allow_blank=True)
    pan_number = serializers.CharField(max_length=10, required=False, allow_blank=True)
    aadhaar_number = serializers.CharField(max_length=12, required=False, allow_blank=True)
    email_address = serializers.EmailField(required=False)
    status = serializers.ChoiceField(choices=CompanySignatory.STATUS_CHOICES)
    # serializers.ChoiceField(choices=CompanySignatory.DESIGNATION_CHOICES)
    verified = serializers.BooleanField(required=False)
    dsc_upload = serializers.FileField(required=False, allow_null=True)
    document_file_pan = serializers.FileField(required=False, allow_null=True)
    document_file_aadhaar = serializers.FileField(required=False, allow_null=True)

    # ------------------ VALIDATION ------------------ #
    def validate(self, data):
        instance = self.instance

        # Validate duplicates
        if "pan_number" in data:
            existing = CompanySignatory.objects.filter(
                pan_number=data["pan_number"]
            ).exclude(signatory_id=instance.signatory_id)
            if existing.exists():
                raise serializers.ValidationError({
                    "pan_number": "This PAN number is already registered with another signatory."
                })

        if "aadhaar_number" in data:
            existing = CompanySignatory.objects.filter(
                aadhaar_number=data["aadhaar_number"]
            ).exclude(signatory_id=instance.signatory_id)
            if existing.exists():
                raise serializers.ValidationError({
                    "aadhaar_number": "This Aadhaar number is already registered with another signatory."
                })

        if "din" in data:
            existing = CompanySignatory.objects.filter(
                din=data["din"]
            ).exclude(signatory_id=instance.signatory_id)
            if existing.exists():
                raise serializers.ValidationError({
                    "din": "This DIN is already associated with another signatory."
                })

        return data

    # ------------------ UPDATE ------------------ #
    def update(self, instance, validated_data):
        """Perform signatory update, with OCR extraction + onboarding update."""
        request = self.context["request"]
        user = request.user

        # OCR extraction for PAN
        if "document_file_pan" in validated_data and validated_data["document_file_pan"]:
            pan_file = validated_data.pop("document_file_pan")
            pan_bytes = pan_file.read()
            extracted_pan = extract_pan_from_file(pan_bytes)

            if not extracted_pan or not validate_pan_format(extracted_pan):
                raise serializers.ValidationError({
                    "document_file_pan": "Unable to extract valid PAN number. Please upload a clearer file."
                })

            # Check duplicates
            if CompanySignatory.objects.filter(
                pan_number=extracted_pan
            ).exclude(signatory_id=instance.signatory_id).exists():
                raise serializers.ValidationError({
                    "document_file_pan": f"This PAN number ({extracted_pan}) is already used by another signatory."
                })

            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            pan_filename = f"pan_{timestamp}.pdf"
            instance.document_file_pan = ContentFile(pan_bytes, name=pan_filename)
            instance.pan_number = extracted_pan

        # OCR extraction for Aadhaar
        if "document_file_aadhaar" in validated_data and validated_data["document_file_aadhaar"]:
            aadhaar_file = validated_data.pop("document_file_aadhaar")
            aadhaar_bytes = aadhaar_file.read()
            extracted_aadhaar = extract_aadhaar_from_file(aadhaar_bytes)

            if not extracted_aadhaar or not validate_aadhaar_format(extracted_aadhaar):
                raise serializers.ValidationError({
                    "document_file_aadhaar": "Unable to extract valid Aadhaar number. Please upload a clearer file."
                })

            # Check duplicates
            if CompanySignatory.objects.filter(
                aadhaar_number=extracted_aadhaar
            ).exclude(signatory_id=instance.signatory_id).exists():
                raise serializers.ValidationError({
                    "document_file_aadhaar": f"This Aadhaar number ({extracted_aadhaar}) is already used by another signatory."
                })

            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            aadhaar_filename = f"aadhaar_{timestamp}.pdf"
            instance.document_file_aadhaar = ContentFile(aadhaar_bytes, name=aadhaar_filename)
            instance.aadhaar_number = extracted_aadhaar

        # DSC Upload
        if "dsc_upload" in validated_data and validated_data["dsc_upload"]:
            dsc_file = validated_data.pop("dsc_upload")
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            dsc_filename = f"dsc_{timestamp}.pdf"
            instance.dsc_upload = ContentFile(dsc_file.read(), name=dsc_filename)

        # Normal field updates
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.user_id_updated_by = user
        instance.save()

        # ------------------ UPDATE ONBOARDING STEP ------------------ #
        # try:
        #     onboarding_app, _ = CompanyOnboardingApplication.objects.get_or_create(
        #         user=user,
        #         defaults={
        #             "status": "IN_PROGRESS",
        #             "last_accessed_step": 6,
        #             "company_information": instance.company,
        #             "step_completion": {},
        #         },
        #     )
        #     step_completion = onboarding_app.step_completion or {}
        #     step_completion["6"] = {
        #         "completed": True,
        #         "record_id": str(instance.signatory_id),
        #     }
        #     onboarding_app.step_completion = step_completion
        #     onboarding_app.company_information = instance.company
        #     onboarding_app.save(update_fields=["step_completion", "company_information"])
        # except Exception as e:
        #     print("Onboarding update error:", e)

        # Response
        return {
            "signatory_id": instance.signatory_id,
            "name_of_signatory": instance.name_of_signatory,
            "designation": instance.designation,
            "din": instance.din,
            "pan_number": instance.pan_number,
            "aadhaar_number": instance.aadhaar_number,
            "email_address": instance.email_address,
            "status": instance.status,
            "verified": instance.verified,
            "message": "Signatory details updated successfully with extracted PAN/Aadhaar info.",
        }

class CompanySignatoryStatusUpdateSerializer(serializers.Serializer):
    """Serializer to update signatory status only."""
    status = serializers.ChoiceField(choices=CompanySignatory.STATUS_CHOICES)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        new_status = validated_data.get("status", instance.status)

        instance.status = new_status
        instance.user_id_updated_by = user
        instance.save(update_fields=["status", "user_id_updated_by", "updated_at"])

        return instance



