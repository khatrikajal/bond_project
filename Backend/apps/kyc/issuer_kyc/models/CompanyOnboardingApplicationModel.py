from apps.kyc.issuer_kyc.models.BaseModel import BaseModel
from django.db import models
from django.utils import timezone
from apps.authentication.issureauth.models import User
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

import uuid

class CompanyOnboardingApplication(BaseModel):
    """
    Master controller for the company onboarding flow.
    Tracks steps, resume logic, and final statuses.
    """

    APPLICATION_STATUS = [
        ('INITIATED', 'Initiated'),
        ('IN_PROGRESS', 'In Progress'),
        ('SUBMITTED', 'Submitted for Review'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    application_id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='company_applications'
    )

    status = models.CharField(
        max_length=20,
        choices=APPLICATION_STATUS,
        default='INITIATED',
        db_index=True
    )

    last_accessed_step = models.IntegerField(
        default=1,
        help_text="Last step user visited (analytics only)"
    )

    step_completion = models.JSONField(
        default=dict,
        blank=True,
        help_text="Tracks completion status of each onboarding step."
    )


    company_information = models.OneToOneField(
        "CompanyInformation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="application"
    )

    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "company_onboarding_applications"
        ordering = ['-created_at']
        managed = False
        indexes = [
            models.Index(fields=['user', 'status']),

        ]

    def __str__(self):
        return f"Application #{self.application_id} - {self.user.user_id}"

    # ==========================================
    # Core State Management
    # ==========================================

    def update_state(self, step_number: int, completed=True, record_ids=None):
        """
        Lightweight state tracker for onboarding steps.
        No validation logic here — validation is handled in serializers/views/models.

        Behavior:
            ✅ Merge and dedupe record_ids
            ✅ Remove IDs of deleted DB records (auto-clean)
            ✅ Track completed status
            ✅ Save timestamps when completed
            ✅ Mark application IN_PROGRESS automatically
        """

        step_key = str(step_number)
        logger.debug(f"[update_state] Called for step_number={step_key}, completed={completed}, record_ids={record_ids}")

        # Get existing state
        state = self.step_completion or {}
        logger.debug(f"[update_state] Current step_completion state: {state}")

        step_state = state.get(step_key, {})
        logger.debug(f"[update_state] Existing state for step {step_key}: {step_state}")

        # Normalize record_ids
        if record_ids is not None:
            if not isinstance(record_ids, list):
                record_ids = [record_ids]
                logger.debug(f"[update_state] Normalized record_ids to list: {record_ids}")

            existing = step_state.get("record_id", [])
            logger.debug(f"[update_state] Existing record_ids for step {step_key}: {existing}")

            merged_ids = list(set(existing + record_ids))
            logger.debug(f"[update_state] Merged and deduped record_ids: {merged_ids}")

            # Auto-remove deleted IDs using model lookup
            model = self._get_model_for_step(step_number)
            logger.debug(f"[update_state] Resolved model for step {step_key}: {model}")
            #changed here
            if model:
                valid_ids = list(
                    model.objects.filter(pk__in=merged_ids)
                    .values_list("pk", flat=True)
                )
                step_state["record_id"] = valid_ids
                logger.debug(f"[update_state] Valid record_ids after model lookup: {valid_ids}")
            else:
                step_state["record_id"] = merged_ids
                logger.debug(f"[update_state] No model found — keeping merged record_ids: {merged_ids}")

        # Set completion status
        step_state["completed"] = completed
        logger.debug(f"[update_state] Step {step_key} completion status set to: {completed}")

        if completed:
            completed_at = timezone.now().isoformat()
            step_state["completed_at"] = completed_at
            logger.debug(f"[update_state] Step {step_key} marked completed at {completed_at}")

        # Update JSON state
        state[step_key] = step_state
        self.step_completion = state
        logger.debug(f"[update_state] Updated step_completion JSON: {state}")

        # Move to IN_PROGRESS if starting journey
        if self.status == "INITIATED":
            self.status = "IN_PROGRESS"
            logger.debug("[update_state] Status moved from INITIATED → IN_PROGRESS")

        self.save(update_fields=["step_completion", "status", "updated_at"])
        logger.debug("[update_state] State saved successfully to DB")



    def remove_record_id(self, step_number: int, record_id: int):
        """
        Remove a specific record ID from a step's state.
        Useful when user deletes a document or address.
        """
        state = self.step_completion or {}
        step_key = str(step_number)
        
        if step_key in state:
            ids = state[step_key].get("record_id", [])
            ids = [i for i in ids if i != record_id]
            state[step_key]["record_id"] = ids
            
            # If no records left, mark incomplete
            if not ids:
                state[step_key]["completed"] = False
            
            self.step_completion = state
            self.save(update_fields=["step_completion", "updated_at"])

    def mark_step_incomplete(self, step_number: int, reason: str = None):
        """
        Mark step explicitly incomplete.
        Useful when user deletes data or step becomes invalid externally.
        """
        step_key = str(step_number)
        state = self.step_completion or {}

        if step_key not in state:
            state[step_key] = {}

        state[step_key].update({
            "completed": False,
            "incomplete_reason": reason,
            "updated_at": timezone.now().isoformat()
        })

        self.step_completion = state
        self.save(update_fields=["step_completion", "updated_at"])


    # ==========================================
    # Helper Methods
    # ==========================================

    def _get_model_for_step(self, step_number: int):
        """Get the model class for a given step"""
        from apps.kyc.issuer_kyc.services.onboarding_service import get_model_for_step
        return get_model_for_step(step_number)

    def is_step_completed(self, step: int) -> bool:
        """Check if a step is marked as completed"""
        return self.step_completion.get(str(step), {}).get("completed", False)

    def get_step_status(self, step: int) -> dict:
        """Get detailed status for a step"""
        step_data = self.step_completion.get(str(step), {})
        
        return {
            "step": step,
            "completed": step_data.get("completed", False),
            "completed_at": step_data.get("completed_at"),
            "is_valid": step_data.get("is_valid", False),
            "validation_errors": step_data.get("validation_errors", []),
            "record_id": step_data.get("record_id"),
        }

    def get_completion_percentage(self) -> int:
        """Calculate overall completion percentage"""
        total_steps = 5
        completed = sum(1 for s in range(1, 6) if self.is_step_completed(s))
        return int((completed / total_steps) * 100)