from datetime import date
from apps.kyc.issuer_kyc.models.FinancialDocumentModel import FinancialDocument, DocumentType, PeriodType
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation

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
    

    @staticmethod
    def update_onboarding_state(company_id):
        company = CompanyInformation.objects.get(pk=company_id)

        is_completed = FinancialDocumentService.is_step_completed(company_id)

        company.update_state(step_number=5, completed=is_completed)
