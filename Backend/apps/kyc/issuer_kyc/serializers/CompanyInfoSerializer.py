from rest_framework import serializers
from datetime import datetime
from io import BytesIO
from PIL import Image
import re
import pytesseract
from ..models.CompanyInformationModel import CompanyInformation,CompanyOnboardingApplication
from django.core.files.base import ContentFile
import uuid

class CompanyInfoSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=False)
    corporate_identification_number = serializers.CharField(max_length=21)
    company_name = serializers.CharField(max_length=255)
    date_of_incorporation = serializers.DateField()
    place_of_incorporation = serializers.CharField(max_length=100)
    state_of_incorporation = serializers.CharField(max_length=100)
    entity_type = serializers.CharField(max_length=50)
    company_or_individual_pan_card_file = serializers.FileField(required=True)
    gstin = serializers.CharField(max_length=15)
    msme_udyam_registration_no = serializers.CharField(
        max_length=50, required=False, allow_blank=True
    )

    # PAN details: extracted OR manually overridden
    company_pan_number = serializers.CharField(max_length=10, required=False, allow_blank=True)
    pan_holder_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)

    # ---------------- VALIDATIONS ---------------- #

    def validate_company_or_individual_pan_card_file(self, value):
        """Ensure uploaded file is a valid image or PDF."""
        if not value.name.lower().endswith((".jpg", ".jpeg", ".png", ".pdf")):
            raise serializers.ValidationError("Only image or PDF files are allowed for PAN upload.")
        return value

    def validate(self, attrs):
        """Validate CIN and GSTIN uniqueness before saving."""
        cin = attrs.get("corporate_identification_number")
        gstin = attrs.get("gstin")

        # ✅ Check for duplicate CIN
        if CompanyInformation.objects.filter(corporate_identification_number=cin).exists():
            raise serializers.ValidationError(
                {"corporate_identification_number": "This Corporate Identification Number (CIN) is already registered."}
            )

        # ✅ Check for duplicate GSTIN
        if CompanyInformation.objects.filter(gstin=gstin).exists():
            raise serializers.ValidationError(
                {"gstin": "This GSTIN number is already registered with another company."}
            )

        return attrs

    # ---------------- OCR EXTRACTION ---------------- #

    def extract_pan_details(self, file_bytes):
        """Extract PAN details from the uploaded file using OCR."""
        try:
            img = Image.open(BytesIO(file_bytes))
            text = pytesseract.image_to_string(img).upper()
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            # Extract PAN number and DOB
            pan_match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", text)
            dob_match = re.search(r"\d{2}/\d{2}/\d{4}", text)

            pan_number = pan_match.group(0) if pan_match else None
            dob = (
                datetime.strptime(dob_match.group(0), "%d/%m/%Y").date()
                if dob_match
                else None
            )

            # Try to find name line
            name_line = None
            for i, line in enumerate(lines):
                if "नाम" in line or "NAME" in line:
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if not any(
                            k in next_line
                            for k in [
                                "FATHER",
                                "INCOME TAX",
                                "GOVT",
                                "PERMANENT ACCOUNT",
                                "DEPARTMENT",
                            ]
                        ):
                            name_line = next_line
                            break

            if not name_line and pan_match:
                for i, line in enumerate(lines):
                    if pan_match.group(0) in line and i > 0:
                        name_line = lines[i - 1]
                        break

            return {
                "pan_number": pan_number,
                "pan_holder_name": name_line,
                "dob": dob,
            }

        except Exception as e:
            print("OCR extraction error:", e)
            return {"pan_number": None, "pan_holder_name": None, "dob": None}

    # ---------------- CREATE LOGIC ---------------- #

    def create(self, validated_data):
        """Create CompanyInformation with extracted or manually overridden PAN data."""
        user = self.context["request"].user
        file = validated_data.pop("company_or_individual_pan_card_file", None)

        if not file:
            raise serializers.ValidationError(
                {"company_or_individual_pan_card_file": "PAN card upload is required."}
            )

        # Step 1: Extract PAN details using OCR
        file_bytes = file.read()
        extracted = self.extract_pan_details(file_bytes)

        # Step 2: If user provided manual fields, override the extracted ones
        manual_pan = validated_data.pop("company_pan_number", None)
        manual_name = validated_data.pop("pan_holder_name", None)
        manual_dob = validated_data.pop("date_of_birth", None)

        company_pan_number = manual_pan or extracted["pan_number"]
        pan_holder_name = manual_name or extracted["pan_holder_name"]
        date_of_birth = manual_dob or extracted["dob"]

        # Step 3: Validate PAN number is found (either from OCR or manual)
        if not company_pan_number:
            raise serializers.ValidationError(
                {"company_pan_number": "PAN number could not be extracted or entered manually."}
            )

        # Step 4: Prevent duplicate PANs
        if CompanyInformation.objects.filter(company_pan_number=company_pan_number).exists():
            raise serializers.ValidationError(
                {"company_pan_number": "This PAN number is already registered with another company."}
            )

        # Step 5: Save the PAN file
        filename = f"pan_{uuid.uuid4().hex}.pdf"
        file_obj = ContentFile(file_bytes, name=filename)

        # Step 6: Create CompanyInformation record
        company_info = CompanyInformation.objects.create(
            user=user,
            company_or_individual_pan_card_file=file_obj,
            company_pan_number=company_pan_number,
            pan_holder_name=pan_holder_name,
            date_of_birth=date_of_birth,
            **validated_data,
        )

        # Step 7: Update onboarding application
        onboarding_app, created = CompanyOnboardingApplication.objects.get_or_create(
            user=user,
            defaults={
                "status": "IN_PROGRESS",
                "last_accessed_step": 1,
                "company_information": company_info,
                "step_completion": {},
            },
        )

        step_completion = onboarding_app.step_completion or {}
        step_completion["1"] = {
            "completed": True,
            "record_id": str(company_info.company_id),
        }
        onboarding_app.step_completion = step_completion
        onboarding_app.company_information = company_info
        onboarding_app.save(update_fields=["step_completion", "company_information"])

        return {
            "company_id": company_info.company_id,
            "company_name": company_info.company_name,
            "company_pan_number": company_info.company_pan_number,
            "pan_holder_name": company_info.pan_holder_name,
            "date_of_birth": company_info.date_of_birth,
            "message": "Company information and PAN details saved successfully.",
        }

