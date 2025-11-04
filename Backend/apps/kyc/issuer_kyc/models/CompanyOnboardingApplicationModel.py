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
    last_accessed_step = models.IntegerField(default=1)

    # current_step = models.IntegerField(default=1)

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
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['last_accessed_step']),
        ]

    def __str__(self):
        return f"Application #{self.application_id} - {self.user.username}"

    # ---------------------------------------------------
    # ✅ Resume Logic Helper Methods
    # ---------------------------------------------------

    def is_step_completed(self, step):
        return self.step_completion.get(str(step), {}).get("completed", False)

    def get_next_incomplete_step(self):
        for step in range(1, 6):
            if not self.is_step_completed(step):
                return step
        return 5

    def can_proceed_to_step(self, target_step):
        if target_step == 1:
            return True
        for s in range(1, target_step):
            if not self.is_step_completed(s):
                return False
        return True

    def mark_step_complete(self, step, record_id=None):
        self.step_completion[str(step)] = {
            "completed": True,
            "completed_at": timezone.now().isoformat(),
            "record_id": record_id,
        }

        # if self.last_accessed_step == step:
        #     self.last_accessed_step = min(step + 1, 5)

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


