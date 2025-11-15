import uuid
from django.db import models
from django.contrib.auth import get_user_model

from apps.bond_estimate.models.BaseModel import BaseModel
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation

User = get_user_model()


class PreliminaryBondRequirements(BaseModel):
    """
    Preliminary Bond Requirements
    - All fields required
    - Category & Payment Cycle stored as JSON arrays
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company = models.ForeignKey(
        CompanyInformation,
        on_delete=models.CASCADE,
        related_name="preliminary_bond_requirements",
        db_index=True
    )

    issue_amount = models.DecimalField(max_digits=18, decimal_places=2)

    security_type = models.CharField(
        max_length=20,
        choices=(("Secured", "Secured"), ("Unsecured", "Unsecured"))
    )

    tenure = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Tenure in years"
    )

    preferred_roi = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Preferred ROI %"
    )

    # NEW FIELD (Coupon Rate)
    coupon_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Coupon Rate %"
    )

    # Multi-select field (required)
    preferred_investor_categories = models.JSONField()

    # Multi-select field (required)
    preferred_interest_payment_cycle = models.JSONField()

    class Meta:
        db_table = "preliminary_bond_requirements"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company", "del_flag"]),
            models.Index(fields=["security_type"]),
            models.Index(fields=["issue_amount"]),
            models.Index(fields=["coupon_rate"]),     # NEW INDEX
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Preliminary Bond Req - {self.company.company_name if self.company else ''}"
