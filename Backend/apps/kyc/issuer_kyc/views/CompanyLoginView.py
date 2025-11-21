import logging
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from ..serializers.CompanyLoginSerializer import CompanyLoginSerializer
from config.common.response import APIResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CompanyLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CompanyLoginSerializer(data=request.data)

        if not serializer.is_valid():
            return APIResponse.error(
                message="Invalid login credentials",
                errors=serializer.errors,
                status_code=400
            )

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        logger.info(f"[COMPANY LOGIN] Login successful for user={user.id}")

        return APIResponse.success(
            message="Login successful",
            data={
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user_id": user.id,
                "roles": list(user.roles.values_list("name", flat=True))
            }
        )