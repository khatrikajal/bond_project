# import os
# import re
# from datetime import date
# from django.conf import settings
# from rest_framework import serializers
# from apps.authentication.services.verification_store import VerificationStore


# # --------------------------------------------------------------
# # Validate required fields
# # --------------------------------------------------------------
# def validate_required_fields(attrs, required_fields):
#     missing = [f for f in required_fields if not attrs.get(f)]
#     if missing:
#         raise serializers.ValidationError({
#             "non_field_errors": [f"{', '.join(missing)} field(s) are required."]
#         })


# # --------------------------------------------------------------
# # Validate mobile number (cache)
# # --------------------------------------------------------------
# def validate_mobile_verification(request, mobile):
#     if not VerificationStore.is_mobile_verified(request, mobile):
#         raise serializers.ValidationError({
#             "non_field_errors": ["Mobile number is not verified."]
#         })


# # --------------------------------------------------------------
# # Validate email verification (cache)
# # --------------------------------------------------------------
# def validate_email_verification(request, email):
#     if not VerificationStore.is_email_verified(request, email):
#         raise serializers.ValidationError({
#             "non_field_errors": ["Email is not verified."]
#         })


# # -------------------------------------------------------------------
# # STRICT PAN Holder Name Match (exact word-to-word)
# # -------------------------------------------------------------------

# def validate_pan_name(pan_holder_name, company_name):
#     if pan_holder_name.strip().lower() != company_name.strip().lower():
#         raise serializers.ValidationError({
#             "non_field_errors": ["PAN holder name must EXACTLY match the company name."]
#         })


# # -------------------------------------------------------------------
# # STRICT PAN Number Format (AAAAA9999A)
# # -------------------------------------------------------------------
# PAN_REGEX = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'

# def validate_pan_number(pan):
#     if not re.match(PAN_REGEX, pan):
#         raise serializers.ValidationError({
#             "company_pan_number": [
#                 "Invalid PAN format. Must be 5 uppercase letters, 4 digits, 1 uppercase letter (e.g., ABCDE1234F)."
#             ]
#         })

# # -------------------------------------------------------------------
# # STRICT GSTIN Format Validation (official govt regex)
# # -------------------------------------------------------------------
# def validate_gstin_format(gstin):
#     gst_regex = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"

#     if not re.match(gst_regex, gstin.upper()):
#         raise serializers.ValidationError({
#             "gstin": ["Invalid GSTIN format. Example: 22AAAAA0000A1Z5"]
#         })


# # -------------------------------------------------------------------
# # Validate file token exists
# # -------------------------------------------------------------------
# def validate_pan_file_token(file_token):
#     file_path = os.path.join(settings.MEDIA_ROOT, "temp_pan", f"{file_token}.pdf")
#     if not os.path.exists(file_path):
#         raise serializers.ValidationError({
#             "file_token": ["Invalid or expired file token."]
#         })


# # -------------------------------------------------------------------
# # STRICT Date of Birth Validation
# #  - No future dates
# #  - Not older than 120 years
# # -------------------------------------------------------------------
# def validate_date_of_birth(dob):
#     today = date.today()

#     if dob > today:
#         raise serializers.ValidationError({
#             "date_of_birth": ["Date of birth cannot be in the future."]
#         })

#     # Maximum age limit 120
#     min_valid_year = today.year - 120
#     if dob.year < min_valid_year:
#         raise serializers.ValidationError({
#             "date_of_birth": ["Date of birth is too old. Age cannot exceed 120 years."]
#         })


import os
import re
from datetime import date
from django.conf import settings
from rest_framework import serializers
from apps.authentication.services.verification_store import VerificationStore


# ============================================================
#  NORMALIZER (for company name + PAN holder match)
# ============================================================
def normalize_name(name):
    """Remove special chars + spaces + lowercase"""
    return re.sub(r'[^a-z]', '', name.strip().lower())


# ============================================================
# 1️⃣ REQUIRED FIELD VALIDATOR
# ============================================================
def validate_required_fields(attrs, required_fields):
    missing = [f for f in required_fields if not attrs.get(f)]
    if missing:
        raise serializers.ValidationError({
            "non_field_errors": [f"{', '.join(missing)} field(s) are required."]
        })


