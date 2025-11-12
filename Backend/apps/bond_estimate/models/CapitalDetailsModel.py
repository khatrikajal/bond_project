
from django.db import models
from apps.bond_estimate.models.BaseModel import BaseModel
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation


class CapitalDetails(BaseModel):
    """
    Stores capital-related financial information for a company.
    """

    capital_detail_id = models.BigAutoField(primary_key=True)

    company = models.ForeignKey(
        CompanyInformation,
        on_delete=models.CASCADE,
        related_name='credit_ratings',
        help_text="Linked company for which the rating is issued."
    )

    share_capital = models.DecimalField(
        max_digits=18, decimal_places=2, null=False
    )

    reserves_surplus = models.DecimalField(
        max_digits=18, decimal_places=2, null=False
    )

    net_worth = models.DecimalField(
        max_digits=18, decimal_places=2, null=False
    )

   
    class Meta:
        db_table = "capital_details"
        indexes = [
            models.Index(fields=["company"]),
        ]

    def __str__(self):
        return f"Capital Details – {self.company.company_name}"
