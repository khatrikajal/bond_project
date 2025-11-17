from rest_framework.response import Response
from rest_framework import status
from apps.kyc.issuer_kyc.models import CompanyInformation

def get_company_from_token(request):
    """
    Fetch company based on authenticated user.
    No company_id is stored in JWT.
    """

    user = request.user

    if not user or not user.is_authenticated:
        return None, Response(
            {
                "success": False,
                "message": "Authentication required."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Get active companies for this user
    companies = CompanyInformation.active.filter(user=user)

    # No company found → user has not completed onboarding
    if not companies.exists():
        return None, Response(
            {
                "success": False,
                "message": "No active company found for this user. Complete onboarding first."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # If multiple companies assigned → ask to choose (optional logic)
    if companies.count() > 1:
        return None, Response(
            {
                "success": False,
                "message": "Multiple companies found. Please specify which company you want to access."
            },
            status=status.HTTP_409_CONFLICT
        )

    # Exactly one company → SUCCESS
    return companies.first(), None
