# services/bond_estimation_service.py

from apps.bond_estimate.models.BondEstimationApplicationModel import BondEstimationApplication
from apps.bond_estimate.models.CapitalDetailsModel import CapitalDetails
from apps.bond_estimate.models.CreditRatingDetailsModel import CreditRatingDetails
from apps.bond_estimate.models.FundPositionModel import FundPosition
from apps.bond_estimate.models.borrowing_details import BorrowingDetails
from apps.bond_estimate.models.PreliminaryBondRequirementsModel import PreliminaryBondRequirements
from apps.bond_estimate.models.CollateralAssetVerificationModel import CollateralAssetVerification
from apps.bond_estimate.models.ProfitabilityRatiosModel import ProfitabilityRatios
from apps.bond_estimate.services.financial_documents.financial_document_service import FinancialDocumentService
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


STEP_MODEL_MAP = {
    # Add step and its model here
    "1.1":FundPosition,
    "1.2":CreditRatingDetails, 
    "3.1":BorrowingDetails,
    "3.2":CapitalDetails,
    "4":ProfitabilityRatios,
    "5.1":PreliminaryBondRequirements,
    "5.2":CollateralAssetVerification,
}

REQUIRED_SUB_STEPS = {
    "3": ["3.1", "3.2"],
    "1": ["1.1", "1.2"],
    "5": ["5.1", "5.2"],
}

def create_or_get_application(user, company):
    """
    Returns existing active application or creates a new one.P
    """
    app, created = BondEstimationApplication.objects.get_or_create(
        user=user,
        company=company,
        status__in=["DRAFT", "IN_PROGRESS"],
        defaults={"user": user, "company": company},
    )
    return app


def update_step(application: BondEstimationApplication, step_id: str, **kwargs):
    """
    Thin wrapper to call model.mark_step()
    """
    return application.mark_step(step_id, **kwargs)


def is_ready_for_calculation(application: BondEstimationApplication) -> bool:
    """
    Application is ready only if:
    1. Company-level financial docs completed
    2. App-level steps 1, 3, 4, 5 completed
    """
    company_id = application.company.company_id

    financial_docs_done = FinancialDocumentService.is_step_completed(company_id)

    REQUIRED_APP_STEPS = ["1", "3", "4", "5"]

    app_steps_done = all(application.is_step_completed(s) for s in REQUIRED_APP_STEPS)

    return financial_docs_done and app_steps_done


def get_application_status_summary(application: BondEstimationApplication):
    """
    Returns:
    - financial_docs_completed (company-level)
    - completed application steps
    - missing application steps
    - next required step
    - last accessed step
    - is_ready_for_calculation
    """

    logger.debug(f"[StatusSummary] Checking status for application {application.application_id}")

    company_id = application.company.company_id

    # 1. Company-level step (financial docs)
    fin_docs_done = FinancialDocumentService.is_step_completed(company_id)
    logger.debug(f"[StatusSummary] Financial docs: {fin_docs_done}")

    # 2. Application steps
    REQUIRED_APP_STEPS = ["1", "3", "4", "5"]

    completed = []
    missing = []

    for s in REQUIRED_APP_STEPS:
        if application.is_step_completed(s):
            completed.append(s)
        else:
            missing.append(s)

    logger.debug(f"[StatusSummary] Completed: {completed}, Missing: {missing}")

    next_step = missing[0] if missing else None

    # 3. Final readiness for calculation
    is_ready = fin_docs_done and len(missing) == 0

    logger.debug(f"[StatusSummary] Final readiness: {is_ready}")

    return {
        "financial_docs_completed": fin_docs_done,
        "application_steps_completed": completed,
        "application_steps_missing": missing,
        "next_required_step": next_step,
        "last_accessed_step": application.last_accessed_step,
        "is_ready_for_calculation": is_ready,
    }