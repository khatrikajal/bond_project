# services/bond_estimation_service.py

from apps.bond_estimate.model.BondEstimationApplicationModel import BondEstimationApplication
STEP_MODEL_MAP = {
    # Add step and its model here
    # "1.1":FundPostion,
    # "1.2":Creditrating,
    # "2.2": CapitalDetails,
}


def create_or_get_application(user, company):
    """
    Returns existing active application or creates a new one.
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
    REQUIRED_STEPS = ["1", "2", "3"]
    return all(application.is_step_completed(s) for s in REQUIRED_STEPS)