# class CompanyInfoSerializer(serializers.Serializer):
#     user_id = serializers.IntegerField(required=False)
#     corporate_identification_number = serializers.CharField(max_length=21)
#     company_name = serializers.CharField(max_length=255)
#     date_of_incorporation = serializers.DateField()
#     place_of_incorporation = serializers.CharField(max_length=100)
#     state_of_incorporation = serializers.CharField(max_length=100)
#     entity_type = serializers.CharField(max_length=50)
#     company_or_individual_pan_card_file = serializers.FileField()
#     gstin = serializers.CharField(max_length=15)
#     msme_udyam_registration_no = serializers.CharField(
#         max_length=50, required=False, allow_blank=True
#     )

#     # Extracted PAN details
#     company_pan_number = serializers.CharField(max_length=10, read_only=True)
#     pan_holder_name = serializers.CharField(max_length=255, read_only=True)
#     date_of_birth = serializers.DateField(read_only=True)

#     def validate_company_or_individual_pan_card_file(self, value):
#         """Ensure uploaded file is a valid image or PDF."""
#         if not value.name.lower().endswith((".jpg", ".jpeg", ".png", ".pdf")):
#             raise serializers.ValidationError(
#                 "Only image or PDF files are allowed for PAN upload."
#             )
#         return value

#     def extract_pan_details(self, file_bytes):
#         """
#         Extract PAN details using OCR — detect name via 'नाम/Name' marker.
#         """
#         try:
#             img = Image.open(BytesIO(file_bytes))
#             text = pytesseract.image_to_string(img).upper()
#             lines = [l.strip() for l in text.splitlines() if l.strip()]

#             # Extract PAN number and DOB
#             pan_match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", text)
#             dob_match = re.search(r"\d{2}/\d{2}/\d{4}", text)

#             pan_number = pan_match.group(0) if pan_match else None
#             dob = (
#                 datetime.strptime(dob_match.group(0), "%d/%m/%Y").date()
#                 if dob_match
#                 else None
#             )

#             name_line = None

#             # Step 1: Try to find 'नाम/NAME' and extract the next line as the holder's name
#             for i, line in enumerate(lines):
#                 if "नाम" in line or "NAME" in line:
#                     if i + 1 < len(lines):
#                         next_line = lines[i + 1].strip()
#                         if not any(
#                             k in next_line
#                             for k in [
#                                 "FATHER",
#                                 "INCOME TAX",
#                                 "GOVT",
#                                 "PERMANENT ACCOUNT",
#                                 "DEPARTMENT",
#                             ]
#                         ):
#                             name_line = next_line
#                             break

