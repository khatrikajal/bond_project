from apps.bond_estimate.models import BaseModel
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from apps.authentication.issureauth.models import User
from django.db import models
from ..models.AgencyRatingChoice import RatingAgency,CreditRating

class CreditRatingDetails(BaseModel):
    """
    Stores credit rating details for a company.
    Each company can have one or multiple credit ratings issued by different agencies.
    """

    credit_rating_id = models.BigAutoField(primary_key=True)

    company = models.ForeignKey(
        CompanyInformation,
        on_delete=models.CASCADE,
        related_name='credit_ratings',
        help_text="Linked company for which the rating is issued."
    )

    # Integrated with your TextChoices
    agency = models.CharField(
        max_length=50,
        choices=RatingAgency.choices,
        help_text="Credit rating agency (e.g., CRISIL, ICRA, CARE, etc.)."
    )

    rating = models.CharField(
        max_length=10,
        choices=CreditRating.choices,
        help_text="Rating value (e.g., AA (Stable), BBB+, etc.)."
    )

    valid_till = models.DateField(
        help_text="Expiration date of this credit rating."
    )

    additional_rating = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Optional remarks or additional rating comments."
    )

    upload_letter = models.FileField(
        upload_to='credit_ratings/letters/',
        null=True,
        blank=True,
        help_text="Encrypted uploaded PDF of the official credit rating letter."
    )

    reting_status = models.BooleanField(
        default=False,
        help_text="True if the rating is active/valid; False if expired or invalid."
    )

    is_del = models.SmallIntegerField(
        default=0,
        help_text="Logical delete flag — 0 = active, 1 = deleted."
    )

    user_id_updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_rating_updates',
        help_text="User/admin who last updated this record."
    )

    class Meta:
        db_table = "credit_rating_details"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['agency']),
            models.Index(fields=['rating']),
            models.Index(fields=['valid_till']),
            models.Index(fields=['reting_status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'agency', 'rating'],
                name='unique_company_agency_rating'
            )
        ]

    def __str__(self):
        return f"{self.company.company_name} - {self.agency} ({self.rating})"

