from .BaseModel import BaseModel
from django.db import models
from django.utils import timezone
from apps.authentication.issureauth.models import User

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

        if self.current_step == step:
            self.current_step = min(step + 1, 5)

        if self.status == "INITIATED":
            self.status = "IN_PROGRESS"

        self.save()

    def get_completion_percentage(self):
        total_steps = 5
        completed = sum(1 for s in self.step_completion.values() if s.get("completed"))
        return int((completed / total_steps) * 100)

