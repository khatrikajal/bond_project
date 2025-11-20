   


import os
import uuid
import re
from datetime import datetime
from io import BytesIO
from PIL import Image
import pytesseract

from rest_framework import serializers
from django.core.files.base import ContentFile
from django.conf import settings

from ..models.CompanyInformationModel import CompanyInformation



# ============================================================
# 🔥 SERVICE: TEMP PAN STORAGE HELPERS
# ============================================================
TEMP_PAN_FOLDER = os.path.join(settings.MEDIA_ROOT, "temp_pan")

if not os.path.exists(TEMP_PAN_FOLDER):
    os.makedirs(TEMP_PAN_FOLDER, exist_ok=True)


def save_temp_pan(file_bytes):
    """Save uploaded PAN temporarily and return token."""
    token = f"TEMP_{uuid.uuid4().hex}"
    file_path = os.path.join(TEMP_PAN_FOLDER, f"{token}.pdf")

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    return token


def load_temp_pan(token):
    """Load temporary PAN file using token."""
    file_path = os.path.join(TEMP_PAN_FOLDER, f"{token}.pdf")

    if not os.path.exists(file_path):
        return None

    with open(file_path, "rb") as f:
        return f.read()

def delete_temp_pan(token):
    file_path = os.path.join(TEMP_PAN_FOLDER, f"{token}.pdf")
    if os.path.exists(file_path):
        os.remove(file_path)



# ============================================================
# 1️⃣ PAN EXTRACTION SERIALIZER  (UPLOAD ONCE)
# ============================================================
class PanExtractionSerializer(serializers.Serializer):
    pan_card_file = serializers.FileField(required=True)

    pan_number = serializers.CharField(read_only=True)
    pan_holder_name = serializers.CharField(read_only=True)
    date_of_birth = serializers.DateField(read_only=True)
    file_token = serializers.CharField(read_only=True)

    def validate_pan_card_file(self, value):
        if not value.name.lower().endswith((".jpg", ".jpeg", ".png", ".pdf")):
            raise serializers.ValidationError("Only image or PDF files allowed.")
        return value

    def extract_pan_details(self, file_bytes):
        try:
            img = Image.open(BytesIO(file_bytes))
            text = pytesseract.image_to_string(img).upper()

            lines = [l.strip() for l in text.splitlines() if l.strip()]

            pan_match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]", text)
            dob_match = re.search(r"\d{2}/\d{2}/\d{4}", text)

            pan_number = pan_match.group(0) if pan_match else None
            dob = datetime.strptime(dob_match.group(0), "%d/%m/%Y").date() if dob_match else None

            name = None
            for i, line in enumerate(lines):
                if "NAME" in line or "नाम" in line:
                    if i + 1 < len(lines):
                        possible = lines[i + 1]
                        if not any(x in possible for x in ["GOVT", "TAX", "INCOME"]):
                            name = possible
                            break

            return {
                "pan_number": pan_number,
                "pan_holder_name": name,
                "date_of_birth": dob,
            }

        except Exception:
            return {"pan_number": None, "pan_holder_name": None, "date_of_birth": None}

    def create(self, validated_data):
        file = validated_data["pan_card_file"]
        file_bytes = file.read()

        extracted = self.extract_pan_details(file_bytes)
        if not extracted["pan_number"]:
            raise serializers.ValidationError("Invalid PAN image. Could not extract PAN number.")

        # Save the PAN file temporarily
        file_token = save_temp_pan(file_bytes)

        return {
            **extracted,
            "file_token": file_token
        }



# ============================================================
# 2️⃣ CREATE COMPANY (FINAL SUBMIT — STRICT CIN VALIDATION)
# ============================================================

# CIN Regex → Accept MCA CIN or Numeric CIN
CIN_REGEX = re.compile(
    r'^([LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}|\d{10,20})$'
)

class CompanyInfoSerializer(serializers.Serializer):
    """Final company creation — expects file_token NOT file."""

    # BASIC FIELDS
    corporate_identification_number = serializers.CharField(max_length=25)
    company_name = serializers.CharField(max_length=255)
    date_of_incorporation = serializers.DateField()

    city_of_incorporation = serializers.CharField(max_length=100)
    state_of_incorporation = serializers.CharField(max_length=100)
    country_of_incorporation = serializers.CharField(max_length=100)
    sector = serializers.CharField(max_length=50)
    entity_type = serializers.CharField(max_length=50)

    gstin = serializers.CharField(max_length=15)
    msme_udyam_registration_no = serializers.CharField(max_length=50, required=False)

    # PAN FIELDS from frontend
    company_pan_number = serializers.CharField(max_length=10)
    pan_holder_name = serializers.CharField(max_length=255)
    date_of_birth = serializers.DateField()

    # TEMP FILE TOKEN
    file_token = serializers.CharField()

    # -------------------------------
    # STRICT CIN VALIDATION ADDED
    # -------------------------------
    def validate_corporate_identification_number(self, value):
        cin = value.strip().upper()

        # enforce correct format
        if not CIN_REGEX.match(cin):
            raise serializers.ValidationError(
                "Invalid CIN format. Must be valid MCA CIN (e.g., L12345MH2001PLC123456) "
                "OR numeric CIN (10–20 digits)."
            )

        if CompanyInformation.active.filter(corporate_identification_number=cin).exists():
            raise serializers.ValidationError("CIN already exists")

        return cin

    def validate(self, attrs):
        # check GSTIN
        gst = attrs["gstin"]
        if CompanyInformation.active.filter(gstin=gst).exists():
            raise serializers.ValidationError({"gstin": "GSTIN already exists"})

        # check PAN
        pan = attrs["company_pan_number"]
        if CompanyInformation.active.filter(company_pan_number=pan).exists():
            raise serializers.ValidationError({"company_pan_number": "PAN already exists"})

        return attrs

    def create(self, validated_data):
        user = self.context["request"].user

        # handle token → fetch stored PAN file
        token = validated_data.pop("file_token")
        file_bytes = load_temp_pan(token)

        if not file_bytes:
            raise serializers.ValidationError("PAN file token expired or invalid.")

        filename = f"pan_{uuid.uuid4().hex}.pdf"
        file_obj = ContentFile(file_bytes, name=filename)

        company = CompanyInformation.objects.create(
            user=user,
            company_or_individual_pan_card_file=file_obj,
            **validated_data
        )

        delete_temp_pan(token)

        return {
            "company_id": company.company_id,
            "company_name": company.company_name,
            "company_pan_number": company.company_pan_number,
            "pan_holder_name": company.pan_holder_name,
            "date_of_birth": company.date_of_birth,
            "message": "Company information saved successfully."
        }

# ============================================================
# 3️⃣ UPDATE SERIALIZER (NO OCR, NO FILE)
# ============================================================
class CompanyInfoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyInformation
        fields = [
            "company_name",
            "city_of_incorporation",
            "state_of_incorporation",
            "country_of_incorporation",
            "sector",
            "gstin",
            "msme_udyam_registration_no",
        ]


class CompanyInfoGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyInformation
        fields = [
            "company_id",
            "user",
            "corporate_identification_number",
            "company_name",
            "date_of_incorporation",
            "city_of_incorporation",
            "state_of_incorporation",
            "country_of_incorporation",
            "sector",
            "entity_type",
            "company_or_individual_pan_card_file",
            "company_pan_number",
            "pan_holder_name",
            "date_of_birth",
            "gstin",
            "msme_udyam_registration_no",
        ]
        read_only_fields = fields
