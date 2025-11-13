import uuid
from django.db import models
from apps.bond_estimate.models.BaseModel import BaseModel
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation


class FundPositionQuerySet(models.QuerySet):
    """Custom QuerySet with optimized queries"""

    def active(self):
        return self.filter(del_flag=0)

    def with_relations(self):
        return self.select_related("company", "user_id_updated_by")

    def for_company(self, company_id):
        return self.active().filter(company_id=company_id).with_relations()


class FundPositionManager(models.Manager):
    def get_queryset(self):
        return FundPositionQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def with_relations(self):
        return self.get_queryset().with_relations()

    def for_company(self, company_id):
        return self.get_queryset().for_company(company_id)


class FundPosition(BaseModel):
    """
    UUID-based FundPosition table.
    Compatible with PostgreSQL and Django migrations.
    """

    # UUID Primary Key — Correct for your new table
    fund_position_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Primary key (UUID)"
    )

    company = models.ForeignKey(
        CompanyInformation,
        on_delete=models.CASCADE,
        related_name="fund_positions",
        db_column="company_id",
        help_text="Reference to company"
    )

    cash_balance_date = models.DateField(
        db_index=True,
        help_text="Date of cash balance"
    )

    bank_balance_date = models.DateField(
        db_index=True,
        help_text="Date of bank balance"
    )

    cash_balance_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Cash balance amount"
    )

    bank_balance_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Bank balance amount"
    )

    remarks = models.TextField(
        null=True,
        blank=True,
        help_text="Optional remarks"
    )

    # Custom manager
    objects = FundPositionManager()

    class Meta:
        db_table = "fund_position"
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["company", "del_flag"], name="idx_fund_pos_comp_del"),
            models.Index(fields=["company", "cash_balance_date"], name="idx_fund_pos_comp_cash_dt"),
            models.Index(fields=["company", "bank_balance_date"], name="idx_fund_pos_comp_bank_dt"),
            models.Index(fields=["user_id_updated_by", "created_at"], name="idx_fund_pos_user_created"),
            models.Index(fields=["company", "del_flag", "created_at"], name="idx_fund_pos_list"),
        ]

        constraints = [
            models.CheckConstraint(
                check=models.Q(cash_balance_amount__gte=0),
                name="check_cash_balance_positive",
            ),
            models.CheckConstraint(
                check=models.Q(bank_balance_amount__gte=0),
                name="check_bank_balance_positive",
            ),
            models.CheckConstraint(
                check=models.Q(del_flag__in=[0, 1]),
                name="check_del_flag_valid",
            ),
        ]

    def __str__(self):
        return f"Fund Position ({self.fund_position_id}) for {self.company.company_name}"

    def soft_delete(self, user=None):
        """Soft delete record"""
        self.del_flag = 1
        if user:
            self.user_id_updated_by = user
        self.save(update_fields=["del_flag", "user_id_updated_by", "updated_at"])

    @property
    def total_balance(self):
        return self.cash_balance_amount + self.bank_balance_amount
