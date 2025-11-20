from .BaseModel import BaseModel
from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()
import uuid


class ActiveCompanyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(del_flag=0)


class SectorChoices(models.TextChoices):
    BANKING = 'BANKING', 'banking'
    INFRASTRUCTURE = 'INFRASTRUCTURE', 'Infrastructure'
    POWER = 'POWER', 'Power'
    REAL_ESTATE = 'REAL ESTATE', 'Real Estate'
    MANUFACTURING = 'MANUFACTURING', 'Manufacturing'
    IT = 'IT', 'IT & Software'
    PUBLIC_SECTOR_UNDERTAKING = 'PUBLIC SECTOR UNDERTAKING', 'Public Sector Undertaking'
    OTHERS = 'OTHERS', 'Others'


class CompanyInformation(BaseModel):
    """
    Company KYC Table
    ALL fields REQUIRED (no null/no blank)
    """

    # Flowchart logic fields
    human_intervention = models.BooleanField(
        help_text="Manual review required?"
    )

    verification_status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending Verification"),
            ("SUCCESS", "Verified Successfully"),
            ("FAILED", "Failed Verification"),
        ],
        default="PENDING",
    )

    # Primary Key
    company_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    # user REQUIRED now
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    # REQUIRED FIELDS
    corporate_identification_number = models.CharField(max_length=21)
    company_name = models.CharField(max_length=255)
    gstin = models.CharField(max_length=15)
    date_of_incorporation = models.DateField()

    city_of_incorporation = models.CharField(max_length=100)
    state_of_incorporation = models.CharField(max_length=100)
    country_of_incorporation = models.CharField(max_length=100)

    COMPANY_TYPE_CHOICES = [
        ('PUBLIC_LTD', 'Public Ltd Company'),
        ('PRIVATE_LTD', 'Private Limited'),
        ('LLP', 'LLP'),
        ('PARTNERSHIP', 'Partnership Firm'),
        ('SOLE_PROP', 'Sole Proprietorship'),
        ('OPC', 'OPC'),
        ('TRUST_NGO', 'Trust/Society/NGO'),
    ]

    entity_type = models.CharField(max_length=50, choices=COMPANY_TYPE_CHOICES)

    sector = models.CharField(
        max_length=50,
        choices=SectorChoices.choices,
    )

    company_or_individual_pan_card_file = models.FileField(
        upload_to='company_documents/pan_cards/',
    )

    company_pan_number = models.CharField(max_length=10)
    pan_holder_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()

    msme_udyam_registration_no = models.CharField(max_length=50)

    objects = models.Manager()
    active = ActiveCompanyManager()

    class Meta:
        db_table = "company_kyc"
        indexes = [
            models.Index(fields=["user", "del_flag"]),
            models.Index(fields=["company_pan_number"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['corporate_identification_number'],
                condition=Q(del_flag=0),
                name='unique_cin_active_only'
            ),
            models.UniqueConstraint(
                fields=['company_pan_number'],
                condition=Q(del_flag=0),
                name='unique_pan_active_only'
            ),
        ]

    def __str__(self):
        return f"{self.company_name} (CIN: {self.corporate_identification_number})"
