import uuid
from django.db import models
from django.contrib.auth import get_user_model
from apps.bond_estimate.models.BaseModel import BaseModel
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation

User = get_user_model()

# ============================
# TOP-LEVEL MIGRATION-SAFE FUNCTIONS
# ============================

def security_document_upload_path(instance, filename):
    company_id = instance.company.company_id
    return f"{company_id}/bond_estimate/collateral_asset_verification/security_document/{filename}"

def asset_cover_certificate_upload_path(instance, filename):
    company_id = instance.company.company_id
    return f"{company_id}/bond_estimate/collateral_asset_verification/asset_cover_certificate/{filename}"

def valuation_report_upload_path(instance, filename):
    company_id = instance.company.company_id
    return f"{company_id}/bond_estimate/collateral_asset_verification/valuation_report/{filename}"


class CollateralAssetVerification(BaseModel):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company = models.ForeignKey(
        CompanyInformation,
        on_delete=models.CASCADE,
        related_name="collateral_assets",
        db_index=True
    )

    collateral_type = models.CharField(
        max_length=50,
        choices=(
            ("Land", "Land"),
            ("Equipment", "Equipment"),
            ("Receivables", "Receivables"),
            ("Shares", "Shares"),
            ("Project Assets", "Project Assets"),
        )
    )

    charge_type = models.CharField(
        max_length=50,
        choices=(
            ("First Charge", "First Charge"),
            ("Second Charge", "Second Charge"),
            ("Exclusive Charge", "Exclusive Charge"),
            ("Pari Passu Charge", "Pari Passu Charge"),
            ("Subservient Charge", "Subservient Charge"),
        )
    )

    asset_description = models.TextField()

    estimated_value = models.DecimalField(max_digits=18, decimal_places=2)

    valuation_date = models.DateField()

    # =============================
    # FIXED: increase max_length
    # =============================
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
            ("Owned", "Owned"),
            ("Leased", "Leased"),
            ("Pledged", "Pledged"),
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

    class Meta:
        db_table = "collateral_asset_verification"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company", "del_flag"]),
            models.Index(fields=["collateral_type"]),
            models.Index(fields=["charge_type"]),
            models.Index(fields=["ownership_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Collateral - {self.company.company_name if self.company else ''}"