#             # Step 2: If still not found, fallback to older logic (line above PAN number)
#             if not name_line and pan_match:
#                 for i, line in enumerate(lines):
#                     if pan_match.group(0) in line and i > 0:
#                         name_line = lines[i - 1]
#                         break

#             return {
#                 "pan_number": pan_number,
#                 "pan_holder_name": name_line,
#                 "dob": dob,
#             }

#         except Exception as e:
#             print("OCR extraction error:", e)
#             return {
#                 "pan_number": None,
#                 "pan_holder_name": None,
#                 "dob": None,
#             }

#     def create(self, validated_data):
#         """Create a CompanyInformation record with OCR auto-fill."""
#         user = self.context["request"].user
#         file = validated_data.pop("company_or_individual_pan_card_file", None)

#         if not file:
#             raise serializers.ValidationError(
#                 {"company_or_individual_pan_card_file": "PAN card upload is required."}
#             )

#         # Extract details via OCR
#         file_bytes = file.read()
#         extracted = self.extract_pan_details(file_bytes)

#         if not extracted["pan_number"]:
#             raise serializers.ValidationError(
#                 {
#                     "company_or_individual_pan_card_file": "PAN number could not be extracted. Please upload a clearer image."
#                 }
#             )

#         # Prevent duplicate PAN
#         if CompanyInformation.objects.filter(
#             company_pan_number=extracted["pan_number"]
#         ).exists():
#             raise serializers.ValidationError(
#                 {
#                     "company_or_individual_pan_card_file": "This PAN number is already registered with another company."
#                 }
#             )

#         # Save PAN file
#         filename = f"pan_{uuid.uuid4().hex}.pdf"
#         file_obj = ContentFile(file_bytes, name=filename)

#         # Create company record
#         company_info = CompanyInformation.objects.create(
#             user=user,
#             company_or_individual_pan_card_file=file_obj,
#             company_pan_number=extracted["pan_number"],
#             pan_holder_name=extracted["pan_holder_name"],
#             date_of_birth=extracted["dob"],
#             **validated_data,
#         )

#         # Create or update onboarding record
#         onboarding_app, created = CompanyOnboardingApplication.objects.get_or_create(
#             user=user,
#             defaults={
#                 "status": "IN_PROGRESS",
#                 "last_accessed_step": 1,
#                 "company_information": company_info,
#                 "step_completion": {},
#             },
#         )

#         # ✅ Fix: safely mark step complete without relying on a missing model method
#         step_completion = onboarding_app.step_completion or {}
#         step_completion["1"] = {
#             "completed": True,
#             "record_id": str(company_info.company_id),
#         }
#         onboarding_app.step_completion = step_completion
#         onboarding_app.company_information = company_info
#         onboarding_app.save(update_fields=["step_completion", "company_information"])

#         # Return extracted + saved info
#         return {
#             "company_id": company_info.company_id,
#             "company_name": company_info.company_name,
#             "company_pan_number": company_info.company_pan_number,
#             "pan_holder_name": company_info.pan_holder_name,
#             "date_of_birth": company_info.date_of_birth,
#             "message": "Company information and PAN details saved successfully.",
#         }
    


class PanExtractionSerializer(serializers.Serializer):
    """Serializer to extract PAN details (PAN number, Name, DOB) from uploaded PAN card."""
    pan_card_file = serializers.FileField()
    pan_number = serializers.CharField(max_length=10, read_only=True)
    pan_holder_name = serializers.CharField(max_length=255, read_only=True)
    date_of_birth = serializers.DateField(read_only=True)

    def validate_pan_card_file(self, value):
        """Ensure uploaded file is a valid image or PDF."""
        if not value.name.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
            raise serializers.ValidationError("Only image or PDF files are allowed for PAN upload.")
        return value

    def extract_pan_details(self, file_bytes):
        """
        Extract PAN details using OCR — detect name via 'नाम/Name' marker.
        """
        try:
            img = Image.open(BytesIO(file_bytes))
            text = pytesseract.image_to_string(img).upper()
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            # Extract PAN number and DOB
            pan_match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", text)
            dob_match = re.search(r"\d{2}/\d{2}/\d{4}", text)

            pan_number = pan_match.group(0) if pan_match else None
            dob = (
                datetime.strptime(dob_match.group(0), "%d/%m/%Y").date()
                if dob_match
                else None
            )

            name_line = None

            # Step 1: Try to find 'नाम/NAME' and extract the next line as the holder's name
            for i, line in enumerate(lines):
                if "नाम" in line or "NAME" in line:
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        # Avoid capturing labels or headers
                        if not any(
                            k in next_line
                            for k in [
                                "FATHER",
                                "INCOME TAX",
                                "GOVT",
                                "PERMANENT ACCOUNT",
                                "DEPARTMENT",
                            ]
                        ):
                            name_line = next_line
                            break

            # Step 2: If still not found, fallback to older logic (line above PAN number)
            if not name_line and pan_match:
                for i, line in enumerate(lines):
                    if pan_match.group(0) in line and i > 0:
                        name_line = lines[i - 1]
                        break

            return {
                "pan_number": pan_number,
                "pan_holder_name": name_line,
                "date_of_birth": dob,
            }

        except Exception as e:
            print("OCR extraction error:", e)
            return {
                "pan_number": None,
                "pan_holder_name": None,
                "date_of_birth": None,
            }

    def create(self, validated_data):
        """Only perform OCR and return extracted details."""
        file = validated_data.get("pan_card_file")
        file_bytes = file.read()

        extracted = self.extract_pan_details(file_bytes)

        if not extracted["pan_number"]:
            raise serializers.ValidationError({
                "pan_card_file": "Could not extract PAN number. Please upload a clearer image."
            })

        return extracted
    

class CompanyInfoGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyInformation
        fields = [
            "company_id",
            "user",
            "corporate_identification_number",
            "company_name",
            "date_of_incorporation",
            "place_of_incorporation",
            "state_of_incorporation",
            "entity_type",
            "company_or_individual_pan_card_file",
            "gstin",
            "msme_udyam_registration_no",
            "company_pan_number",
            "pan_holder_name",
            "date_of_birth",
        ]
        read_only_fields = fields


class CompanyInfoUpdateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=False)
    corporate_identification_number = serializers.CharField(max_length=21, required=False)
    company_name = serializers.CharField(max_length=255, required=False)
    date_of_incorporation = serializers.DateField(required=False)
    place_of_incorporation = serializers.CharField(max_length=100, required=False)
    state_of_incorporation = serializers.CharField(max_length=100, required=False)
    entity_type = serializers.CharField(max_length=50, required=False)
    company_or_individual_pan_card_file = serializers.FileField(required=False)
    gstin = serializers.CharField(max_length=15, required=False)
    msme_udyam_registration_no = serializers.CharField(max_length=50, required=False, allow_blank=True)

    company_pan_number = serializers.CharField(max_length=10, required=False)
    pan_holder_name = serializers.CharField(max_length=255, required=False)
    date_of_birth = serializers.DateField(required=False)

    # ---------------- VALIDATIONS ---------------- #

    def validate_company_or_individual_pan_card_file(self, value):
        """Ensure uploaded file is a valid image or PDF."""
        if not value.name.lower().endswith((".jpg", ".jpeg", ".png", ".pdf")):
            raise serializers.ValidationError("Only image or PDF files are allowed for PAN upload.")
        return value

    def validate(self, attrs):
        """Validate CIN and GSTIN — allow if same company, reject if used by another."""
        request = self.context.get("request")
        company_instance = self.instance  # the company being updated

        cin = attrs.get("corporate_identification_number")
        gstin = attrs.get("gstin")

        # ✅ Check CIN duplicates (ignore same company)
        if cin:
            existing_cin = CompanyInformation.objects.filter(
                corporate_identification_number__iexact=cin
            ).exclude(company_id=company_instance.company_id)
            if existing_cin.exists():
                raise serializers.ValidationError(
                    {"corporate_identification_number": "This Corporate Identification Number (CIN) is already registered with another company."}
                )

        # ✅ Check GSTIN duplicates (ignore same company)
        if gstin:
            existing_gstin = CompanyInformation.objects.filter(
                gstin__iexact=gstin
            ).exclude(company_id=company_instance.company_id)
            if existing_gstin.exists():
                raise serializers.ValidationError(
                    {"gstin": "This GSTIN number is already registered with another company."}
                )

        return attrs

    # ---------------- PAN EXTRACTION ---------------- #

    def extract_pan_details(self, file_bytes):
        """Extract PAN details using OCR."""
        try:
            img = Image.open(BytesIO(file_bytes))
            text = pytesseract.image_to_string(img).upper()
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            pan_match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", text)
            dob_match = re.search(r"\d{2}/\d{2}/\d{4}", text)
            pan_number = pan_match.group(0) if pan_match else None
            dob = datetime.strptime(dob_match.group(0), "%d/%m/%Y").date() if dob_match else None

            name_line = None
            for i, line in enumerate(lines):
                if "नाम" in line or "NAME" in line:
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if not any(
                            k in next_line
                            for k in ["FATHER", "INCOME TAX", "GOVT", "PERMANENT ACCOUNT", "DEPARTMENT"]
                        ):
                            name_line = next_line
                            break

            # Fallback: line above PAN
            if not name_line and pan_match:
                for i, line in enumerate(lines):
                    if pan_match.group(0) in line and i > 0:
                        name_line = lines[i - 1]
                        break

            return {
                "pan_number": pan_number,
                "pan_holder_name": name_line,
                "dob": dob,
            }

        except Exception as e:
            print("OCR extraction error:", e)
            return {"pan_number": None, "pan_holder_name": None, "dob": None}

    # ---------------- UPDATE LOGIC ---------------- #

    def update(self, instance, validated_data):
        """Update company info (supports PAN re-upload with OCR)."""
        user = self.context["request"].user

        # Handle PAN re-upload
        pan_file = validated_data.pop("company_or_individual_pan_card_file", None)
        if pan_file:
            file_bytes = pan_file.read()
            extracted = self.extract_pan_details(file_bytes)

            if not extracted["pan_number"]:
                raise serializers.ValidationError(
                    {"company_or_individual_pan_card_file": "PAN number could not be extracted. Please upload a clearer image."}
                )

            # Prevent duplicate PAN (excluding current company)
            if CompanyInformation.objects.filter(
                company_pan_number=extracted["pan_number"]
            ).exclude(company_id=instance.company_id).exists():
                raise serializers.ValidationError(
                    {"company_or_individual_pan_card_file": "This PAN number is already registered with another company."}
                )

            filename = f"pan_{uuid.uuid4().hex}.pdf"
            file_obj = ContentFile(file_bytes, name=filename)

            instance.company_or_individual_pan_card_file = file_obj
            instance.company_pan_number = extracted["pan_number"]
            instance.pan_holder_name = extracted["pan_holder_name"]
            instance.date_of_birth = extracted["dob"]

        # ✅ Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # ✅ Update onboarding progress (Step 1)
        onboarding_app, _ = CompanyOnboardingApplication.objects.get_or_create(
            user=user,
            defaults={
                "status": "IN_PROGRESS",
                "last_accessed_step": 1,
                "company_information": instance,
                "step_completion": {},
            },
        )

        step_completion = onboarding_app.step_completion or {}
        step_completion["1"] = {"completed": True, "record_id": str(instance.company_id)}
        onboarding_app.step_completion = step_completion
        onboarding_app.company_information = instance
        onboarding_app.save(update_fields=["step_completion", "company_information"])

        return {
            "company_id": instance.company_id,
            "company_name": instance.company_name,
            "company_pan_number": instance.company_pan_number,
            "pan_holder_name": instance.pan_holder_name,
            "date_of_birth": instance.date_of_birth,
            "message": "Company information updated successfully.",
        }




