

import io
import re
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes

# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class BaseDocumentExtractor:
    def extract(self, file_bytes: bytes) -> dict:
        """Return extracted bank details as dict."""
        raise NotImplementedError
    

class PassbookExtractor(BaseDocumentExtractor):

    _FINAL_IFSC_REGEX = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")

    _RELAXED_IFSC_REGEX = re.compile(
        r"([A-Z]{4})"          # first 4 letters
        r"\W*([0OD])\W*"       # reserved ‘0’ but noisy
        r"([A-Z0-9]{6})"       # branch alphanumeric
    )

    def _clean_and_validate_ifsc(self, match: re.Match) -> str | None:
        bank_code = match.group(1)
        fifth_char_noisy = match.group(2)
        branch_code_noisy = match.group(3)

        cleaned_fifth = fifth_char_noisy.replace("O", "0").replace("D", "0")
        cleaned_branch = (
            branch_code_noisy.replace("O", "0")
            .replace("D", "0")
            .replace("I", "1")
            .replace("L", "1")
            .replace("S", "5")
        )

        candidate = f"{bank_code}{cleaned_fifth}{cleaned_branch}"
        if self._FINAL_IFSC_REGEX.match(candidate):
            return candidate
        return None

    def _extract_ifsc_code(self, text: str) -> str | None:
        if not text:
            return None

        norm = re.sub(r"[\n\r]", " ", text).upper()

        # Near keyword IFSC
        key = re.search(r"IFSC(?:\s*CODE)?[\s:;=\-]*([A-Z0-9\W]{8,40})", norm)
        if key:
            nearby = key.group(1)
            m = re.search(self._RELAXED_IFSC_REGEX, nearby)
            if m:
                cleaned = self._clean_and_validate_ifsc(m)
                if cleaned:
                    return cleaned

        # Fallback global
        m = re.search(self._RELAXED_IFSC_REGEX, norm)
        if m:
            return self._clean_and_validate_ifsc(m)

        return None

    def _extract_account_type(self, text: str) -> str | None:
        text_lower = text.lower()

        match = re.search(
            r"(account\s*type|a/c\s*type|ac\s*type)\s*[:\-]?\s*([a-zA-Z\s]+)",
            text_lower,
        )
        if match:
            out = match.group(2).strip().title()
            out = out.split("account")[0].strip()
            return out or None

        # Short forms
        if re.search(r"\bSB\s*A/C\b", text_lower):
            return "Savings"
        if re.search(r"\bCA\s*A/C\b", text_lower):
            return "Current"

        # Generic fallbacks
        for word in ["savings", "current", "salary", "nre", "nro", "recurring", "fixed"]:
            if word in text_lower:
                return word.title()

        return None

    def _extract_customer_name(self, text: str) -> str | None:
        # Passbooks usually have "Name:" or "Customer Name"
        match = re.search(
            r"(customer\s*name|name)\s*[:\-]?\s*([A-Za-z\s]+)", text, re.IGNORECASE
        )
        if match:
            out = match.group(2).strip()
            # Remove noise like "Address"
            out = re.split(r"address", out, flags=re.IGNORECASE)[0].strip()
            return out
        return None

    def extract(self, file_bytes: bytes) -> dict:
        try:
            # Detect PDF or Image
            is_pdf = file_bytes[:4] == b"%PDF"

            if is_pdf:
                pages = convert_from_bytes(file_bytes)
                text = ""
                for p in pages:
                    text += pytesseract.image_to_string(p)
            else:
                img = Image.open(io.BytesIO(file_bytes))
                text = pytesseract.image_to_string(img)

            clean = (
                text.replace("\n", " ")
                .replace(":", " ")
                .replace("-", " ")
                .strip()
            )
            clean_lower = clean.lower()

            # Regex patterns
            account_no_pattern = r"\b\d{9,18}\b"
            branch_pattern = r"branch\s*[:\-]?\s*([a-zA-Z0-9\s]+)"
            bank_pattern = r"([A-Z][A-Za-z\s]+bank( of india)?)"

            # Extract fields
            ifsc = self._extract_ifsc_code(clean)
            account_no = re.search(account_no_pattern, clean)
            branch_match = re.search(branch_pattern, clean_lower)
            bank_match = re.search(bank_pattern, clean, re.IGNORECASE)
            account_type = self._extract_account_type(clean)
            customer_name = self._extract_customer_name(clean)

            # Guess bank name if missing
            common_banks = {
                "sbi": "State Bank of India",
                "hdfc": "HDFC Bank",
                "icici": "ICICI Bank",
                "axis": "Axis Bank",
                "pnb": "Punjab National Bank",
                "bob": "Bank of Baroda",
                "kotak": "Kotak Mahindra Bank",
                "canara": "Canara Bank",
                "union": "Union Bank of India",
            }

            bank_name = bank_match.group(1).strip() if bank_match else None
            if not bank_name:
                for key, val in common_banks.items():
                    if key in clean_lower:
                        bank_name = val
                        break

            result = {
                "bank_name": bank_name,
                "branch_name": branch_match.group(1).strip().title() if branch_match else None,
                "account_number": account_no.group(0) if account_no else None,
                "ifsc_code": ifsc,
                "account_type": account_type,
                "customer_name": customer_name,
            }

            return {"success": True, "data": result}

        except Exception as e:
            return {"success": False, "error": str(e)}



