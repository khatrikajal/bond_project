import uuid
from django.db import models
from django.contrib.auth import get_user_model

from apps.bond_estimate.models.BaseModel import BaseModel
from apps.bond_estimate.models.BondEstimationApplicationModel import BondEstimationApplication

User = get_user_model()


# ------------------------------------------------------------
# Optimized QuerySet to eliminate N+1 queries
# ------------------------------------------------------------
class PreliminaryBondReqQuerySet(models.QuerySet):
    def with_application(self):
        return self.select_related("application")


# ------------------------------------------------------------
# Manager that globally enforces select_related
# ------------------------------------------------------------
class PreliminaryBondReqManager(models.Manager):
    def get_queryset(self):
        return PreliminaryBondReqQuerySet(self.model, using=self._db).with_application()


class PreliminaryBondRequirements(BaseModel):
    """
    Preliminary Bond Requirements (One per Application)
    """

    preliminarybond_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    application = models.OneToOneField(
        BondEstimationApplication,
        on_delete=models.CASCADE,
        related_name='preliminary_bond_requirements',
        db_column='application_id',
        help_text="Bond estimation application this preliminary requirement belongs to."
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

    coupon_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Coupon Rate %"
    )

    preferred_investor_categories = models.JSONField()
    preferred_interest_payment_cycle = models.JSONField()

    # Attach optimized manager
    objects = PreliminaryBondReqManager()

    class Meta:
        db_table = "preliminary_bond_requirements"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["application"], name="idx_prebond_application"),
            models.Index(fields=["security_type"], name="idx_prebond_security_type"),
            models.Index(fields=["issue_amount"], name="idx_prebond_issue_amount"),
            models.Index(fields=["coupon_rate"], name="idx_prebond_coupon_rate"),
            models.Index(fields=["created_at"], name="idx_prebond_created_at"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["application"], name="unique_prelim_req_per_application"
            )
        ]

    def __str__(self):
        return f"Preliminary Bond Requirements – Application {self.application.application_id}"
