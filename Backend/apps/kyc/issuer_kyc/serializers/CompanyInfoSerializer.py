from rest_framework import serializers
from datetime import datetime
from io import BytesIO
from PIL import Image
import re
import pytesseract
from ..models.CompanyInformationModel import CompanyInformation






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
    
    def extract_pan_details(self, file_bytes):
        """Extract PAN details using OCR."""
        try:
            image = image.open(BytesIO(file_bytes))
            text = pytesseract.image_to_string(image).upper()

            pan_match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", text) 
            dob_match = re.search(r"\d{2}/\d{2}/\d{4}", text)

            name_line = ""

            if pan_match:
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                for i, line in enumerate(lines):
                    if pan_match.group(0) in line and i > 0:
                        name_line = lines[i - 1]
                        break

            return {
                 "pan_number": pan_match.group(0) 
                 if pan_match else None, 
                 "pan_holder_name": name_line,
                   "dob": datetime.strptime(dob_match.group(0), "%d/%m/%Y").date() if dob_match else None, }
        except Exception as e:
            print("OCR extraction error:", e)
            return {"pan_number": None, "pan_holder_name": None, "dob": None}
        
    def create(self, validated_data):
        """Create a CompanyInformation record with OCR auto-fill."""
        user = self.context['request'].user
        file = validated_data.pop("company_or_individual_pan_card_file", None)

        if not file:
            raise serializers.ValidationError({"company_or_individual_pan_card_file": "PAN card upload is required."})
        
        file_bytes = file.read()
        extracted = self.extract_pan_details(file_bytes)

        company_info = CompanyInformation.objects.create(
            user=user,
            company_or_individual_pan_card_file=file_bytes,
            company_pan_number=extracted["pan_number"],
            pan_holder_name=extracted["pan_holder_name"],
            date_of_birth=extracted["dob"],
            **validated_data
        )
        return { 
            "company_id": company_info.company_id,
              "company_name": company_info.company_name,
                "company_pan_number": company_info.company_pan_number,
                  "pan_holder_name": company_info.pan_holder_name,
                    "date_of_birth": company_info.date_of_birth,
                      "message": "Company information and PAN details saved successfully." }




    
  