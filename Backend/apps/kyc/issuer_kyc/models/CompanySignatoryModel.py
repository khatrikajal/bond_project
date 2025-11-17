from django.db import models
from apps.kyc.issuer_kyc.models.BaseModel import BaseModel
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from apps.authentication.issureauth.models import User

class ActiveSignatoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(del_flag=0)
class CompanySignatory(BaseModel):
    """
    Stores signatory details (Director / Signatory / Manager) for each company.
    A single company can have multiple signatories.
    """

    # DESIGNATION_CHOICES = [
    #     ('Director', 'Director'),
    #     ('Signatory', 'Signatory'),
    #     ('Manager', 'Manager'),
    # ]

    # STATUS_CHOICES = [
    #     ('Pending', 'Pending'),
    #     ('Active', 'Active'),
    #     ('Inactive','Inactive')
    # ]
    DESIGNATION_CHOICES = [
        ('DIRECTOR', 'Director'),
        ('SIGNATORY', 'Signatory'),
        ('MANAGER', 'Manager'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    ]


    signatory_id = models.BigAutoField(primary_key=True)

    company = models.ForeignKey(
        CompanyInformation,
        on_delete=models.CASCADE,
        related_name='signatories'
    )

    name_of_signatory = models.CharField(max_length=255)
    designation = models.CharField(max_length=50, choices=DESIGNATION_CHOICES)
    din = models.CharField(max_length=8)
    pan_number = models.CharField(max_length=10)
    aadhaar_number = models.CharField(max_length=12)
    email_address = models.EmailField(max_length=255)

    dsc_upload = models.FileField(
        upload_to='signatory_documents/dsc/',
        null=True,
        blank=True
    )

    document_file_pan = models.FileField(
        upload_to='signatory_documents/pan_cards/',
        null=False,
        blank=False
    )

    document_file_aadhaar = models.FileField(
        upload_to='signatory_documents/aadhaar_cards/',
        null=False,
        blank=False
    )

    # ✅ New fields
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text="Current status of the signatory (Active/Pending)."
    )

    verified = models.BooleanField(
        default=False,
        help_text="Indicates whether the signatory has been verified."
    )

    user_id_updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='signatory_updates'
    )

    objects = models.Manager()  # Default
    active = ActiveSignatoryManager()

    class Meta:
        db_table = "company_signatory"
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["din"]),
            models.Index(fields=["pan_number"]),
            models.Index(fields=["aadhaar_number"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "din"],
                name="unique_din_per_company"
            )
        ]

    def __str__(self):
        return f"{self.name_of_signatory} ({self.designation}) - {self.company.company_name}"
