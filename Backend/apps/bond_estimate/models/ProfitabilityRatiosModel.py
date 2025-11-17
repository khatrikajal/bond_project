from django.db import models
from apps.bond_estimate.models.BaseModel import BaseModel
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation


class ProfitabilityRatios(BaseModel):
    """
    Stores profitability & financial ratios for a company.
    One-to-one with CompanyInformation because each company has a single ratio set.
    """

    ratio_id = models.BigAutoField(primary_key=True)

    company = models.ForeignKey(
        CompanyInformation,
        on_delete=models.CASCADE,
        related_name="profitability_ratios",
        help_text="Company for which the profitability and ratios are recorded.",
        null=True, blank=True
    )

    net_profit = models.DecimalField(
        max_digits=18, decimal_places=2,
        null=True, blank=True,
        help_text="Net profit amount"
    )

    net_worth = models.DecimalField(
        max_digits=18, decimal_places=2,
        null=True, blank=True
    )

    ebitda = models.DecimalField(
        max_digits=18, decimal_places=2,
        null=True, blank=True
    )

    debt_equity_ratio = models.DecimalField(
        max_digits=10, decimal_places=4,
        null=True, blank=True
    )

    current_ratio = models.DecimalField(
        max_digits=10, decimal_places=4,
        null=True, blank=True
    )

    quick_ratio = models.DecimalField(
        max_digits=10, decimal_places=4,
        null=True, blank=True
    )

    return_on_equity = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text="ROE percentage"
    )

    return_on_assets = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text="ROA percentage"
    )

    dscr = models.DecimalField(
        max_digits=10, decimal_places=4,
        null=True, blank=True,
        help_text="Debt-Service Coverage Ratio"
    )

    class Meta:
        db_table = "profitability_ratios"
        indexes = [
            models.Index(fields=["company"]),
        ]

    def __str__(self):
        if self.company:
            return f"Profitability & Ratios – {self.company.company_name}"
        return "Profitability & Ratios – Unlinked Company"
