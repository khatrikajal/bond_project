from django.db import models
from apps.kyc.issuer_kyc.models.BaseModel import BaseModel
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from apps.bond_estimate.utils.financial_documents.financial_document_path import financial_document_upload_path

class DocumentType(models.TextChoices):
    GSTR_3B = 'GSTR_3B', 'GSTR-3B'
    GSTR_9 = 'GSTR_9', 'GSTR-9'
    ITR = 'ITR', 'Income Tax Return'
    FINANCIAL_STATEMENT = 'FINANCIAL_STATEMENT', 'Audited Financial Statement'


class DocumentTag(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PROVISIONAL = 'PROVISIONAL', 'Provisional'
    AUDITED = 'AUDITED', 'Audited'


class PeriodType(models.TextChoices):
    MONTHLY = 'MONTHLY', 'Monthly'
    QUARTERLY = 'QUARTERLY', 'Quarterly'
    YEARLY = 'YEARLY', 'Yearly'


class VerificationSource(models.TextChoices):
    PENDING = 'PENDING', 'Pending Verification'
    GST_PORTAL = 'GST_PORTAL', 'GST Portal API'
    INCOME_TAX_API = 'INCOME_TAX_API', 'Income Tax API'
    THIRD_PARTY_API = 'THIRD_PARTY_API', 'Third Party Verification'
    MANUAL = 'MANUAL', 'Manual Verification'

    
class FinancialDocument(BaseModel):
    document_id = models.BigAutoField(primary_key=True)

    company = models.ForeignKey(
        CompanyInformation,
        on_delete=models.PROTECT,
        related_name='financial_documents'
    )

    document_type = models.CharField(max_length=50, choices=DocumentType.choices)
    document_tag = models.CharField(max_length=20, choices=DocumentTag.choices)

    financial_year = models.CharField(max_length=9)
    period_type = models.CharField(max_length=20, choices=PeriodType.choices)
    period_start_date = models.DateField()
    period_end_date = models.DateField()

    period_code = models.CharField(max_length=20, null=True, blank=True)

    version = models.SmallIntegerField(default=1)

    file_name = models.CharField(max_length=255)
    file_path = models.FileField(
        upload_to=financial_document_upload_path,
        null=True,
        blank=True,
        max_length=500
    )

    file_size = models.BigIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, default='application/pdf')
    file_hash = models.CharField(max_length=64, null=True, blank=True, db_index=True)


    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_source = models.CharField(max_length=100, choices=VerificationSource.choices, default=VerificationSource.PENDING)
    verification_reference_id = models.CharField(max_length=255, null=True, blank=True)

    auditor_name = models.CharField(max_length=255, null=True, blank=True)
    audit_report_date = models.DateField(null=True, blank=True)
    audit_firm_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'financial_documents'
        unique_together = [
            ('company', 'document_type', 'period_start_date', 'period_end_date', 'document_tag', 'version')
        ]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'document_type']),
            models.Index(fields=['financial_year', 'document_tag']),
            models.Index(fields=['period_start_date', 'period_end_date']),
            models.Index(fields=['is_verified', 'verification_source']),
        ]
