from .BaseModel import BaseModel
from django.db import models
from .CompanyOnboardingApplicationModel import CompanyOnboardingApplication
from apps.authentication.issureauth.models import User
from django.db import Q
import uuid

class ActiveCompanyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(del_flag=0)
    

class CompanyInformation(BaseModel):
    
    """
    Stores company legal information (KYC).
    """

    COMPANY_TYPE_CHOICES = [
        ('PUBLIC_LTD', 'Public Ltd Company'),
        ('PRIVATE_LTD', 'Private Limited'),
        ('LLP', 'LLP'),
        ('PARTNERSHIP', 'Partnership Firm'),
        ('SOLE_PROP', 'Sole Proprietorship'),
        ('OPC', 'OPC'),
        ('TRUST_NGO', 'Trust/Society/NGO'),
    ]
    company_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    # company_id = models.BigAutoField(primary_key=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # ENCRYPT WHEN READY
    corporate_identification_number = models.CharField(max_length=21)
    company_name = models.CharField(max_length=255)
    date_of_incorporation = models.DateField()
    place_of_incorporation = models.CharField(max_length=100)
    state_of_incorporation = models.CharField(max_length=100)

    entity_type = models.CharField(max_length=50, choices=COMPANY_TYPE_CHOICES)

    # Sensitive fields
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

    objects = models.Manager()  # Default
    active = ActiveCompanyManager()

    class Meta:
        db_table = "company_kyc"
        managed = False
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
            models.UniqueConstraint(
                fields=['gstin'],
                condition=Q(del_flag=0),
                name='unique_gstin_active_only'
            ),
        ]

    def __str__(self):
         return f"{self.company_name} (CIN: {self.corporate_identification_number})"
