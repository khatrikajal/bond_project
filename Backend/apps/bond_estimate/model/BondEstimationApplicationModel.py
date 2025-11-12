import uuid
from django.db import models
from apps.authentication.issureauth.models import User
from django.utils import timezone
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation



class BondEstimationApplication(models.Model):
    """
    Manages step-by-step workflow for bond estimation.
    Stores nested step state in JSON.
    """

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("IN_PROGRESS", "In Progress"),
        ("READY_FOR_CALCULATION", "Ready For Calculation"),
        ("COMPLETED", "Completed"),
        ("ARCHIVED", "Archived"),
    ]

    application_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="bond_estimations"
    )

    company = models.ForeignKey(
        CompanyInformation,
        on_delete=models.CASCADE,
        related_name="bond_estimations"
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="DRAFT",
        db_index=True
    )
    last_accessed_step = models.IntegerField(
        default=1,
        help_text="Last step user visited (analytics only)"
    )


    step_progress = models.JSONField(default=dict, blank=True)

    submitted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bond_estimation_applications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"Bond Estimation - {self.company.company_name}"

    # --------------------------------------------------
    # Step update API
    # --------------------------------------------------

    def mark_step(
        self,
        step_id: str,
        *,
        completed: bool = False,
        record_ids=None,
        metadata=None
    ):
        progress = self.step_progress or {}

        parts = step_id.split(".")
        main = parts[0]
        is_sub = len(parts) > 1
        now = timezone.now().isoformat()

        # create step bucket if missing
        if main not in progress:
            progress[main] = {"completed": False, "sub": {}}

        if is_sub:
            # substep update
            sub = progress[main]["sub"].setdefault(step_id, {})
            sub["completed"] = completed
            sub["updated_at"] = now

            if completed:
                sub["completed_at"] = now

            if record_ids:
                existing = sub.get("record_ids", [])
                sub["record_ids"] = list(set(existing + record_ids))

            if metadata:
                sub["metadata"] = metadata

            # auto-complete main when all substeps complete
            all_done = all(
                x.get("completed", False)
                for x in progress[main]["sub"].values()
            )
            progress[main]["completed"] = all_done
            if all_done:
                progress[main]["completed_at"] = now

        else:
            # main step update
            step = progress[main]
            step["completed"] = completed
            step["updated_at"] = now

            if completed:
                step["completed_at"] = now

            if metadata:
                step["metadata"] = metadata

        # save
        self.step_progress = progress

        if self.status == "DRAFT":
            self.status = "IN_PROGRESS"

        self.save(update_fields=["step_progress", "status", "updated_at"])
        return self

    # --------------------------------------------------
    def is_step_completed(self, step_id: str) -> bool:
        parts = step_id.split(".")
        main = parts[0]
        data = self.step_progress.get(main, {})

        if len(parts) > 1:
            return data.get("sub", {}).get(step_id, {}).get("completed", False)

        return data.get("completed", False)

    # --------------------------------------------------
    def get_step_state(self, step_id: str) -> dict:
        parts = step_id.split(".")
        main = parts[0]
        data = self.step_progress.get(main, {})

        if len(parts) > 1:
            return data.get("sub", {}).get(step_id, {})

        return data