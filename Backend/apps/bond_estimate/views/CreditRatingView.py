from rest_framework.views import APIView
from ..serializers.CreditRatingSerializer import CreditRatingSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated



class CreditRatingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, company_id):
        serializer = CreditRatingSerializer(
            data=request.data,
            context={"request": request, "company_id": company_id},
        )

        if serializer.is_valid():
            data = serializer.save()
            return Response(
                {"status": "success", "message": data["message"], "data": data},
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
