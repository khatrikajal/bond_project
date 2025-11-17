from rest_framework.exceptions import PermissionDenied
from apps.utils.get_company_from_token import get_company_from_token

class CompanyScopedMixin:
    """
    Universal mixin for:
    - APIView
    - GenericAPIView
    - ViewSet
    """

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        # Fetch company for user
        self.company, error = get_company_from_token(request)

        if error:
            raise PermissionDenied(detail=error.data.get("message", "Unauthorized access"))

        # No need to check company_id from URL anymore
