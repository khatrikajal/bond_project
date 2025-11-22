from django.db import models
from apps.kyc.issuer_kyc.models.BaseModel import BaseModel
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation

class ActiveDematManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(del_flag=0)

class DematAccount(BaseModel):
    """
    Stores a company's demat account details.
    One company = one demat account.
    """

    demat_account_id = models.BigAutoField(primary_key=True)

    company = models.OneToOneField(
        CompanyInformation,
        on_delete=models.CASCADE,
        related_name="demat_account"
    )

    dp_name = models.CharField(max_length=50)

    DEPOSITORY_CHOICES = [
        ("NSDL", "NSDL"),
        ("CDSL", "CDSL"),
    ]
    depository_participant = models.CharField(
        max_length=10,
        choices=DEPOSITORY_CHOICES
    )

    dp_id = models.CharField(max_length=20)

    # Redundant storage for faster lookup
    demat_account_number = models.CharField(
        max_length=50,
        unique=True
    )

    client_id_bo_id = models.CharField(max_length=20, null=True, blank=True)

    # Audit tracking
    user_id_updated_by = models.BigIntegerField(null=True, blank=True)

    objects = models.Manager()  # Default
    active = ActiveDematManager()

    class Meta:
        db_table = "demat_accounts"
        # managed = False
        indexes = [
            models.Index(fields=["company", "del_flag"]),
            models.Index(fields=["dp_id"]),
            # ❌ Removed invalid beneficiary_client_id index
        ]

    def __str__(self):
        return f"Demat Account for {self.company.company_name}"
