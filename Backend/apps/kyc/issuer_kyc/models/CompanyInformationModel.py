from .BaseModel import BaseModel
from django.db import models
from .CompanyOnboardingApplicationModel import CompanyOnboardingApplication
from apps.authentication.issureauth.model import User

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

    company_id = models.BigAutoField(primary_key=True)

    application = models.ForeignKey(
        CompanyOnboardingApplication,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="company_info"
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # ENCRYPT WHEN READY
    corporate_identification_number = models.CharField(max_length=21, unique=True)
    company_name = models.CharField(max_length=255)
    date_of_incorporation = models.DateField()
    place_of_incorporation = models.CharField(max_length=100)
    state_of_incorporation = models.CharField(max_length=100)

    entity_type = models.CharField(max_length=50, choices=COMPANY_TYPE_CHOICES)

    # Sensitive fields
    company_or_individual_pan_card_file = models.BinaryField()
    company_pan_number = models.CharField(max_length=10, unique=True)
    pan_holder_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()

    gstin = models.CharField(max_length=15)
    msme_udyam_registration_no = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "company_kyc"
        indexes = [
            models.Index(fields=["user", "del_flag"]),
            models.Index(fields=["company_pan_number"]),
        ]

    def __str__(self):
        return f"{self.company_name} (CIN: {self.corporate_identification_number})"
