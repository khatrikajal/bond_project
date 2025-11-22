from rest_framework.exceptions import PermissionDenied
from apps.bond_estimate.models.BondEstimationApplicationModel import BondEstimationApplication

class ApplicationScopedMixin:
    """
    Ensures the logged-in user has access to the given application_id.
    """

    def get_application(self, application_id):
        """
        Fetch application + validate ownership.
        """
        application = (
            BondEstimationApplication.objects
            .select_related("company")
            .filter(
                application_id=application_id,
                company__user=self.request.user,
                company__del_flag=0
            )
            .first()
        )

        if application is None:
            raise PermissionDenied("You do not have access to this application.")

        return application


    def initial(self, request, *args, **kwargs):
        """
        Override DRF initial() WITHOUT causing metaclass issues.
        """
        application_id = kwargs.get("application_id")

        if not application_id:
            raise PermissionDenied("Application ID missing in request.")

        # Attach to self for use inside the view
        self.application = self.get_application(application_id)

        # Continue DRF processing
        return super().initial(request, *args, **kwargs)
