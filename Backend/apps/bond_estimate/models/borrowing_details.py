from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class BorrowingType(models.TextChoices):
    """Enumeration for borrowing types"""
    
    SECURED = 'Secured', 'Secured'
    UNSECURED = 'Unsecured', 'Unsecured'
    SHORT_TERM = 'Short Term', 'Short Term'
    LONG_TERM = 'Long Term', 'Long Term'
    INTERNAL = 'Internal', 
    EXTERNAL = 'External', 'External'


class RepaymentTerms(models.TextChoices):
    """Enumeration for repayment terms"""
    MONTHLY = 'Monthly', 'Monthly'
    QUARTERLY = 'Quarterly', 'Quarterly'
    HALF_YEARLY = 'Half Yearly', 'Half Yearly'
    ANNUALLY = 'Annually', 'Annually'


class BorrowingDetails(models.Model):
    """
    Model to store borrowing details for companies
    Optimized with proper indexing and relationships
    Uses UUID for primary key for better scalability and security
    """
    borrowing_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column='borrowing_id',
        help_text='Unique identifier for borrowing record'
    )
    
    company_id = models.UUIDField(
        db_column='company_id',
        db_index=True,  # Index for faster lookups
        help_text='Foreign key reference to company_kyc table'
    )
    
    lender_name = models.CharField(
        max_length=255,
        db_column='lender_name',
        help_text='Name of the lending institution'
    )
    
    lender_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        db_column='lender_amount',
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Amount borrowed in currency'
    )
    
    borrowing_type = models.CharField(
        max_length=50,
        choices=BorrowingType.choices,
        db_column='borrowing_type',
        help_text='Type of borrowing (Term Loan/WC/ECB)'
    )
    
    repayment_terms = models.CharField(
        max_length=50,
        choices=RepaymentTerms.choices,
        db_column='repayment_terms',
        help_text='Frequency of repayment'
    )
    
    monthly_principal_payment = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        db_column='monthly_principal_payment',
        validators=[MinValueValidator(Decimal('0'))],
        help_text='Monthly principal payment amount'
    )
    
    interest_payment_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        db_column='interest_payment_percentage',
        validators=[
            MinValueValidator(Decimal('0')),
            MaxValueValidator(Decimal('100'))
        ],
        null=True,
        blank=True,
        help_text='Interest rate percentage (0-100)'
    )
    
    monthly_interest_payment = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        db_column='monthly_interest_payment',
        validators=[MinValueValidator(Decimal('0'))],
        help_text='Monthly interest payment amount'
    )
    
    is_del = models.SmallIntegerField(
        default=0,
        db_column='is_del',
        help_text='Soft delete flag (0=active, 1=deleted)'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_column='created_at',
        help_text='Record creation timestamp'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        db_column='updated_at',
        help_text='Last modification timestamp'
    )
    
    user_id_updated_by = models.UUIDField(
        db_column='user_id_updated_by',
        null=True,
        blank=True,
        help_text='User ID who last updated the record'
    )

    class Meta:
        db_table = 'borrowing_details'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company_id', 'is_del'], name='idx_company_active'),
            models.Index(fields=['borrowing_type'], name='idx_borrowing_type'),
            models.Index(fields=['created_at'], name='idx_created_at'),
            models.Index(fields=['is_del', 'company_id', '-created_at'], name='idx_active_company_date'),
        ]
        verbose_name = 'Borrowing Detail'
        verbose_name_plural = 'Borrowing Details'

    def __str__(self):
        return f"{self.lender_name} - {self.borrowing_type} - {self.lender_amount}"

    @property
    def is_active(self):
        """Check if record is active"""
        return self.is_del == 0

    def soft_delete(self, user_id=None):
        """Soft delete the record"""
        self.is_del = 1
        if user_id:
            self.user_id_updated_by = user_id
        self.save(update_fields=['is_del', 'user_id_updated_by', 'updated_at'])

    def restore(self, user_id=None):
        """Restore soft deleted record"""
        self.is_del = 0
        if user_id:
            self.user_id_updated_by = user_id
        self.save(update_fields=['is_del', 'user_id_updated_by', 'updated_at'])