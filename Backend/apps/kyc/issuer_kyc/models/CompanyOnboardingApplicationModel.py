from .BaseModel import BaseModel
from django.db import models
from django.utils import timezone
from apps.authentication.issureauth.model import User
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

    current_step = models.IntegerField(default=1)

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
            models.Index(fields=['current_step']),
        ]

    def __str__(self):
        return f"Application #{self.application_id} - {self.user.user_id}"

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

        if self.current_step == step:
            self.current_step = min(step + 1, 5)

        if self.status == "INITIATED":
            self.status = "IN_PROGRESS"

        self.save()

    def get_completion_percentage(self):
        total_steps = 5
        completed = sum(1 for s in self.step_completion.values() if s.get("completed"))
        return int((completed / total_steps) * 100)
    
    def update_state(self, step_number: int, completed=True, record_ids=None):
        """
        Updates onboarding state for a step with automatic merging, dedupe,
        cleanup of deleted records, and required behaviors for resume logic.

        Args:
            step_number (int): Step number (1 to N).
            completed (bool): Whether the step is completed.
            record_ids (int | list[int] | None): IDs of records for this step.

        Behavior:
            ✅ Merges record_ids with existing ones
            ✅ Removes deleted/missing records automatically
            ✅ Rejects duplicates
            ✅ Automatically adds timestamps
            ✅ Moves current_step forward
            ✅ Does not overwrite previous steps
            ✅ Perfect for multi-record steps (address, directors, documents)
        """
        from apps.kyc.issuer_kyc.services.onboarding_service import get_model_for_step
        step_key = str(step_number)

        # Existing state
        state = self.step_completion or {}
        step_state = state.get(step_key, {})

        # Normalize record_id input
        if record_ids is not None:
            if not isinstance(record_ids, list):
                record_ids = [record_ids]

            # Merge with existing IDs
            existing = step_state.get("record_id", [])
            merged_ids = list(set(existing + record_ids))   # dedupe

            # ✅ Auto-remove deleted records from DB
            model = get_model_for_step(step_number)
            #valid_ids = list(model.objects.filter(id__in=merged_ids).values_list("id", flat=True))
            pk_name = model._meta.pk.name  
            valid_ids = list(model.objects.filter(**{f"{pk_name}__in": merged_ids}).values_list(pk_name, flat=True))

            step_state["record_id"] = valid_ids

        # Set completion
        step_state["completed"] = completed

        if completed:
            step_state["completed_at"] = timezone.now().isoformat()

        # Update JSON
        state[step_key] = step_state
        self.step_completion = state

        # Move next step only if current matches
        if self.current_step == step_number:
            self.current_step = min(step_number + 1, 5)

        # Mark progress
        if self.status == "INITIATED":
            self.status = "IN_PROGRESS"

        self.save(update_fields=["step_completion", "current_step", "status"])

    def remove_record_id(self, step_number, record_id):
        state = self.step_completion or {}
        step_key = str(step_number)

        if step_key in state:
            ids = state[step_key].get("record_id", [])
            ids = [i for i in ids if i != record_id]
            state[step_key]["record_id"] = ids

            self.step_completion = state
            self.save(update_fields=["step_completion"])


