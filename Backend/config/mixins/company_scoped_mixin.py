# config/mixins/company_scoped_mixin.py

from rest_framework.exceptions import PermissionDenied
from apps.utils.get_company_from_token import get_company_from_token
from rest_framework.views import APIView
import logging

logger = logging.getLogger(__name__)

class CompanyScopedMixin:
    """
    Extracts company from access token (using your helper).
    Provides: self.company
    """

    def initial(self, request, *args, **kwargs):
        logger.debug("CompanyScopedMixin: Extracting company from token")
        company, error = get_company_from_token(request)

        if error:
            logger.debug(f"Token rejected: {error}")
            raise PermissionDenied(error.get("message", "Unauthorized"))

        self.company = company
        logger.debug(f"Company validated: {company.company_id}")

        return super().initial(request, *args, **kwargs)
