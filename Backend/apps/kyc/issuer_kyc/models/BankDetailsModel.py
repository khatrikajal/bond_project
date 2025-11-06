from django.db import models
from apps.kyc.issuer_kyc.models.BaseModel import BaseModel
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation



class BankDetails(BaseModel):
    ACCOUNT_TYPES = [
        ("SAVINGS", "Savings"),
        ("CURRENT", "Current"),
    ]
    bank_detail_id = models.BigAutoField(primary_key=True)

    company = models.OneToOneField(
        CompanyInformation,
        on_delete=models.CASCADE,
        related_name="bank_details"
    )

    # Documents
    cancelled_cheque = models.FileField(
        upload_to="onboarding/bank/cancelled_cheques/",
        null=True, blank=True
    )
    bank_statement = models.FileField(
        upload_to="onboarding/bank/statements/",
        null=True, blank=True
    )
    passbook = models.FileField(
        upload_to="onboarding/bank/passbooks/",
        null=True, blank=True
    )

    # Bank fields
    bank_name = models.CharField(max_length=100)
    branch_name = models.CharField(max_length=150)
    account_number = models.CharField(max_length=30)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    ifsc_code = models.CharField(max_length=11)


    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True)
   
    class Meta:
        db_table = "bank_details"
        indexes = [
            models.Index(fields=["company", "del_flag"]),
            models.Index(fields=["ifsc_code"]),
        ]

    def __str__(self):
        return f"Bank Details for {self.company.company_name}"
