from rest_framework.views import APIView
from rest_framework import permissions, status
from django.utils import timezone
from django.db import transaction
import logging

from config.common.response import APIResponse
from apps.kyc.issuer_kyc.models import CompanyOnboardingApplication
from apps.authentication.issureauth.models import User  # adjust import path if needed
from apps.kyc.issuer_kyc.services.financial_documents.financial_document_service import FinancialDocumentService

logger = logging.getLogger(__name__)


# class FinalSubmitAPIView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#     TOTAL_STEPS = 5

#     @transaction.atomic
#     def post(self, request, company_id, *args, **kwargs):
#         user = request.user

#         application = (
#             CompanyOnboardingApplication.objects
#             .select_related("company_information")
#             .filter(company_information_id=company_id, user=user)
#             .first()
#         )

#         if not application:
#             return APIResponse.error(
#                 message="No onboarding application found for this company.",
#                 status_code=status.HTTP_404_NOT_FOUND,
#             )

#         completion_info = self._evaluate_completion(application)
#         if not completion_info["all_completed"]:
#             return APIResponse.error(
#                 message="Please complete all KYC steps before submitting.",
#                 errors={"incomplete_steps": completion_info["incomplete_steps"]},
#                 status_code=status.HTTP_400_BAD_REQUEST,
#             )

#         # Decide final states in one place
#         decision = self._determine_state(application)

#         # 1) Update application status & timestamps according to decision
#         previous_app_status = application.status
#         application.status = decision["application_status"]
#         # ensure submitted_at set if moved to SUBMITTED (or keep existing)
#         if not application.submitted_at and decision.get("set_submitted_at", False):
#             application.submitted_at = timezone.now()
#         application.save(update_fields=["status", "submitted_at", "updated_at"])

#         logger.info(
#             f"[FinalSubmit] Application {application.application_id} moved "
#             f"{previous_app_status} → {application.status}"
#         )

#         # 2) Update user KYC status according to the same decision
#         previous_kyc = user.kyc_status
#         user.kyc_status = decision["user_kyc_status"]
#         user.save(update_fields=["kyc_status", "updated_at"])

#         logger.info(
#             f"[FinalSubmit] User {user.user_id} KYC status changed {previous_kyc} → {user.kyc_status}"
#         )

#         # 3) Build and return response
#         response_data = {
#             "kyc_completed": True,
#             "application_id": str(application.application_id),
#             "company_id": company_id,
#             "status": application.status,
#             "redirect_to": decision["redirect_to"],
#             "submitted_at": application.submitted_at,
#             "completion_percentage": application.get_completion_percentage(),
#         }

#         return APIResponse.success(
#             message=decision.get("message", "KYC submitted."),
#             data=response_data,
#             status_code=status.HTTP_200_OK,
#         )

#     # --------------- helpers ---------------

#     def _determine_state(self, application):
#         """
#         Single place to decide what happens after final submit.
#         Return dict:
#             {
#               "application_status": "SUBMITTED" | "APPROVED" | ...,
#               "user_kyc_status": "UNDER_REVIEW" | "APPROVED" | ...,
#               "redirect_to": "UNDER_REVIEW" | "COMPLETED" | ...,
#               "message": "..."
#               "set_submitted_at": True|False
#             }
#         Current behavior: always move to SUBMITTED / UNDER_REVIEW.
#         """
#         # FUTURE: add auto-approval checks here (document verification, pan/gst checks, flags, config toggles)
#         # Example placeholder (current simple behavior):
#         return {
#             "application_status": "SUBMITTED",
#             "user_kyc_status": "UNDER_REVIEW",
#             "redirect_to": "UNDER_REVIEW",
#             "message": "KYC submitted successfully and is now under review.",
#             "set_submitted_at": True,
#         }

#     def _evaluate_completion(self, application):
#         total_steps = self.TOTAL_STEPS
#         completed_steps, incomplete_steps, missing_details = [], [], {}

#         for step in range(1, total_steps + 1):
#             step_key = str(step)

#             if application.is_step_completed(step):
#                 completed_steps.append(step_key)
#             else:
#                 incomplete_steps.append(step_key)

#                 if step == 5:
#                     # ▶️ Detailed financial document breakdown
#                     missing_details[step_key] = FinancialDocumentService.get_missing_details(
#                         application.company_information.company_id
#                     )
#                 else:
#                     # ▶️ Generic message for other steps (keep simple)
#                     missing_details[step_key] = "Step incomplete"

#         all_completed = len(completed_steps) == total_steps

#         return {
#             "completed_steps": completed_steps,
#             "incomplete_steps": incomplete_steps,
#             "missing_details": missing_details,
#             "all_completed": all_completed,
#         }




class FinalSubmitAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    TOTAL_STEPS = 5

    @transaction.atomic
    def post(self, request, company_id, *args, **kwargs):
        user = request.user

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

        # Evaluate completion
        completion_info = self._evaluate_completion(application)

        if not completion_info["all_completed"]:
            return APIResponse.error(
                message="Please complete all KYC steps before submitting.",
                errors={
                    "incomplete_steps": completion_info["incomplete_steps"],
                    # "missing_details": completion_info["missing_details"],
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Decide final states
        decision = self._determine_state(application)

        # Update application
        previous_app_status = application.status
        application.status = decision["application_status"]
        if not application.submitted_at and decision.get("set_submitted_at", False):
            application.submitted_at = timezone.now()
        application.save(update_fields=["status", "submitted_at", "updated_at"])

        logger.info(
            f"[FinalSubmit] Application {application.application_id} moved "
            f"{previous_app_status} → {application.status}"
        )

        # Update user
        previous_kyc = user.kyc_status
        user.kyc_status = decision["user_kyc_status"]
        user.save(update_fields=["kyc_status", "updated_at"])

        logger.info(
            f"[FinalSubmit] User {user.user_id} KYC status changed {previous_kyc} → {user.kyc_status}"
        )

        # Build response
        response_data = {
            "kyc_completed": True,
            "application_id": str(application.application_id),
            "company_id": company_id,
            "status": application.status,
            "redirect_to": decision["redirect_to"],
            "submitted_at": application.submitted_at,
            # "completion_percentage": application.get_completion_percentage(),
        }

        return APIResponse.success(
            message=decision.get("message", "KYC submitted."),
            data=response_data,
            status_code=status.HTTP_200_OK,
        )

    # -------------------------------
    # Helpers
    # -------------------------------
    def _determine_state(self, application):
        return {
            "application_status": "SUBMITTED",
            "user_kyc_status": "UNDER_REVIEW",
            "redirect_to": "UNDER_REVIEW",
            "message": "KYC submitted successfully and is now under review.",
            "set_submitted_at": True,
        }

    def _evaluate_completion(self, application):
        total_steps = self.TOTAL_STEPS
        # completed_steps, incomplete_steps, missing_details = [], [], {}
        completed_steps, incomplete_steps = [], []

        for step in range(1, total_steps + 1):
            step_key = str(step)

            if application.is_step_completed(step):
                completed_steps.append(step_key)
            else:
                incomplete_steps.append(step_key)

                # if step == 5:
                #     missing_details[step_key] = FinancialDocumentService.get_missing_details(
                #         application.company_information.company_id
                #     )
                # else:
                #     missing_details[step_key] = "Step incomplete"

        all_completed = len(completed_steps) == total_steps

        return {
            "completed_steps": completed_steps,
            "incomplete_steps": incomplete_steps,
            # "missing_details": missing_details,
            # "all_completed": all_completed,
        }
