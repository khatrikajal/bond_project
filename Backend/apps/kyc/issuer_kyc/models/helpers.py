from .CompanyOnboardingApplicationModel import CompanyOnboardingApplication
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation

def update_step_state(company_id, step_number, status="COMPLETED"):
    company = CompanyInformation.objects.get(company_id=company_id)
    app = company.application  # OneToOne relation

    completed = set(app.completed_steps or [])

    if status == "COMPLETED":
        completed.add(step_number)

    app.completed_steps = list(completed)
    app.current_step = step_number
    app.save(update_fields=["completed_steps", "current_step"])

    return app