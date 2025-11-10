from apps.kyc.issuer_kyc.models.FinancialDocumentModel import FinancialDocument
from datetime import datetime

# TEMP FEATURE FLAG
REQUIRE_MULTIPLE_YEARS = False     

# Required docs per FY
REQUIRED_DOCS_PER_YEAR = {
    "GSTR_3B": 12,   # monthly
    "GSTR_9": 1,     # yearly
    "ITR": 1,        # yearly
    "FINANCIAL_STATEMENT": 1,  # yearly
}

# number of FY to check → current + last 3
MULTI_YEAR_RANGE = 4   


def all_documents_verified(company_id: int, financial_year: str) -> bool:
    """
    Check if ALL required documents for a single FY are PRESENT AND VERIFIED.
    This is used by your verification logic.
    """

    qs = FinancialDocument.objects.filter(
        company_id=company_id,
        financial_year=financial_year,
        is_del=0,
        is_verified=True
    )

    # GSTR-3B requires 12 monthly verified entries
    if qs.filter(document_type="GSTR_3B").count() < REQUIRED_DOCS_PER_YEAR["GSTR_3B"]:
        return False

    # Yearly documents must be present and verified
    for doc_type in ["GSTR_9", "ITR", "FINANCIAL_STATEMENT"]:
        if qs.filter(document_type=doc_type).count() < REQUIRED_DOCS_PER_YEAR[doc_type]:
            return False

    return True




def all_required_years_present(company_id: int) -> bool:
    """
    TEMP logic.
    Checks if required documents EXIST (no verification check)
    for last N FY including current FY.

    Controlled fully by REQUIRE_MULTIPLE_YEARS flag.
    """

    if not REQUIRE_MULTIPLE_YEARS:
        return True   # Feature disabled → bypass check

    current_year = datetime.now().year
    fy_list = []

    # Build list of FY strings → FY2023-24, FY2022-23, FY2021-22, FY2020-21
    for i in range(MULTI_YEAR_RANGE):
        start_year = current_year - i
        fy_list.append(f"FY{start_year}-{str(start_year + 1)[-2:]}")

    # Verify each year has required number of docs (present only)
    for fy in fy_list:
        qs = FinancialDocument.objects.filter(
            company_id=company_id,
            financial_year=fy,
            is_del=0
        )

        # GSTR-3B monthly (12)
        if qs.filter(document_type="GSTR_3B").count() < REQUIRED_DOCS_PER_YEAR["GSTR_3B"]:
            return False

        # Yearly documents (1 each)
        for doc_type in ["GSTR_9", "ITR", "FINANCIAL_STATEMENT"]:
            if qs.filter(document_type=doc_type).count() < REQUIRED_DOCS_PER_YEAR[doc_type]:
                return False

    return True
