from rest_framework.exceptions import PermissionDenied
from apps.utils.get_company_from_token import get_company_from_token
from rest_framework.views import APIView

class CompanyScopedMixin(object):
    """
    Mixin that does NOT use DRF metaclass.
    """

    def initial(self, request, *args, **kwargs):
        # DO NOT CALL super().initial()

        self.company, error = get_company_from_token(request)

        if error:
            raise PermissionDenied(detail=error.get("message", "Unauthorized access"))

        # Let DRF continue
        return super(APIView, self).initial(request, *args, **kwargs)
