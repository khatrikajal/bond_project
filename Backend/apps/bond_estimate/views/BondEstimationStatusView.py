# views/bond_estimation_status.py

import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from config.common.response import APIResponse
from apps.bond_estimate.mixins.ApplicationScopedMixin import ApplicationScopedMixin
from apps.bond_estimate.services.bond_estimation_service import get_application_status_summary

logger = logging.getLogger(__name__)


class BondEstimationStatusAPI(ApplicationScopedMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, application_id):
        logger.debug(f"[BondEstimationStatusAPI] Started for {application_id}")

        try:
            application = self.application  # From mixin

            summary = get_application_status_summary(application)

            logger.debug(
                f"[BondEstimationStatusAPI] Summary for {application_id}: {summary}"
            )

            return APIResponse.success(
                message="Application status summary fetched",
                data=summary
            )

        except Exception as e:
            logger.error(
                f"[BondEstimationStatusAPI] ERROR for application {application_id}: {e}",
                exc_info=True
            )
            return APIResponse.error(
                "Failed to fetch status",
                status_code=500
            )