class ChequeExtractor:

    _FINAL_IFSC_REGEX = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")

    _RELAXED_IFSC_REGEX = re.compile(
        r"([A-Z]{4})"          # first 4 letters
        r"\W*([0OD])\W*"       # 5th reserved char (0, O, or D)
        r"([A-Z0-9]{6})"       # 6 alphanumeric branch chars
    )

    def _clean_and_validate_ifsc(self, match: re.Match) -> str | None:
        """Clean and validate IFSC candidate."""
        bank_code = match.group(1)
        fifth_char_noisy = match.group(2)
        branch_code_noisy = match.group(3)

        cleaned_fifth_char = fifth_char_noisy.replace("O", "0").replace("D", "0")
        cleaned_branch_code = (
            branch_code_noisy.replace("O", "0")
            .replace("D", "0")
            .replace("I", "1")
            .replace("L", "1")
            .replace("S", "5")
        )

        candidate = f"{bank_code}{cleaned_fifth_char}{cleaned_branch_code}"
        if self._FINAL_IFSC_REGEX.match(candidate):
            return candidate
        return None

    def _extract_ifsc_code(self, text: str) -> str | None:
        """Extract IFSC code (pattern: 4 letters + 0 + 6 digits/alphanumeric)."""
        if not text:
            return None

        norm_text = re.sub(r"[\n\r]", " ", text).upper()

        # --- 1. Search near 'IFSC' keyword ---
        keyword_search = re.search(
            r"IFSC(?:\s*CODE)?[\s:;=\-]*([A-Z0-9\W]{8,40})", norm_text
        )
        if keyword_search:
            nearby_text = keyword_search.group(1)
            match = re.search(self._RELAXED_IFSC_REGEX, nearby_text)
            if match:
                result = self._clean_and_validate_ifsc(match)
                if result:
                    return result

        # --- 2. Global fallback ---
        fallback_match = re.search(self._RELAXED_IFSC_REGEX, norm_text)
        if fallback_match:
            result = self._clean_and_validate_ifsc(fallback_match)
            if result:
                return result

        return None

    def _extract_account_type(self, text: str) -> str | None:
        if not text:
            return None

        text_lower = text.lower()
        account_keywords = [
            "savings",
            "current",
            "salary",
            "nre",
            "nro",
            "recurring",
            "fixed",
            "deposit",
        ]

        # Pattern for lines like 'Account Type: Savings Account'
        match = re.search(
            r"(account\s*type|a/c\s*type|ac\s*type)\s*[:\-]?\s*([a-zA-Z\s]+)",
            text_lower,
        )
        if match:
            found = match.group(2).strip().title()
            found = found.split("account")[0].strip()
            return found

        # Detect short forms like 'SB A/C', 'CA A/C'
        if re.search(r"\bSB\s*A/C\b", text_lower):
            return "Savings"
        if re.search(r"\bCA\s*A/C\b", text_lower):
            return "Current"

        # Fallback: keyword-based detection
        for word in account_keywords:
            if word in text_lower:
                return word.title()

        return None

    def extract(self, file_bytes: bytes) -> dict:
        try:
            # Detect file type
            first_bytes = file_bytes[:4]
            is_pdf = first_bytes == b"%PDF"

            # OCR extraction
            text = ""
            if is_pdf:
                images = convert_from_bytes(file_bytes)
                for img in images:
                    text += pytesseract.image_to_string(img)
            else:
                image = Image.open(io.BytesIO(file_bytes))
                text = pytesseract.image_to_string(image)

            # Normalize
            clean_text = text.replace("\n", " ").replace(":", " ").replace("-", " ").strip()
            clean_text_lower = clean_text.lower()

            # Regex patterns
            account_pattern = r"\b\d{9,18}\b"
            branch_pattern = r"(?:branch\s*[:\-]?\s*)([a-zA-Z0-9\s]+)"
            bank_pattern = r"([A-Z][A-Za-z\s]+bank( of india)?)"

            # Extract details
            ifsc_candidate = self._extract_ifsc_code(clean_text)
            account_match = re.search(account_pattern, clean_text)
            branch_match = re.search(branch_pattern, clean_text_lower)
            bank_match = re.search(bank_pattern, clean_text, re.IGNORECASE)
            account_type = self._extract_account_type(clean_text)

            # Guess bank name if missing
            common_banks = {
                "sbi": "State Bank of India",
                "hdfc": "HDFC Bank",
                "icici": "ICICI Bank",
                "axis": "Axis Bank",
                "pnb": "Punjab National Bank",
                "bob": "Bank of Baroda",
                "kotak": "Kotak Mahindra Bank",
                "canara": "Canara Bank",
                "union": "Union Bank of India",
            }

            bank_name = bank_match.group(1).strip() if bank_match else None
            if not bank_name:
                for key, val in common_banks.items():
                    if key in clean_text_lower:
                        bank_name = val
                        break

            # Assemble final result
            extracted_data = {
                "bank_name": bank_name,
                "branch_name": (
                    branch_match.group(1).strip().title() if branch_match else None
                ),
                "account_number": account_match.group(0) if account_match else None,
                "ifsc_code": ifsc_candidate,
                "account_type": account_type,
            }

            return {"success": True, "data": extracted_data}

        except Exception as e:
            return {"success": False, "error": str(e)}


