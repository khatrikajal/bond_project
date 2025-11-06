import re
import os
import pytesseract
import mimetypes
import platform
from PIL import Image, UnidentifiedImageError
from pdf2image import convert_from_path

# --- Auto-detect Tesseract binary path based on OS ---
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
elif platform.system() == "Darwin":  # macOS (Apple Silicon / Intel)
    pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"
else:  # Linux
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


# --- Indian states reference ---
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
    "Uttarakhand", "West Bengal", "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry",
    "Dadra and Nagar Haveli", "Daman and Diu", "Andaman and Nicobar Islands", "Chandigarh"
]
STATE_SET = {s.lower() for s in INDIAN_STATES}


def detect_file_type(file_path: str) -> str:
    """
    Detect file type using MIME type and Pillow for image verification.
    Returns: 'image' | 'pdf'
    Raises ValueError if unsupported.
    """
    mime_type, _ = mimetypes.guess_type(file_path)

    # Detect by extension first
    if mime_type and "pdf" in mime_type:
        return "pdf"
    elif mime_type and "image" in mime_type:
        return "image"

    # If mimetype uncertain, try opening with Pillow
    try:
        with Image.open(file_path) as img:
            img.verify()  # Verify it’s an image
        return "image"
    except UnidentifiedImageError:
        pass

    raise ValueError(f"Unsupported or unknown file type: {file_path}")


def extract_address_from_bill(file_path: str):
    """
    Extract structured address fields (line1, line2, city, state, pin)
    from OCR of image or PDF documents.
    Works even if temp file has no extension.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # --- Detect file type ---
    try:
        file_type = detect_file_type(file_path)
    except Exception as e:
        raise RuntimeError(f"File type detection failed: {str(e)}")

    text = ""
    try:
        if file_type == "image":
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img)

        elif file_type == "pdf":
            pages = convert_from_path(file_path)
            for page in pages:
                text += pytesseract.image_to_string(page) + "\n"

    except Exception as e:
        raise RuntimeError(f"OCR extraction failed: {str(e)}")

    # --- Clean text ---
    text = re.sub(r"[^\x00-\x7F\n]+", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text.strip())
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    if not lines:
        return {"error": "No readable text detected from OCR."}

    # --- Step 1: Find PIN code ---
    pin, pin_idx = None, None
    for i, line in enumerate(lines):
        match = re.search(r"\b(\d{6})\b", line)
        if match:
            pin = match.group(1)
            pin_idx = i
            break

    if not pin:
        return {"error": "Pincode not found in document."}

    # --- Step 2: Collect address context ---
    addr_lines = []
    context_lines = lines[max(0, pin_idx - 2): pin_idx + 1]
    for ln in context_lines:
        if not re.search(r"(gstin|bill|invoice|amount|rs\.|due|http|www)", ln, re.I):
            addr_lines.append(ln)

    # Build address string up to PIN only
    address_text = " ".join(addr_lines)
    address_text = re.sub(r"\s+", " ", address_text)
    address_text = re.sub(r"[,:;]+", " ", address_text).strip()
    address_text = re.split(r"\b\d{6}\b", address_text)[0] + f" {pin}"

    # --- Step 3: Extract state ---
    state = next((st.title() for st in STATE_SET if st in address_text.lower()), None)

    # --- Step 4: Extract city ---
    before_pin = address_text.split(pin)[0].strip()
    tokens = before_pin.split()
    city = tokens[-1].replace(".", "").title() if tokens else None

    # --- Step 5: Split address lines ---
    if ";" in address_text:
        parts = [p.strip() for p in address_text.split(";", 1)]
        line1, line2 = parts[0], parts[1]
    else:
        tokens = before_pin.split()
        mid = len(tokens) // 2 if len(tokens) > 4 else 2
        line1 = " ".join(tokens[:mid])
        line2 = " ".join(tokens[mid:])

    # --- Step 6: Cleanup ---
    line2 = re.sub(rf"\b({city or ''}|{state or ''}|{pin})\b", "", line2, flags=re.I).strip()
    line2 = re.sub(r"\s{2,}", " ", line2)

    # --- Step 7: Return structured result ---
    return {
        "address_line1": line1 or None,
        "address_line2": line2 or None,
        "city": city,
        "state": state,
        "pin": pin,
    }


# --- Example Usage ---
if __name__ == "__main__":
    sample_file = "sample_bill.png"  # Replace with your file path
    try:
        result = extract_address_from_bill(sample_file)
        for k, v in result.items():
            print(f"{k}: {v}")
    except Exception as e:
        print(f" Error: {e}")
