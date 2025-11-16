from rest_framework.response import Response
from rest_framework import status


class CompanyPermissionMixin:
    """
    Mixin to enforce that a user can only access/modify data for their own company.
    - For modifying actions (create/update/delete/patch), returns a friendly 403 Response if unauthorized.
    - For list/retrieve (querysets), returns an empty queryset if unauthorized.
    
    Requirements:
    - The viewset must implement `_get_user_company(self, company_id)` method.
    - The viewset must accept `company_id` in URL kwargs.
    """

    def check_company_access(self, company_id, for_queryset=False):
        """
        Checks if the logged-in user has access to the company.
        Args:
            company_id: The company ID to check
            for_queryset: True if called inside get_queryset()
        Returns:
            - Company instance if allowed
            - Response (403) if for action and unauthorized
            - None if for queryset and unauthorized
        """
        company = self._get_user_company(company_id)
        if not company:
            if for_queryset:
                return None
            return Response(
                {
                    "success": False,
                    "message": "You are not allowed to access or modify data for this company. "
                               "Please check your company selection."
                },
                status=status.HTTP_403_FORBIDDEN
            )
        return company

    def ensure_company_access(self, company_id, for_queryset=False):
        """
        Shortcut to enforce company access.
        - Returns company instance if allowed
        - Returns Response (for actions) or None (for queryset) if unauthorized
        """
        return self.check_company_access(company_id, for_queryset=for_queryset)

    def filter_queryset_by_company(self, queryset, company_id):
        """
        Helper to filter queryset by company access.
        Returns an empty queryset if unauthorized.
        """
        company = self.ensure_company_access(company_id, for_queryset=True)
        if company is None:
            return queryset.none()
        return queryset.filter(company_id=company_id)
