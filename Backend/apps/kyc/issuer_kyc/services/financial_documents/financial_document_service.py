from datetime import date
from apps.kyc.issuer_kyc.models.FinancialDocumentModel import FinancialDocument, DocumentType, PeriodType
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
import logging
import re

logger = logging.getLogger(__name__)

class FinancialDocumentService:
 
    USE_VERIFICATION_RULE = False   # feature flag (switch logic without code changes)

    # Dynamic mapping – PERIOD → expected document count per FY
    PERIOD_LENGTH = {
        PeriodType.MONTHLY: 12,
        PeriodType.QUARTERLY: 4,
        PeriodType.YEARLY: 1,
    }

    @staticmethod
    def get_last_four_fys():
        year = date.today().year
        return [
            f"FY{year-3}-{year-2}",
            f"FY{year-2}-{year-1}",
            f"FY{year-1}-{year}",
            f"FY{year}-{year+1}",
        ]

    # ---------------------------------------------------------
    # ✅ Check if all required documents exist (count-only)
    # ---------------------------------------------------------
    @classmethod
    def check_count_only(cls, company_id):

        fys = cls.get_last_four_fys()
        doc_types = list(DocumentType.values)

        for fy in fys:

            for doc_type in doc_types:

                # Get the period type from ANY one record (if it exists)
                period_type = FinancialDocument.objects.filter(
                    company_id=company_id,
                    document_type=doc_type,
                ).values_list("period_type", flat=True).first()

                if not period_type:
                    # Document type doesn't exist for this FY → fail
                    return False

                required_count = cls.PERIOD_LENGTH.get(period_type, 1)

                actual_count = FinancialDocument.objects.filter(
                    company_id=company_id,
                    financial_year=fy,
                    document_type=doc_type,
                    del_flag=0
                ).count()

                if actual_count < required_count:
                    return False

        return True

    # ---------------------------------------------------------
    # ✅ Check count + verification-required
    # ---------------------------------------------------------
    @classmethod
    def check_verified(cls, company_id):

        fys = cls.get_last_four_fys()
        doc_types = list(DocumentType.values)

        for fy in fys:

            for doc_type in doc_types:

                period_type = FinancialDocument.objects.filter(
                    company_id=company_id,
                    document_type=doc_type,
                ).values_list("period_type", flat=True).first()

                if not period_type:
                    return False

                required_count = cls.PERIOD_LENGTH.get(period_type, 1)

                actual_count = FinancialDocument.objects.filter(
                    company_id=company_id,
                    financial_year=fy,
                    document_type=doc_type,
                    is_verified=True,
                    del_flag=0
                ).count()

                if actual_count < required_count:
                    return False

        return True

    # ---------------------------------------------------------
    # ✅ Public method used by onboarding
    # ---------------------------------------------------------
    @classmethod
    def is_step_completed(cls, company_id):
        if cls.USE_VERIFICATION_RULE:
            return cls.check_verified(company_id)
        return cls.check_count_only(company_id)
    

    @classmethod
    def get_missing_details(cls, company_id):
        """
        Return missing documents grouped by financial year.
        {
            "FY2022-2023": [ { ... }, { ... } ],
            "FY2023-2024": [ { ... }, ... ],
            ...
        }
        """
        fys = cls.get_last_four_fys()
        doc_types = list(DocumentType.values)

        grouped = {}

        for fy in fys:
            grouped[fy] = []   # initialize empty list for each year

            for doc_type in doc_types:

                # Get any existing period type for this doc_type
                period_type = FinancialDocument.objects.filter(
                    company_id=company_id,
                    document_type=doc_type,
                ).values_list("period_type", flat=True).first()

                if not period_type:
                    # No document uploaded for this type → default YEARLY required
                    grouped[fy].append({
                        "document_type": doc_type,
                        "required_count": cls.PERIOD_LENGTH.get(PeriodType.YEARLY, 1),
                        "uploaded_count": 0,
                        "reason": "No uploads found"
                    })
                    continue

                required = cls.PERIOD_LENGTH.get(period_type, 1)
                normalized_fys = cls.canonical_fy(fy)

                actual = FinancialDocument.objects.filter(
                    company_id=company_id,
                    financial_year__in=normalized_fys,
                    document_type=doc_type,
                    del_flag=0
                ).count()


                if actual < required:
                    grouped[fy].append({
                        "document_type": doc_type,
                        "required_count": required,
                        "uploaded_count": actual,
                        "reason": f"Missing {required - actual} records",
                    })

            # Remove empty FYs (optional: keep empty years as [])
            if not grouped[fy]:
                del grouped[fy]

        return grouped

    @staticmethod
    def canonical_fy(fy):
        """
        Convert any FY format into canonical FYYYYY-YY format.
        Examples:
        "2023-24"       -> "FY2023-24"
        "2023-2024"     -> "FY2023-24"
        "FY2023-24"     -> "FY2023-24"
        "FY2023-2024"   -> "FY2023-24"
        """

        fy = fy.replace("FY", "").strip()   # remove prefix

        first, second = fy.split("-")

        # Convert 2024 to 24 if needed
        if len(second) == 4:
            second = second[2:]   # 2024 → 24

        return f"FY{first}-{second}"


    @staticmethod
    def update_onboarding_state(company_id):
        """
        Marks onboarding step 5 (Financial Documents) as completed/incomplete.
        """
        try:
            company = CompanyInformation.objects.get(pk=company_id)

            # get onboarding application
            application = getattr(company, "application", None)
            if not application:
                logger.warning(f"No onboarding application found for company {company_id}.")
                return

            # check completion
            is_completed = FinancialDocumentService.is_step_completed(company_id)

            # ✅ correct object to call update_state on
            application.update_state(
                step_number=5,
                completed=is_completed
            )

        except Exception as e:
            logger.error(f"update_onboarding_state failed for company {company_id}: {e}", exc_info=True)