class BankStatementExtractor(BaseDocumentExtractor):

    _FINAL_IFSC_REGEX = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")

    _RELAXED_IFSC_REGEX = re.compile(
        r"([A-Z]{4})"
        r"\W*([0OD])\W*"
        r"([A-Z0-9]{6})"
    )

    def _clean_and_validate_ifsc(self, match: re.Match) -> str | None:
        bank_code = match.group(1)
        fifth = match.group(2).replace("O", "0").replace("D", "0")
        branch = (
            match.group(3)
            .replace("O", "0")
            .replace("D", "0")
            .replace("I", "1")
            .replace("L", "1")
            .replace("S", "5")
        )
        candidate = f"{bank_code}{fifth}{branch}"
        return candidate if self._FINAL_IFSC_REGEX.match(candidate) else None

    def _extract_ifsc(self, text: str) -> str | None:
        if not text:
            return None
        norm = text.upper().replace("\n", " ")

        key = re.search(r"IFSC(?:\s*CODE)?[\s:=\-]*([A-Z0-9\W]{8,40})", norm)
        if key:
            chunk = key.group(1)
            m = re.search(self._RELAXED_IFSC_REGEX, chunk)
            if m:
                cleaned = self._clean_and_validate_ifsc(m)
                if cleaned:
                    return cleaned

        m = re.search(self._RELAXED_IFSC_REGEX, norm)
        if m:
            return self._clean_and_validate_ifsc(m)
        return None

    def _extract_account_number(self, text: str) -> str | None:
        # Bank statements often label "Account Number", "A/C No", "A/c No"
        m = re.search(
            r"(account\s*(number|no)|a/c\s*no)\s*[:\-]?\s*(\d{9,18})",
            text, re.IGNORECASE
        )
        if m:
            return m.group(3)

        # fallback
        m = re.search(r"\b\d{9,18}\b", text)
        return m.group(0) if m else None

    def _extract_account_type(self, text: str) -> str | None:
        tl = text.lower()
        m = re.search(
            r"(account\s*type|a/c\s*type)\s*[:\-]?\s*([a-zA-Z\s]+)",
            tl
        )
        if m:
            t = m.group(2).strip().title()
            return t.split("account")[0].strip() or None

        if "savings" in tl:
            return "Savings"
        if "current" in tl:
            return "Current"
        return None

    def _extract_branch(self, text: str) -> str | None:
        m = re.search(r"branch\s*[:\-]?\s*([A-Za-z0-9\s]+)", text, re.IGNORECASE)
        if m:
            return m.group(1).strip().title()
        return None

    def extract(self, file_bytes: bytes) -> dict:
        try:
            is_pdf = file_bytes[:4] == b"%PDF"

            if is_pdf:
                pages = convert_from_bytes(file_bytes)
                text = ""
                for p in pages:
                    text += pytesseract.image_to_string(p)
            else:
                img = Image.open(io.BytesIO(file_bytes))
                text = pytesseract.image_to_string(img)

            clean = (
                text.replace("\n", " ")
                .replace(":", " ")
                .replace("-", " ")
                .strip()
            )
            clean_lower = clean.lower()

            # Detect bank name
            bank_pattern = r"([A-Z][A-Za-z\s]+bank( of india)?)"
            bank_match = re.search(bank_pattern, clean, re.IGNORECASE)

            common_banks = {
                "sbi": "State Bank of India",
                "state bank": "State Bank of India",
                "hdfc": "HDFC Bank",
                "icici": "ICICI Bank",
                "axis": "Axis Bank",
                "pnb": "Punjab National Bank",
                "bob": "Bank of Baroda",
            }

            bank_name = bank_match.group(1).strip() if bank_match else None
            if not bank_name:
                for key, val in common_banks.items():
                    if key in clean_lower:
                        bank_name = val
                        break

            # Extract fields
            account_no = self._extract_account_number(clean)
            ifsc = self._extract_ifsc(clean)
            branch = self._extract_branch(clean)
            account_type = self._extract_account_type(clean)

            return {
                "success": True,
                "data": {
                    "bank_name": bank_name,
                    "branch_name": branch,
                    "account_number": account_no,
                    "ifsc_code": ifsc,
                    "account_type": account_type,
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}



class DocumentExtractorFactory:
    @staticmethod
    def get_extractor(doc_type: str) -> BaseDocumentExtractor:
        if doc_type == "passbook":
            return PassbookExtractor()
        elif doc_type == "cheque":
            return ChequeExtractor()
        elif doc_type == "bank_statement":
            return BankStatementExtractor()
        else:
            raise ValueError("Unsupported document type")
