# services/bond_estimation_service.py

from apps.bond_estimate.models.BondEstimationApplicationModel import BondEstimationApplication
from apps.bond_estimate.models.CapitalDetailsModel import CapitalDetails
from apps.bond_estimate.models.CreditRatingDetailsModel import CreditRatingDetails
from apps.bond_estimate.models.FundPositionModel import FundPosition
from apps.bond_estimate.models.borrowing_details import BorrowingDetails
from apps.bond_estimate.models.PreliminaryBondRequirementsModel import PreliminaryBondRequirements
from apps.bond_estimate.models.CollateralAssetVerificationModel import CollateralAssetVerification
from apps.bond_estimate.models.FinancialDocumentModel import FinancialDocument
STEP_MODEL_MAP = {
    # Add step and its model here
    "1.1":FundPosition,
    "1.2":CreditRatingDetails,
    "2":FinancialDocument,  
    "3.1":BorrowingDetails,
    "3.2":CapitalDetails,
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
    Application is ready for calculation only if required steps are complete.
    """
    REQUIRED_STEPS = ["1", "2", "3", "5"]
    return all(application.is_step_completed(s) for s in REQUIRED_STEPS)