# ============================================================
# 2️⃣ MOBILE NUMBER VALIDATION
# ============================================================

MOBILE_REGEX = r'^[6-9]\d{9}$'   # India format only (10 digits, starts with 6–9)

def validate_mobile_format(mobile):
    mobile = mobile.strip()
    if mobile.startswith("+91"):
        mobile = mobile[3:]

    if not re.match(MOBILE_REGEX, mobile):
        raise serializers.ValidationError({
            "mobile_number": ["Invalid mobile number format. Must be a valid Indian mobile number."]
        })
    return mobile


def validate_mobile_verification(request, mobile):
    if not VerificationStore.is_mobile_verified(request, mobile):
        raise serializers.ValidationError({
            "non_field_errors": ["Mobile number is not verified."]
        })


# ============================================================
# 3️⃣ EMAIL VALIDATION
# ============================================================

EMAIL_REGEX = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

def validate_email_format(email):
    if not re.match(EMAIL_REGEX, email):
        raise serializers.ValidationError({
            "email": ["Invalid email format."]
        })


def validate_email_verification(request, email):
    if not VerificationStore.is_email_verified(request, email):
        raise serializers.ValidationError({
            "non_field_errors": ["Email is not verified."]
        })


# ============================================================
# 4️⃣ PAN NUMBER VALIDATION
# ============================================================

PAN_REGEX = r'^[A-Z]{5}[0-9]{4}[A-Z]$'

def validate_pan_number(pan):
    pan = pan.upper()
    if not re.match(PAN_REGEX, pan):
        raise serializers.ValidationError({
            "company_pan_number": [
                "Invalid PAN format. Must be: 5 letters, 4 digits, 1 letter (e.g., ABCDE1234F)."
            ]
        })


# ============================================================
# 5️⃣ PAN HOLDER NAME VS COMPANY NAME (STRICT NORMAL MATCH)
# ============================================================
def validate_pan_name(pan_holder_name, company_name):
    if pan_holder_name.strip().lower() != company_name.strip().lower():
        raise serializers.ValidationError({
            "non_field_errors": ["PAN holder name must EXACTLY match the company name."]
        })



# ============================================================
# 6️⃣ GSTIN VALIDATION
# ============================================================

GSTIN_REGEX = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$'

def validate_gstin_format(gstin):
    gstin = gstin.upper()
    if not re.match(GSTIN_REGEX, gstin):
        raise serializers.ValidationError({
            "gstin": ["Invalid GSTIN format. Example: 22ABCDE1234F1Z5"]
        })


# ============================================================
# 7️⃣ CIN VALIDATION
# ============================================================

CIN_REGEX = r'^[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$'

def validate_cin_format(cin):
    if not re.match(CIN_REGEX, cin.upper()):
        raise serializers.ValidationError({
            "corporate_identification_number": [
                "Invalid CIN format. Example: U12345MH2020PLC123456"
            ]
        })


# ============================================================
# 8️⃣ DATE OF BIRTH VALIDATION
# ============================================================

def validate_date_of_birth(dob):
    today = date.today()

    if dob > today:
        raise serializers.ValidationError({
            "date_of_birth": ["Date of birth cannot be in the future."]
        })

    if (today - dob).days > (120 * 365):
        raise serializers.ValidationError({
            "date_of_birth": ["Age cannot exceed 120 years."]
        })


# ============================================================
# 9️⃣ TEMP PAN FILE TOKEN
# ============================================================

def validate_pan_file_token(file_token):
    file_path = os.path.join(settings.MEDIA_ROOT, "temp_pan", f"{file_token}.pdf")
    if not os.path.exists(file_path):
        raise serializers.ValidationError({
            "file_token": ["Invalid or expired file token."]
        })


# -------------------------------------------------------------------
# STRICT UDYAM / MSME Number Validation
# Format: UDYAM-XX-XXXXXXXXXX
# -------------------------------------------------------------------
def validate_udyam_number(udyam):
    if not udyam:
        return  # optional field, skip

    udyam_regex = r"^UDYAM-[A-Z]{2}-\d{10}$"

    if not re.match(udyam_regex, udyam):
        raise serializers.ValidationError({
            "msme_udyam_registration_no": [
                "Invalid UDYAM number. Format must be: UDYAM-XX-XXXXXXXXXX"
            ]
        })