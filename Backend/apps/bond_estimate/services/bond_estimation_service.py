# services/bond_estimation_service.py

from apps.bond_estimate.models.BondEstimationApplicationModel import BondEstimationApplication
from apps.bond_estimate.models.CapitalDetailsModel import CapitalDetails
from apps.bond_estimate.models.CreditRatingDetailsModel import CreditRatingDetails
from apps.bond_estimate.models.FundPositionModel import FundPosition
from apps.bond_estimate.models.borrowing_details import BorrowingDetails
from apps.bond_estimate.models.PreliminaryBondRequirementsModel import PreliminaryBondRequirements
from apps.bond_estimate.models.CollateralAssetVerificationModel import CollateralAssetVerification
STEP_MODEL_MAP = {
    # Add step and its model here
    "1.1":FundPosition,
    "1.2":CreditRatingDetails,
    "2.1":BorrowingDetails,
    "2.2":CapitalDetails,
    "4.1":PreliminaryBondRequirements,
    "4.2":CollateralAssetVerification,
}

REQUIRED_SUB_STEPS = {
    "2": ["2.1", "2.2"],
    "1": ["1.1", "1.2"],
    "4": ["4.1", "4.2"],
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
    REQUIRED_STEPS = ["1", "2", "3"," 4"]
    return all(application.is_step_completed(s) for s in REQUIRED_STEPS)