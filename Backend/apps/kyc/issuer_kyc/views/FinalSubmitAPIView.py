from rest_framework.views import APIView
from rest_framework import permissions, status
from django.utils import timezone
from django.db import transaction
import logging

from config.common.response import APIResponse
from apps.kyc.issuer_kyc.models.CompanyOnboardingApplicationModel import CompanyOnboardingApplication

logger = logging.getLogger(__name__)




class FinalSubmitAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    TOTAL_STEPS = 5

    @transaction.atomic
    def post(self, request, company_id, *args, **kwargs):
        user = request.user

        # 1️⃣ Fetch the application for this company + user
        application = (
            CompanyOnboardingApplication.objects
            .select_related("company_information")
            .filter(company_information_id=company_id, user=user)
            .first()
        )

        if not application:
            return APIResponse.error(
                message="No onboarding application found for this company.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # 2️⃣ Validate completion
        completion_info = self._evaluate_completion(application)
        if not completion_info["all_completed"]:
            return APIResponse.error(
                message="Please complete all KYC steps before submitting.",
                errors={"incomplete_steps": completion_info["incomplete_steps"]},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # 3️⃣ Mark as submitted
        previous_status = application.status
        application.status = "SUBMITTED"
        application.submitted_at = timezone.now()
        application.save(update_fields=["status", "submitted_at", "updated_at"])

        logger.info(
            f"[FinalSubmit] User={user.id} submitted company={company_id} "
            f"Application {application.application_id} moved from {previous_status} → SUBMITTED"
        )

        # 4️⃣ Redirect logic
        redirect_to = self._determine_redirect(application)

        response_data = {
            "kyc_completed": True,
            "application_id": str(application.application_id),
            "company_id": company_id,
            "status": application.status,
            "redirect_to": redirect_to,
            "submitted_at": application.submitted_at,
            "completion_percentage": application.get_completion_percentage(),
        }

        return APIResponse.success(
            message="KYC submitted successfully. Awaiting manual review.",
            data=response_data,
            status_code=status.HTTP_200_OK,
        )

    # === Helpers ===
    def _evaluate_completion(self, application):
        total_steps = self.TOTAL_STEPS
        completed_steps = [
            str(s) for s in range(1, total_steps + 1)
            if application.is_step_completed(s)
        ]
        incomplete_steps = [
            str(s) for s in range(1, total_steps + 1)
            if s not in map(int, completed_steps)
        ]
        all_completed = len(completed_steps) == total_steps
        return {
            "completed_steps": completed_steps,
            "incomplete_steps": incomplete_steps,
            "all_completed": all_completed,
        }

    def _determine_redirect(self, application):
        # For now static
        return "UNDER_REVIEW"
