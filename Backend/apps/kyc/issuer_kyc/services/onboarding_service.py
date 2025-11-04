# services/onboarding_service.py

from django.core.exceptions import ObjectDoesNotExist
# from models.CompanyInformationModel  import CompanyInformation
# from models.CompanyAdressModel import CompanyAddress

from apps.kyc.issuer_kyc.models.CompanyAdressModel import CompanyAddress
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation


# ✅ Central mapping of steps to model classes (scalable)
STEP_MODEL_MAP = {
    1: CompanyInformation,
    2: CompanyAddress,
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