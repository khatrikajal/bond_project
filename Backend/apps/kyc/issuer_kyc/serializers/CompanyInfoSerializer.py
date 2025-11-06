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
    company_or_individual_pan_card_file = serializers.FileField()
    gstin = serializers.CharField(max_length=15)
    msme_udyam_registration_no = serializers.CharField(max_length=50, required=False, allow_blank=True)

    # extracted data of pan
    company_pan_number = serializers.CharField(max_length=10, read_only=True)
    pan_holder_name = serializers.CharField(max_length=255, read_only=True) 
    date_of_birth = serializers.DateField(read_only=True)

    def validate_company_or_individual_pan_card_file(seld,value):
        """Ensure uploaded file is a valid image or PDF.""" 
        if not value.name.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
             raise serializers.ValidationError("Only image or PDF files are allowed for PAN upload.")
        return value
    def extract_pan_details(self,file_bytes):
        try:
            img = Image.open(BytesIO(file_bytes))
            text = pytesseract.image_to_string(img).upper()
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            pan_match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", text)
            dob_match = re.search(r"\d{2}/\d{2}/\d{4}", text)

            pan_number = pan_match.group(0) if pan_match else None
            dob = (
                datetime.strptime(dob_match.group(0), "%d/%m/%Y").date()
                if dob_match
                else None
            )
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
            return {
                "pan_number": None,
                "pan_holder_name": None,
                "dob": None,
            }



    
    # def extract_pan_details(self, file_bytes):
    #     """Extract PAN details using OCR."""
    #     try:
    #         img = Image.open(BytesIO(file_bytes))
    #         text = pytesseract.image_to_string(img).upper()

    #         pan_match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", text) 
    #         dob_match = re.search(r"\d{2}/\d{2}/\d{4}", text)

    #         name_line = ""

    #         if pan_match:
    #             lines = [l.strip() for l in text.splitlines() if l.strip()]
    #             for i, line in enumerate(lines):
    #                 if pan_match.group(0) in line and i > 0:
    #                     name_line = lines[i - 1]
    #                     break

    #         return {
    #              "pan_number": pan_match.group(0) 
    #              if pan_match else None, 
    #              "pan_holder_name": name_line,
    #                "dob": datetime.strptime(dob_match.group(0), "%d/%m/%Y").date() if dob_match else None, }
    #     except Exception as e:
    #         print("OCR extraction error:", e)
    #         return {"pan_number": None, "pan_holder_name": None, "dob": None}
        
    def create(self, validated_data):
        """Create a CompanyInformation record with OCR auto-fill."""
        user = self.context['request'].user
        file = validated_data.pop("company_or_individual_pan_card_file", None)

        


        if not file:
            raise serializers.ValidationError({"company_or_individual_pan_card_file": "PAN card upload is required."})
        
        
        file_bytes = file.read()
        extracted = self.extract_pan_details(file_bytes)
        if not extracted["pan_number"]:
           

           raise serializers.ValidationError({
            "company_or_individual_pan_card_file": "PAN number could not be extracted. Please upload a clearer image."
        })

        if CompanyInformation.objects.filter(company_pan_number=extracted["pan_number"]).exists():
            raise serializers.ValidationError({
                "company_or_individual_pan_card_file": "This PAN number is already registered with another company."
            })
        filename = f"pan_{uuid.uuid4().hex}.pdf" 
        file_obj = ContentFile(file_bytes, name=filename)

        company_info = CompanyInformation.objects.create(
            user=user,
            company_or_individual_pan_card_file=file_obj,
            company_pan_number=extracted["pan_number"],
            pan_holder_name=extracted["pan_holder_name"],
            date_of_birth=extracted["dob"],
            **validated_data
        )

        onboarding_app, created = CompanyOnboardingApplication.objects.get_or_create(
            user=user,
            defaults={
                "status": "IN_PROGRESS",
                'last_accessed_step':1,
                # "current_step": 1,
                "company_information": company_info,
                "step_completion": {},
            }
        )
        onboarding_app.mark_step_complete(step=1, record_id=str(company_info.company_id))
        onboarding_app.company_information = company_info
        onboarding_app.save()
        return { 
            "company_id": company_info.company_id,
              "company_name": company_info.company_name,
                "company_pan_number": company_info.company_pan_number,
                  "pan_holder_name": company_info.pan_holder_name,
                    "date_of_birth": company_info.date_of_birth,
                      "message": "Company information and PAN details saved successfully." }
    



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




    
  