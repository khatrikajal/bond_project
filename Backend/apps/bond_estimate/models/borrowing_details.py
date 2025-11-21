import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.bond_estimate.models.BondEstimationApplicationModel import BondEstimationApplication


# ------------------------------------------------------------
# ENUMS
# ------------------------------------------------------------
class BorrowingType(models.TextChoices):
    SECURED = 'SECURED', 'Secured'
    UNSECURED = 'UNSECURED', 'Unsecured'
    SHORT_TERM = 'SHORT-TERM', 'Short Term'
    LONG_TERM = 'LONG-TERM', 'Long Term'
    INTERNAL = 'INTERNAL'
    EXTERNAL = 'EXTERNAL', 'External'


class RepaymentTerms(models.TextChoices):
    MONTHLY = 'MONTHLY', 'Monthly'
    QUARTERLY = 'QUARTERLY', 'Quarterly'
    HALF_YEARLY = 'HALF YEARLY', 'Half Yearly'
    ANNUALLY = 'ANNUALLY', 'Annually'


# ------------------------------------------------------------
# QuerySet optimized for N+1 prevention
# ------------------------------------------------------------
class BorrowingDetailsQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_del=0)

    def with_relations(self):
        return self.select_related("application")

    def for_application(self, application_id):
        return self.with_relations().filter(application_id=application_id, is_del=0)


# ------------------------------------------------------------
# Manager that enforces optimized queries globally
# ------------------------------------------------------------
class BorrowingDetailsManager(models.Manager):
    def get_queryset(self):
        return BorrowingDetailsQuerySet(self.model, using=self._db).with_relations()

    def active(self):
        return self.get_queryset().active()

    def for_application(self, application_id):
        return self.get_queryset().for_application(application_id)


# ------------------------------------------------------------
# MAIN MODEL
# ------------------------------------------------------------
class BorrowingDetails(models.Model):

    borrowing_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    application = models.ForeignKey(
        BondEstimationApplication,
        on_delete=models.CASCADE,
        related_name="borrowing_details",
        db_column="application_id",
        help_text="Bond Estimation Application reference"
    )

    lender_name = models.CharField(max_length=255)

    lender_amount = models.DecimalField(
        max_digits=18, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    borrowing_type = models.CharField(
        max_length=50,
        choices=BorrowingType.choices
    )

    repayment_terms = models.CharField(
        max_length=50,
        choices=RepaymentTerms.choices
    )

    monthly_principal_payment = models.DecimalField(
        max_digits=18, decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    interest_payment_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
        null=True,
        blank=True
    )

    monthly_interest_payment = models.DecimalField(
        max_digits=18, decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    is_del = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user_id_updated_by = models.UUIDField(null=True, blank=True)

    # Attach optimized manager
    objects = BorrowingDetailsManager()

    class Meta:
        db_table = "borrowing_details"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["application", "is_del"], name="idx_borrow_app_active"),
            models.Index(fields=["borrowing_type"], name="idx_borrow_type"),
            models.Index(fields=["created_at"], name="idx_borrow_created"),
            models.Index(fields=["is_del", "application", "-created_at"], name="idx_borrow_app_date"),
        ]

    # ------------------------------------------------------------
    # CLEAN VALIDATION
    # ------------------------------------------------------------
    def clean(self):
        if self.lender_amount <= 0:
            raise ValueError("Lender amount must be greater than zero")

        if self.monthly_principal_payment < 0:
            raise ValueError("Monthly principal payment cannot be negative")

        if self.monthly_interest_payment < 0:
            raise ValueError("Monthly interest payment cannot be negative")

    # ------------------------------------------------------------
    # SOFT DELETE & RESTORE
    # ------------------------------------------------------------
    def soft_delete(self, user_id=None):
        self.is_del = 1
        if user_id:
            self.user_id_updated_by = user_id
        self.save(update_fields=["is_del", "user_id_updated_by", "updated_at"])

    def restore(self, user_id=None):
        self.is_del = 0
        if user_id:
            self.user_id_updated_by = user_id
        self.save(update_fields=["is_del", "user_id_updated_by", "updated_at"])

    # ------------------------------------------------------------
    def __str__(self):
        return f"{self.lender_name} - {self.borrowing_type} - {self.lender_amount}"

    @property
    def is_active(self):
        return self.is_del == 0
