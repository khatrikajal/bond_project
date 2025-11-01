from models.CompanyOnboardingTransitionModel import CompanyOnboardingTransition
from .get_client_ip import get_client_ip


def log_step_transition(application, from_step, to_step, action, user, request, extra_data=None):
    CompanyOnboardingTransition.objects.create(
        application=application,
        from_step=from_step,
        to_step=to_step,
        action=action,
        user=user,
        ip_address=get_client_ip(request),
        changed_data=extra_data or {}
    )