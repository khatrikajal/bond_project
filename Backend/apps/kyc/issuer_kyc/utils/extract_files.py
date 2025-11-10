# apps/kyc/utils/ocr_utils.py

import re
from io import BytesIO
from PIL import Image
import pytesseract

# ----------------------------
# 📌 PAN VALIDATION & EXTRACTION
# ----------------------------

def validate_pan_format(pan_number: str) -> bool:
    """Validate PAN format: 5 letters + 4 digits + 1 letter."""
    return bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", pan_number.strip().upper()))


def extract_pan_from_file(file_bytes: bytes) -> str | None:
    """Extract PAN number from an image/PDF using OCR."""
    try:
        img = Image.open(BytesIO(file_bytes))
        text = pytesseract.image_to_string(img).upper()
        match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", text)
        if match and validate_pan_format(match.group(0)):
            return match.group(0)
        return None
    except Exception as e:
        print("PAN OCR extraction error:", e)
        return None


# ----------------------------
# 📌 AADHAAR VALIDATION & EXTRACTION
# ----------------------------

def validate_aadhaar_format(aadhaar_number: str) -> bool:
    """Validate Aadhaar format: 12 digits (optionally grouped)."""
    aadhaar_number = re.sub(r"\s+", "", aadhaar_number)
    return bool(re.fullmatch(r"\d{12}", aadhaar_number))


def extract_aadhaar_from_file(file_bytes: bytes) -> str | None:
    """Extract Aadhaar number from an image using OCR."""
    try:
        img = Image.open(BytesIO(file_bytes))
        text = pytesseract.image_to_string(img)
        text = text.replace("\n", " ").replace("\t", " ")
        text = re.sub(r"[^\d\s]", "", text)

        # Match spaced or continuous Aadhaar
        aadhaar_match = re.search(r"(\d{4}\s?\d{4}\s?\d{4})", text)
        if aadhaar_match:
            aadhaar = re.sub(r"\s+", "", aadhaar_match.group(1))
            if validate_aadhaar_format(aadhaar):
                return aadhaar

        # Continuous 12-digit fallback
        continuous_match = re.search(r"\b\d{12}\b", text)
        if continuous_match and validate_aadhaar_format(continuous_match.group(0)):
            return continuous_match.group(0)

        return None
    except Exception as e:
        print("Aadhaar OCR extraction error:", e)
        return None