# class CompanyInfoUpdateSerializer(serializers.Serializer):
#     user_id = serializers.IntegerField(required=False)
#     corporate_identification_number = serializers.CharField(max_length=21, required=False)
#     company_name = serializers.CharField(max_length=255, required=False)
#     date_of_incorporation = serializers.DateField(required=False)
#     place_of_incorporation = serializers.CharField(max_length=100, required=False)
#     state_of_incorporation = serializers.CharField(max_length=100, required=False)
#     entity_type = serializers.CharField(max_length=50, required=False)
#     company_or_individual_pan_card_file = serializers.FileField(required=False)
#     gstin = serializers.CharField(max_length=15, required=False)
#     msme_udyam_registration_no = serializers.CharField(
#         max_length=50, required=False, allow_blank=True
#     )

#     # PAN details: extracted or overridden manually
#     company_pan_number = serializers.CharField(max_length=10, required=False, allow_blank=True)
#     pan_holder_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
#     date_of_birth = serializers.DateField(required=False, allow_null=True)

#     def validate_company_or_individual_pan_card_file(self, value):
#         """Ensure uploaded file is a valid image or PDF."""
#         if value and not value.name.lower().endswith((".jpg", ".jpeg", ".png", ".pdf")):
#             raise serializers.ValidationError("Only image or PDF files are allowed for PAN upload.")
#         return value

#     def extract_pan_details(self, file_bytes):
#         """Extract PAN details using OCR."""
#         try:
#             img = Image.open(BytesIO(file_bytes))
#             text = pytesseract.image_to_string(img).upper()
#             lines = [l.strip() for l in text.splitlines() if l.strip()]

