from .BaseModel import BaseModel
from django.db import models
from .CompanyOnboardingApplicationModel import CompanyOnboardingApplication
from apps.authentication.issureauth.model import User

class CompanyOnboardingTransition(BaseModel):
    """
    Stores each onboarding action, step movement, or update.
    """

    transition_id = models.BigAutoField(primary_key=True)

    application = models.ForeignKey(
        CompanyOnboardingApplication,
        on_delete=models.CASCADE,
        related_name="transitions"
    )

    from_step = models.IntegerField()
    to_step = models.IntegerField()
    action = models.CharField(max_length=60)

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    changed_data = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "company_onboarding_transitions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["application", "created_at"]),
        ]

    def __str__(self):
        return f"{self.action} - App {self.application.application_id}"

