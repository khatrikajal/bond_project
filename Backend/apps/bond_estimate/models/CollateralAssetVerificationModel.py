import uuid
from django.db import models
from django.contrib.auth import get_user_model

from apps.bond_estimate.models.BaseModel import BaseModel
from apps.bond_estimate.models.BondEstimationApplicationModel import BondEstimationApplication

User = get_user_model()


# ------------------------------------------------------------
# Upload path helpers (fixed: use application → company)
# ------------------------------------------------------------
def security_document_upload_path(instance, filename):
    company_id = instance.application.company.company_id
    return f"{company_id}/bond_estimate/collateral_asset_verification/security_document/{filename}"

def asset_cover_certificate_upload_path(instance, filename):
    company_id = instance.application.company.company_id
    return f"{company_id}/bond_estimate/collateral_asset_verification/asset_cover_certificate/{filename}"

def valuation_report_upload_path(instance, filename):
    company_id = instance.application.company.company_id
    return f"{company_id}/bond_estimate/collateral_asset_verification/valuation_report/{filename}"


# ------------------------------------------------------------
# QuerySet optimized for N+1 prevention
# ------------------------------------------------------------
class CollateralAssetQuerySet(models.QuerySet):
    def with_relations(self):
        return self.select_related("application", "application__company")


# ------------------------------------------------------------
# Manager to enforce select_related globally
# ------------------------------------------------------------
class CollateralAssetManager(models.Manager):
    def get_queryset(self):
        return CollateralAssetQuerySet(self.model, using=self._db).with_relations()


class CollateralAssetVerification(BaseModel):

    collateral_asset_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    application = models.OneToOneField(
        BondEstimationApplication,
        on_delete=models.CASCADE,
        related_name='collateral_asset_verification',
        db_column='application_id',
        help_text="Bond estimation application this collateral belongs to."
    )

    collateral_type = models.CharField(
        max_length=50,
        choices=(
            ("LAND", "Land"),
            ("EQUIPMENT", "Equipment"),
            ("RECEIVABLES", "Receivables"),
            ("SHARES", "Shares"),
            ("PROJECT ASSETS", "Project Assets"),
        )
    )

    charge_type = models.CharField(
        max_length=50,
        choices=(
            ("FIRST CHARGE", "First Charge"),
            ("SECOND CHARGE", "Second Charge"),
            ("EXCLUSIVE CHARGE", "Exclusive Charge"),
            ("PARI PASSU CHARGE", "Pari Passu Charge"),
            ("SUBSERVIENT CHARGE", "Subservient Charge"),
        )
    )

    asset_description = models.TextField()

    estimated_value = models.DecimalField(max_digits=18, decimal_places=2)

    valuation_date = models.DateField()

    security_document_file = models.FileField(
        upload_to=security_document_upload_path,
        max_length=500,
        null=True,
        blank=True
    )

    security_document_ref = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    trust_name = models.CharField(max_length=255)

    ownership_type = models.CharField(
        max_length=50,
        choices=(
            ("OWNED", "Owned"),
            ("LEASED", "Leased"),
            ("PLEDGED", "Pledged"),
        )
    )

    asset_cover_certificate = models.FileField(
        upload_to=asset_cover_certificate_upload_path,
        max_length=500,
        null=True,
        blank=True
    )

    valuation_report = models.FileField(
        upload_to=valuation_report_upload_path,
        max_length=500,
        null=True,
        blank=True
    )

    remarks = models.TextField(null=True, blank=True)

    objects = CollateralAssetManager()

    class Meta:
        db_table = "collateral_asset_verification"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["application"], name="idx_collateral_application"),
            models.Index(fields=["collateral_type"], name="idx_collateral_type"),
            models.Index(fields=["charge_type"], name="idx_collateral_charge"),
            models.Index(fields=["ownership_type"], name="idx_collateral_ownership"),
            models.Index(fields=["created_at"], name="idx_collateral_created_at"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["application"],
                name="unique_collateral_per_application",
            )
        ]

    def __str__(self):
        company_name = self.application.company.company_name
        return f"Collateral – {company_name}"