#             # Extract PAN number and DOB
#             pan_match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", text)
#             dob_match = re.search(r"\d{2}/\d{2}/\d{4}", text)

#             pan_number = pan_match.group(0) if pan_match else None
#             dob = (
#                 datetime.strptime(dob_match.group(0), "%d/%m/%Y").date()
#                 if dob_match
#                 else None
#             )

#             # Extract name
#             name_line = None
#             for i, line in enumerate(lines):
#                 if "नाम" in line or "NAME" in line:
#                     if i + 1 < len(lines):
#                         next_line = lines[i + 1].strip()
#                         if not any(
#                             k in next_line
#                             for k in [
#                                 "FATHER",
#                                 "INCOME TAX",
#                                 "GOVT",
#                                 "PERMANENT ACCOUNT",
#                                 "DEPARTMENT",
#                             ]
#                         ):
#                             name_line = next_line
#                             break

#             # Fallback: line above PAN
#             if not name_line and pan_match:
#                 for i, line in enumerate(lines):
#                     if pan_match.group(0) in line and i > 0:
#                         name_line = lines[i - 1]
#                         break

#             return {
#                 "pan_number": pan_number,
#                 "pan_holder_name": name_line,
#                 "dob": dob,
#             }

#         except Exception as e:
#             print("OCR extraction error:", e)
#             return {"pan_number": None, "pan_holder_name": None, "dob": None}

#     def update(self, instance, validated_data):
#         """Update company info (supports PAN re-upload and manual correction)."""
#         user = self.context["request"].user

#         # Extract manual fields if provided
#         manual_pan = validated_data.pop("company_pan_number", None)
#         manual_name = validated_data.pop("pan_holder_name", None)
#         manual_dob = validated_data.pop("date_of_birth", None)

#         # Handle PAN re-upload
#         pan_file = validated_data.pop("company_or_individual_pan_card_file", None)
#         if pan_file:
#             file_bytes = pan_file.read()
#             extracted = self.extract_pan_details(file_bytes)

#             # Apply manual overrides
#             pan_number = manual_pan or extracted["pan_number"]
#             pan_holder_name = manual_name or extracted["pan_holder_name"]
#             dob = manual_dob or extracted["dob"]

#             if not pan_number:
#                 raise serializers.ValidationError(
#                     {
#                         "company_or_individual_pan_card_file": "PAN number could not be extracted or entered manually."
#                     }
#                 )

#             # Prevent duplicate PAN (excluding current record)
#             if CompanyInformation.objects.filter(
#                 company_pan_number=pan_number
#             ).exclude(company_id=instance.company_id).exists():
#                 raise serializers.ValidationError(
#                     {"company_pan_number": "This PAN number is already registered with another company."}
#                 )

#             # Save new PAN file
#             filename = f"pan_{uuid.uuid4().hex}.pdf"
#             file_obj = ContentFile(file_bytes, name=filename)

#             instance.company_or_individual_pan_card_file = file_obj
#             instance.company_pan_number = pan_number
#             instance.pan_holder_name = pan_holder_name
#             instance.date_of_birth = dob

#         else:
#             # No new file uploaded — only update manual PAN fields if provided
#             if manual_pan:
#                 instance.company_pan_number = manual_pan
#             if manual_name:
#                 instance.pan_holder_name = manual_name
#             if manual_dob:
#                 instance.date_of_birth = manual_dob

#         # Update all other company fields
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)

#         instance.save()

#         # Update onboarding app progress
#         onboarding_app, _ = CompanyOnboardingApplication.objects.get_or_create(
#             user=user,
#             defaults={
#                 "status": "IN_PROGRESS",
#                 "last_accessed_step": 1,
#                 "company_information": instance,
#                 "step_completion": {},
#             },
#         )

#         step_completion = onboarding_app.step_completion or {}
#         step_completion["1"] = {"completed": True, "record_id": str(instance.company_id)}
#         onboarding_app.step_completion = step_completion
#         onboarding_app.company_information = instance
#         onboarding_app.save(update_fields=["step_completion", "company_information"])

#         return {
#             "company_id": instance.company_id,
#             "company_name": instance.company_name,
#             "company_pan_number": instance.company_pan_number,
#             "pan_holder_name": instance.pan_holder_name,
#             "date_of_birth": instance.date_of_birth,
#             "message": "Company information updated successfully.",
#         }
            
            

            








    
  