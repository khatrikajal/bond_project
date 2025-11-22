from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from apps.bond_estimate.models.BaseModel import BaseModel
from apps.bond_estimate.models.BondEstimationApplicationModel import BondEstimationApplication


# ------------------------------------------------------------
# Custom QuerySet to eliminate N+1 queries
# ------------------------------------------------------------
class CapitalDetailsQuerySet(models.QuerySet):
    def with_application(self):
        return self.select_related("application")

    def active(self):
        return self.filter(del_flag=0)

    def for_application(self, application_id):
        return self.with_application().filter(application_id=application_id)


# ------------------------------------------------------------
# Manager applying QuerySet rules globally
# ------------------------------------------------------------
class CapitalDetailsManager(models.Manager):
    def get_queryset(self):
        return CapitalDetailsQuerySet(self.model, using=self._db).with_application()

    def active(self):
        return self.get_queryset().active()

    def for_application(self, application_id):
        return self.get_queryset().for_application(application_id)


class CapitalDetails(BaseModel):
    """
    Stores capital-related financial information for a Bond Estimation Application.
    Only one capital structure can exist per application.
    """

    capital_detail_id = models.BigAutoField(primary_key=True)

    application = models.OneToOneField(
        BondEstimationApplication,
        on_delete=models.CASCADE,
        related_name='capital_details',
        db_column='application_id',
        help_text="Bond estimation application this capital data belongs to."
    )

    share_capital = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    reserves_surplus = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    net_worth = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Attach optimized manager
    objects = CapitalDetailsManager()

    class Meta:
        db_table = "capital_details"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["application"], name="idx_capital_app"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["application"],
                name="unique_capital_details_per_application"
            )
        ]

    def __str__(self):
        return f"Capital Details – Application {self.application.application_id}"

    # --------------------------------
    # Clean & Validate Model
    # --------------------------------
    def clean(self):
        """Ensure no negative values accidentally saved."""
        if self.share_capital is not None and self.share_capital < 0:
            raise ValueError("Share capital cannot be negative.")

        if self.reserves_surplus is not None and self.reserves_surplus < 0:
            raise ValueError("Reserves & Surplus cannot be negative.")

    # --------------------------------
    # Override Save (Auto Calculate Net Worth)
    # --------------------------------
    def save(self, *args, **kwargs):
        # Safely convert to Decimal (avoiding float operations)
        share_capital = Decimal(self.share_capital or 0)
        reserves_surplus = Decimal(self.reserves_surplus or 0)

        self.net_worth = share_capital + reserves_surplus
        super().save(*args, **kwargs)
