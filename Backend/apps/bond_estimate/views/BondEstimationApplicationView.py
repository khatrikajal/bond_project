from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from config.common.response import APIResponse
from ..models.BondEstimationApplicationModel import BondEstimationApplication
from config.mixins.company_scoped_mixin import CompanyScopedMixin
import logging

logger = logging.getLogger(__name__)

class CreateBondEstimationApplicationAPI(CompanyScopedMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, company_id):
        logger.debug(f"Creating blank application for company={company_id}")

        app = BondEstimationApplication.objects.create(
            user=request.user,
            company=self.company,
            status="DRAFT",
            last_accessed_step=1,
            step_progress={}
        )

        logger.debug(f"Application created: {app.application_id}")

        return APIResponse.success(
            message="Application created successfully",
            data={
                "application_id": str(app.application_id),
                "status": app.status,
                "created_at": app.created_at,
            },
            status_code=201
        )



class ListCompanyBondApplicationsAPI(CompanyScopedMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        logger.debug(f"Fetching applications for company={company_id}")

        apps = BondEstimationApplication.objects.filter(
            company=self.company
        ).order_by("-created_at")

        data = [
            {
                "application_id": str(app.application_id),
                "status": app.status,
                "last_accessed_step": app.last_accessed_step,
                "created_at": app.created_at,
                "updated_at": app.updated_at,
            }
            for app in apps
        ]

        logger.debug(f"Found {len(data)} applications")

        return APIResponse.success(
            message="Applications fetched successfully",
            data=data
        )



from rest_framework.exceptions import PermissionDenied

class UpdateLastAccessedStepAPI(CompanyScopedMixin, APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, company_id, application_id):
        logger.debug(f"Update last accessed API hit for app={application_id}")

        step = request.data.get("step")

        if not step:
            return APIResponse.error("Missing 'step' field", 400)

        try:
            app = BondEstimationApplication.objects.get(
                application_id=application_id,
                company=self.company,
            )
        except BondEstimationApplication.DoesNotExist:
            logger.debug("App not found or unauthorized access")
            raise PermissionDenied("Invalid application or access denied")

        app.last_accessed_step = step
        app.save(update_fields=["last_accessed_step", "updated_at"])

        logger.debug(f"Updated last_accessed_step={step} for app={application_id}")

        return APIResponse.success(
            message="Last accessed step updated",
            data={"application_id": str(app.application_id), "last_accessed_step": step}
        )
