from rest_framework.views import APIView
from ..serializers.DemateAccountSerializer import DemateAccountSerializer,DemateAccountGetSerializer,DemateAccountUpdateSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from ..models.DemateAccountDetailsModel import DematAccount 


class DematAccountCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, company_id):
        serializer = DemateAccountSerializer(
            data=request.data,
            context={
                "request": request,
                "company_id": company_id,
            },
        )

        if serializer.is_valid():
            data = serializer.save()
            return Response(
                {
                    "status": "success",
                    "message": data["message"],
                    "data": {
                        "demat_account_id": data["demat_account_id"],
                        "company_id": data["company_id"],
                        "dp_name": data["dp_name"],
                        "depository_participant": data["depository_participant"],
                        "dp_id": data["dp_id"],
                        "demat_account_number": data["demat_account_number"],
                        "client_id_bo_id": data["client_id_bo_id"],
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    


class DematAccountGetView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, demat_account_id):
        try:
            dematAccount = DematAccount.objects.get(
                demat_account_id=demat_account_id,
                company__user=request.user
            )
        except DematAccount.DoesNotExist:
            return Response(
                {"status": "error", "message": "Demat Account information not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DemateAccountGetSerializer(dematAccount)
        return Response(
            {"status": "success", "data": serializer.data},
            status=status.HTTP_200_OK,
        )
    

class DematAccountUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, demat_account_id):
        """Update demat account details (partial update)."""
        try:
            demat_account = DematAccount.objects.get(
                demat_account_id=demat_account_id,
                company__user=request.user
            )
        except DematAccount.DoesNotExist:
            return Response(
                {"status": "error", "message": "Demat account not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = DemateAccountUpdateSerializer(
            instance=demat_account,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            data = serializer.save()
            return Response(
                {
                    "status": "success",
                    "message": data["message"],
                    "data": {
                        "demat_account_id": data["demat_account_id"],
                        "dp_name": data["dp_name"],
                        "depository_participant": data["depository_participant"],
                        "dp_id": data["dp_id"],
                        "demat_account_number": data["demat_account_number"],
                        "client_id_bo_id": data["client_id_bo_id"],
                    },
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
class DematAccountDelateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self,request,demat_account_id):
        try:
            demat_account = DematAccount.objects.get(
                demat_account_id=demat_account_id,
                company__user=request.user,del_flag=0
            )
        except DematAccount.DoesNotExist:
            return Response({
                "status":"error",
                "message":"Demate account details is not found."
            },status=status.HTTP_404_NOT_FOUND)
        
        demat_account.del_flag = 1
        demat_account.user_id_updated_by = request.user.user_id
        demat_account.save(update_fields=["del_flag", "user_id_updated_by", "updated_at"])
        # demat_account.delete()

        return Response({
             "status": "success",
             "message":"Demate account details deleted successfully."


        },status=status.HTTP_200_OK)



            