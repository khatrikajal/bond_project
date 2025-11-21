from django.db import models
from apps.bond_estimate.models.BaseModel import BaseModel
from apps.bond_estimate.models.BondEstimationApplicationModel import BondEstimationApplication


# ------------------------------------------------------------
# QuerySet optimized for N+1 prevention
# ------------------------------------------------------------
class ProfitabilityRatiosQuerySet(models.QuerySet):
    def with_relations(self):
        return self.select_related("application")


# ------------------------------------------------------------
# Manager that enforces select_related globally
# ------------------------------------------------------------
class ProfitabilityRatiosManager(models.Manager):
    def get_queryset(self):
        return ProfitabilityRatiosQuerySet(self.model, using=self._db).with_relations()


class ProfitabilityRatios(BaseModel):
    """
    Stores profitability & financial ratios for a Bond Estimation Application.
    One record per application.
    """

    ratio_id = models.BigAutoField(primary_key=True)

    application = models.OneToOneField(
        BondEstimationApplication,
        on_delete=models.CASCADE,
        related_name='profitability_ratios',
        db_column='application_id',
        help_text="Bond estimation application this ratio set belongs to."
    )

    net_profit = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    net_worth = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    ebitda = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    debt_equity_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    current_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    quick_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    return_on_equity = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    return_on_assets = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    dscr = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Debt-Service Coverage Ratio"
    )

    # Optimized manager
    objects = ProfitabilityRatiosManager()

    class Meta:
        db_table = "profitability_ratios"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["application"], name="idx_profitability_application"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["application"], name="unique_profitability_per_application"
            )
        ]

    def __str__(self):
        return f"Profitability Ratios – Application {self.application.application_id}"
