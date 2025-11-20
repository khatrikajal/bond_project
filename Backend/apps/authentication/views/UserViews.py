

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication



class GetUserFromTokenView(APIView):
    """
    Returns only safe, non-confidential user info from the JWT token.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # obtained via JWT authentication

        data = {
            "user_id": user.id,
            "email": user.email,
            "mobile_number": user.mobile_number,
            "kyc_status": user.kyc_status,
        }

        return APIResponse.success(
            message="User info retrieved successfully",
            data=data,
            status_code=status.HTTP_200_OK
        )