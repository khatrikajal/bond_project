from .BaseModel import BaseModel
from django.db import models
from django.db.models import Q
from apps.authentication.issureauth.models import User
import uuid
# from .managers.ActiveCompanyManager import ActiveCompanyManager # type: ignore


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
    Stores company legal information (KYC).
    """

    # ------------ NEW FIELDS FOR FLOWCHART LOGIC ------------
    HUMAN_INTERVENTION_CHOICES = [
        (True, "Requires Human Review"),
        (False, "Auto Verified"),
    ]

    VERIFICATION_STATUS_CHOICES = [
        ("PENDING", "Pending - Human intervention required"),
        ("SUCCESS", "Successfully Verified"),
        ("FAILED", "Failed Verification"),
    ]

    human_intervention = models.BooleanField(
        default=False,
        help_text="Flag to indicate manual review requirement."
    )

    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default="PENDING",
        help_text="Current verification state of the company KYC."
    )
    # ---------------------------------------------------------

    company_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    corporate_identification_number = models.CharField(max_length=21)
    company_name = models.CharField(max_length=255)
    date_of_incorporation = models.DateField()

    city_of_incorporation = models.CharField(max_length=100, null=True, blank=True)
    state_of_incorporation = models.CharField(max_length=100, null=True, blank=True)
    country_of_incorporation = models.CharField(max_length=100, null=True, blank=True)

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
        null=True,
        blank=True
    )

    company_or_individual_pan_card_file = models.FileField(
        upload_to='company_documents/pan_cards/',
        null=True,
        blank=True
    )

    company_pan_number = models.CharField(max_length=10)
    pan_holder_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()

    gstin = models.CharField(max_length=15)
    msme_udyam_registration_no = models.CharField(max_length=50, null=True, blank=True)

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
