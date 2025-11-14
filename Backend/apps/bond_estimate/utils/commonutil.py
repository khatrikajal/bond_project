# apps/bond_estimate/utils.py

from typing import Optional, Tuple
from django.core.paginator import Paginator, EmptyPage
from django.db.models import QuerySet

from config.common.response import APIResponse
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation

from apps.bond_estimate.services.bond_estimation_service import (
    create_or_get_application,
    update_step,
    REQUIRED_SUB_STEPS,
)


# -------------------------------------------------------------------------
# VALIDATE: Company must belong to logged-in user
# -------------------------------------------------------------------------
def get_company_for_user(company_id, user) -> Optional[CompanyInformation]:
    """
    Fetch company belonging to the logged-in user.
    Return None if not owned / not found.
    """
    try:
        return CompanyInformation.objects.get(company_id=company_id, user=user)
    except CompanyInformation.DoesNotExist:
        return None


# -------------------------------------------------------------------------
# PAGINATION: Limit/Offset flexible pagination
# -------------------------------------------------------------------------
def paginate_queryset(
    queryset: QuerySet,
    request,
    default_page_size: int = 25,
    max_page_size: int = 200
) -> Tuple[list, dict]:
    """
    Efficient limit-offset pagination.
    Returns: (results_list, meta_dict)
    """
    try:
        limit = int(request.query_params.get("limit", default_page_size))
        offset = int(request.query_params.get("offset", 0))
    except (TypeError, ValueError):
        limit = default_page_size
        offset = 0

    limit = max(1, min(limit, max_page_size))
    offset = max(0, offset)

    total = queryset.count()
    results = list(queryset[offset: offset + limit])

    meta = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "returned": len(results),
    }
    return results, meta


# -------------------------------------------------------------------------
# STEP TRACKING: Auto-update main step when substeps change
# -------------------------------------------------------------------------
def update_step_status(application, main_step: str):
    """
    Auto-update main step (e.g., "4") depending on its required substeps.
    Called after create/update/delete of substeps like 4.1 or 4.2.
    """
    required = REQUIRED_SUB_STEPS.get(main_step, [])

    if not required:
        # No validation needed
        return

    all_done = all(application.is_step_completed(step) for step in required)

    update_step(
        application=application,
        step_id=main_step,
        completed=all_done,
    )


# -------------------------------------------------------------------------
# HELPER: Validate and fetch object safely
# -------------------------------------------------------------------------
def get_object_or_error(queryset, **filters):
    """
    Replaces get_object_or_404 with APIResponse error handling.
    Returns tuple -> (object or None, error_response or None)
    """
    try:
        obj = queryset.get(**filters)
        return obj, None
    except queryset.model.DoesNotExist:
        return None, APIResponse.error(
            message="Record not found",
            status_code=404
        )
