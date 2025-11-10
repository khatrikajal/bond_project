# services/onboarding_service.py

from django.core.exceptions import ObjectDoesNotExist
# from models.CompanyInformationModel  import CompanyInformation
# from models.CompanyAdressModel import CompanyAddress

from apps.kyc.issuer_kyc.models.CompanyAdressModel import CompanyAddress
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from apps.kyc.issuer_kyc.models.BankDetailsModel import BankDetails
# from apps.kyc.issuer_kyc.models.DematAccountModel  import DematAccount
from apps.kyc.issuer_kyc.models.FinancialDocumentModel import FinancialDocument
from apps.kyc.issuer_kyc.models.CompanyDocumentModel import CompanyDocument
from apps.kyc.issuer_kyc.models.DemateAccountDetailsModel import DematAccount
from datetime import timezone
import logging

logger = logging.getLogger(__name__)


# ✅ Central mapping of steps to model classes (scalable)
STEP_MODEL_MAP = {
    1: CompanyInformation,
    2: CompanyAddress,
    4: [BankDetails],
    5:FinancialDocument,
    3:CompanyDocument,
    4: [BankDetails, DematAccount],

    # add more steps here (KYC, Documents, Directors etc.)
}


def get_model_for_step(step_number: int):
    """
    Returns the Django model class mapped to a specific step.

    Args:
        step_number (int): The onboarding step number.

    Returns:
        model (DjangoModel | None): The model associated with the step.
    """
    return STEP_MODEL_MAP.get(step_number)



def get_step_data(application, step_number: int):
    """
    Retrieves all saved records for a given onboarding step.

    Behavior:
        ✅ Step 1 uses OneToOne → return a list of one element
        ✅ Step 2+ use ForeignKey(company)
        ✅ Safe fallback when company_information is missing

    Args:
        application (CompanyOnboardingApplication):
            The application whose step data must be fetched.

        step_number (int): Onboarding step number.

    Returns:
        list: List of model instances for that step.
    """

    model = get_model_for_step(step_number)
    if not model:
        return []

    # ✅ Step 1: OneToOne relation (CompanyInformation)
    if step_number == 1:
        company_info = application.company_information
        return [company_info] if company_info else []

    # ✅ Safety check: For step 2+, company_information MUST exist
    if not application.company_information:
        return []   # user hasn't even completed step 1

    # ✅ Step 2+: Fetch using ForeignKey(company)
    return list(
        model.objects.filter(company=application.company_information)
        .order_by("-created_at")  # optional, but useful
    )



def update_step_4_status(application, bank_ids=None, demat_ids=None):
    """
    Safely updates Step 4 completion in onboarding JSON.

    Args:
        application: CompanyOnboardingApplication instance
        bank_ids: list of bank_detail_ids (optional)
        demat_ids: list of demat_account_ids (optional)
    """
    company = application.company_information
    if not company:
        return

    step_state = application.step_completion.get("4", {})
    record_id = step_state.get("record_id", {})

    # 🧩 Fix: Convert record_id to dict if it’s a string
    if not isinstance(record_id, dict):
        record_id = {}

    # Update partial record IDs if provided
    if bank_ids is not None:
        record_id["bank_details"] = bank_ids
    if demat_ids is not None:
        record_id["demat_account"] = demat_ids

    # Determine if both sides are complete
    step_completed = bool(record_id.get("bank_details")) and bool(record_id.get("demat_account"))

    # Update step state
    step_state.update({
        "completed": step_completed,
        "record_id": record_id,
    })

    if step_completed:
        step_state["completed_at"] = timezone.now().isoformat()

    # Update the application record
    application.step_completion["4"] = step_state

    if application.status == "INITIATED":
        application.status = "IN_PROGRESS"

    application.save(update_fields=["step_completion", "status", "updated_at"])
