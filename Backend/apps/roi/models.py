# D:\BOnd\bond_project\Backend\apps\roi\models.py
from django.db import models
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from apps.authentication.issureauth.models import User


# ---------- 1. Fund Position ----------
class FundPosition(models.Model):
    fund_position_id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(CompanyInformation, on_delete=models.CASCADE, related_name="fund_positions")
    cash_balance_as_on_date = models.DateField()
    bank_balance_as_on_date = models.DateField()
    cash_balance_amount = models.DecimalField(max_digits=18, decimal_places=2)
    bank_balance_amount = models.DecimalField(max_digits=18, decimal_places=2)
    remarks = models.TextField(null=True, blank=True)
    is_del = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_id_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "roi_fund_position"
        indexes = [
            models.Index(fields=["company", "is_del"]),
        ]


# ---------- 2. Credit Rating Details ----------
class CreditRating(models.Model):
    credit_rating_id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(CompanyInformation, on_delete=models.CASCADE, related_name="credit_ratings")
    agency = models.CharField(max_length=50)
    rating = models.CharField(max_length=10)
    valid_till = models.DateField()
    additional_rating = models.CharField(max_length=255, null=True, blank=True)
    upload_letter = models.FileField(upload_to="uploads/credit_ratings/", null=True, blank=True)
    is_del = models.SmallIntegerField(default=0)
    reting_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_id_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "roi_credit_rating"
        indexes = [
            models.Index(fields=["company", "is_del"]),
        ]


# ---------- 3. Borrowing Details ----------
class BorrowingDetail(models.Model):
    BORROWING_TYPE_CHOICES = [
        ("TERM_LOAN", "Term Loan"),
        ("WC", "Working Capital"),
        ("ECB", "External Commercial Borrowing"),
    ]
    REPAYMENT_TERM_CHOICES = [
        ("MONTHLY", "Monthly"),
        ("QUARTERLY", "Quarterly"),
    ]

    borrowing_id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(CompanyInformation, on_delete=models.CASCADE, related_name="borrowings")
    lender_name = models.CharField(max_length=255)
    lender_amount = models.DecimalField(max_digits=18, decimal_places=2)
    borrowing_type = models.CharField(max_length=50, choices=BORROWING_TYPE_CHOICES)
    repayment_terms = models.CharField(max_length=50, choices=REPAYMENT_TERM_CHOICES)
    monthly_principal_payment = models.DecimalField(max_digits=18, decimal_places=2)
    interest_payment_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    monthly_interest_payment = models.DecimalField(max_digits=18, decimal_places=2)
    is_del = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_id_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "roi_borrowing_detail"
        indexes = [
            models.Index(fields=["company", "is_del"]),
        ]


# ---------- 4. Capital Details ----------
class CapitalDetail(models.Model):
    capital_detail_id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(CompanyInformation, on_delete=models.CASCADE, related_name="capital_details")
    share_capital = models.DecimalField(max_digits=18, decimal_places=2)
    reserves_surplus = models.DecimalField(max_digits=18, decimal_places=2)
    net_worth = models.DecimalField(max_digits=18, decimal_places=2)
    is_del = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_id_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "roi_capital_detail"
        indexes = [
            models.Index(fields=["company", "is_del"]),
        ]


# ---------- 5. Profitability & Ratios ----------
class ProfitabilityRatio(models.Model):
    ratio_id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(CompanyInformation, on_delete=models.CASCADE, related_name="profitability_ratios")
    net_worth = models.DecimalField(max_digits=18, decimal_places=2)
    ebitda = models.DecimalField(max_digits=18, decimal_places=2)
    debt_equity_ratio = models.DecimalField(max_digits=10, decimal_places=4)
    current_ratio = models.DecimalField(max_digits=10, decimal_places=4)
    quick_ratio = models.DecimalField(max_digits=10, decimal_places=4)
    return_on_equity = models.DecimalField(max_digits=5, decimal_places=2)
    return_on_assets = models.DecimalField(max_digits=5, decimal_places=2)
    dscr = models.DecimalField(max_digits=10, decimal_places=4)
    is_del = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_id_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "roi_profitability_ratio"
        indexes = [
            models.Index(fields=["company", "is_del"]),
        ]
