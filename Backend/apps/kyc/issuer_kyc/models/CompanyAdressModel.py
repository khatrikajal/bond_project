from .BaseModel import BaseModel
from django.db import models
from .CompanyOnboardingApplicationModel import CompanyOnboardingApplication
from .CompanyInformationModel import CompanyInformation


class CompanyAddress(BaseModel):
    """
    Stores registered + correspondence addresses.
    """

    ADDRESS_TYPE_CHOICES = [
        (0, "REGISTERED"),
        (1, "CORRESPONDENCE"),
        (2, "BOTH")
    ]

    address_id = models.BigAutoField(primary_key=True)

    application = models.ForeignKey(
        CompanyOnboardingApplication,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="addresses"
    )

    company = models.ForeignKey(
        CompanyInformation,
        on_delete=models.CASCADE,
        related_name="addresses"
    )

    registered_office_address = models.TextField()
    city = models.CharField(max_length=100, db_index=True)
    state_ut = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=6)
    country = models.CharField(max_length=100, default="India")

    company_contact_email = models.EmailField(max_length=255)
    company_contact_phone = models.CharField(max_length=15)

    address_type = models.IntegerField(choices=ADDRESS_TYPE_CHOICES)

    class Meta:
        db_table = "company_address"
        indexes = [
            models.Index(fields=["company", "del_flag"]),
            models.Index(fields=["city", "state_ut"]),
        ]

    def __str__(self):
        return f"{self.company.company_name} - {self.get_address_type_display()}"
