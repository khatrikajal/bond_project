from rest_framework.response import Response
from rest_framework import status
from apps.kyc.issuer_kyc.models import CompanyInformation
from rest_framework.exceptions import PermissionDenied


# def get_company_from_token(request):

#     user = request.user

#     if not user or not user.is_authenticated:
#         return None, {
#             "message": "Authentication required.",
#             "status": status.HTTP_401_UNAUTHORIZED
#         }

#     companies = CompanyInformation.active.filter(user=user)

#     if not companies.exists():
#         return None, {
#             "message": "No active company found for this user. Complete onboarding first.",
#             "status": status.HTTP_404_NOT_FOUND
#         }

#     if companies.count() > 1:
#         return None, {
#             "message": "Multiple companies found. Please specify which company you want to access.",
#             "status": status.HTTP_409_CONFLICT
#         }

#     return companies.first(), None

def get_company_from_token(request):
    user = request.user

    if not user or not user.is_authenticated:
        raise PermissionDenied("Authentication required.")

    companies = CompanyInformation.active.filter(user=user)

    if not companies.exists():
        raise PermissionDenied("No active company found for this user.")

    if companies.count() > 1:
        raise PermissionDenied("Multiple companies found. Cannot auto-select.")

    return companies.first()
