import uuid
from django.db import models
from apps.bond_estimate.models.BaseModel import BaseModel
from apps.bond_estimate.models.BondEstimationApplicationModel import BondEstimationApplication


# ------------------------------------------------------------
# Custom QuerySet optimized for N+1 prevention
# ------------------------------------------------------------
class FundPositionQuerySet(models.QuerySet):
    def active(self):
        return self.filter(del_flag=0)

    def with_relations(self):
        return self.select_related("application")

    def for_application(self, application_id):
        return self.active().filter(application_id=application_id).with_relations()


# ------------------------------------------------------------
# Manager enforcing optimized QuerySet globally
# ------------------------------------------------------------
class FundPositionManager(models.Manager):
    def get_queryset(self):
        return FundPositionQuerySet(self.model, using=self._db).with_relations()

    def active(self):
        return self.get_queryset().active()

    def for_application(self, application_id):
        return self.get_queryset().for_application(application_id)


class FundPosition(BaseModel):
    """
    Stores Cash & Bank Position for a Bond Estimation Application.
    One record per application.
    """

    fund_position_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Primary key (UUID)"
    )

    application = models.OneToOneField(
        BondEstimationApplication,
        on_delete=models.CASCADE,
        related_name='fund_position',
        db_column='application_id',
        help_text="Bond estimation application reference"
    )

    cash_balance_date = models.DateField(db_index=True)
    bank_balance_date = models.DateField(db_index=True)

    cash_balance_amount = models.DecimalField(max_digits=15, decimal_places=2)
    bank_balance_amount = models.DecimalField(max_digits=15, decimal_places=2)

    remarks = models.TextField(null=True, blank=True)

    objects = FundPositionManager()

    class Meta:
        db_table = "fund_position"
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["application"], name="idx_fund_pos_app"),
            models.Index(fields=["cash_balance_date"], name="idx_fund_pos_cash_dt"),
            models.Index(fields=["bank_balance_date"], name="idx_fund_pos_bank_dt"),
            models.Index(fields=["user_id_updated_by", "created_at"], name="idx_fund_pos_user_created"),
            models.Index(fields=["del_flag", "application", "created_at"], name="idx_fund_pos_list"),
        ]

        constraints = [
            models.UniqueConstraint(fields=["application"], name="unique_fund_position_application"),            
            models.CheckConstraint(
                check=models.Q(cash_balance_amount__gte=0),
                name="check_cash_balance_positive"
            ),
            models.CheckConstraint(
                check=models.Q(bank_balance_amount__gte=0),
                name="check_bank_balance_positive"
            ),
            models.CheckConstraint(
                check=models.Q(del_flag__in=[0, 1]),
                name="check_del_flag_valid"
            ),
        ]

    def __str__(self):
        return f"Fund Position – Application {self.application.application_id}"

    def soft_delete(self, user=None):
        """Soft delete record"""
        self.del_flag = 1
        if user:
            self.user_id_updated_by = user
        self.save(update_fields=["del_flag", "user_id_updated_by", "updated_at"])

    @property
    def total_balance(self):
        return self.cash_balance_amount + self.bank_balance_amount
