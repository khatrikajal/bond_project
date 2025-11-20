from rest_framework.views import APIView
from ..serializers.DemateAccountSerializer import DemateAccountSerializer,DemateAccountGetSerializer,DemateAccountUpdateSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from ..models.DemateAccountDetailsModel import DematAccount 
from config.common.response import APIResponse
from ..models.CompanyInformationModel import CompanyInformation
from ..services.demate_details.demat_service import DematService
from apps.utils.get_company_from_token import get_company_from_token
import re

# class DematAccountCreateView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def post(self, request, company_id):
#         serializer = DemateAccountSerializer(
#             data=request.data,
#             context={
#                 "request": request,
#                 "company_id": company_id,
#             },
#         )

#         if serializer.is_valid():
#             data = serializer.save()
#             return Response(
#                 {
#                     "status": "success",
#                     "message": data["message"],
#                     "data": {
#                         "demat_account_id": data["demat_account_id"],
#                         "company_id": data["company_id"],
#                         "dp_name": data["dp_name"],
#                         "depository_participant": data["depository_participant"],
#                         "dp_id": data["dp_id"],
#                         "demat_account_number": data["demat_account_number"],
#                         "client_id_bo_id": data["client_id_bo_id"],
#                     },
#                 },
#                 status=status.HTTP_201_CREATED,
#             )

#         return Response(
#             {"status": "error", "errors": serializer.errors},
#             status=status.HTTP_400_BAD_REQUEST,
#         )
    


# class DematAccountGetView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def get(self, request, demat_account_id):
#         try:
#             dematAccount = DematAccount.objects.get(
#                 demat_account_id=demat_account_id,
#                 company__user=request.user
#             )
#         except DematAccount.DoesNotExist:
#             return Response(
#                 {"status": "error", "message": "Demat Account information not found."},
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         serializer = DemateAccountGetSerializer(dematAccount)
#         return Response(
#             {"status": "success", "data": serializer.data},
#             status=status.HTTP_200_OK,
#         )
    

# class DematAccountUpdateView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def patch(self, request, demat_account_id):
#         """Update demat account details (partial update)."""
#         try:
#             demat_account = DematAccount.objects.get(
#                 demat_account_id=demat_account_id,
#                 company__user=request.user
#             )
#         except DematAccount.DoesNotExist:
#             return Response(
#                 {"status": "error", "message": "Demat account not found."},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = DemateAccountUpdateSerializer(
#             instance=demat_account,
#             data=request.data,
#             partial=True,
#             context={"request": request}
#         )

#         if serializer.is_valid():
#             data = serializer.save()
#             return Response(
#                 {
#                     "status": "success",
#                     "message": data["message"],
#                     "data": {
#                         "demat_account_id": data["demat_account_id"],
#                         "dp_name": data["dp_name"],
#                         "depository_participant": data["depository_participant"],
#                         "dp_id": data["dp_id"],
#                         "demat_account_number": data["demat_account_number"],
#                         "client_id_bo_id": data["client_id_bo_id"],
#                     },
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         return Response(
#             {"status": "error", "errors": serializer.errors},
#             status=status.HTTP_400_BAD_REQUEST
#         )
    
# class DematAccountDelateView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def delete(self,request,demat_account_id):
#         try:
#             demat_account = DematAccount.objects.get(
#                 demat_account_id=demat_account_id,
#                 company__user=request.user,del_flag=0
#             )
#         except DematAccount.DoesNotExist:
#             return Response({
#                 "status":"error",
#                 "message":"Demate account details is not found."
#             },status=status.HTTP_404_NOT_FOUND)
        
#         demat_account.del_flag = 1
#         demat_account.user_id_updated_by = request.user.user_id
#         demat_account.save(update_fields=["del_flag", "user_id_updated_by", "updated_at"])
#         # demat_account.delete()

#         return Response({
#              "status": "success",
#              "message":"Demate account details deleted successfully."


#         },status=status.HTTP_200_OK)



PAN_REGEX = r"^[A-Z]{5}[0-9]{4}[A-Z]$"


class FetchDematDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Fetch demat details using PAN linked to the given company.
        """
        company = get_company_from_token(request)
        company_id = company.company_id

        # 1. Fetch company
        try:
            company = CompanyInformation.active.get(
                company_id=company_id,
                user=request.user
            )
        except CompanyInformation.DoesNotExist:
            return APIResponse.error(
                message="Company not found or not owned by the user",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # 2. Extract PAN
        pan_number = (company.company_pan_number or "").strip().upper()

        # 3. Validate PAN (Even though it should never be invalid)
        if not pan_number:
            return APIResponse.error(
                message="PAN number is missing for this company.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if pan_number in ["NULL", "NONE", "-", "N/A"]:
            return APIResponse.error(
                message="Invalid PAN number stored for this company.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if not re.match(PAN_REGEX, pan_number):
            return APIResponse.error(
                message="PAN number format is invalid. Expected format: AAAAA9999A",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # 4. Call service layer for demat details
        demat_data = DematService.fetch_demat_details_from_pan(pan_number)

        # 5. Success response
        return APIResponse.success(
            message="Demat details fetched successfully.",
            data={
                "company_id": company.company_id,
                "company_name": company.company_name,
                "pan_used": pan_number,
                "demat_details": demat_data
            },
            status_code=status.HTTP_200_OK
        )



class DematAccountCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        company = get_company_from_token(request)
        company_id = company.company_id
        serializer = DemateAccountSerializer(
            data=request.data,
            context={
                "request": request,
                "company_id": company_id,
            },
        )

        if serializer.is_valid():
            data = serializer.save()
            return APIResponse.success(
                message=data["message"],
                data={
                    "demat_account_id": data["demat_account_id"],
                    "company_id": data["company_id"],
                    "dp_name": data["dp_name"],
                    "depository_participant": data["depository_participant"],
                    "dp_id": data["dp_id"],
                    "demat_account_number": data["demat_account_number"],
                    "client_id_bo_id": data["client_id_bo_id"],
                },
                status_code=status.HTTP_201_CREATED
            )

        return APIResponse.error(
            message="Validation failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
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
            return APIResponse.error(
                message="Demat Account information not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = DemateAccountGetSerializer(dematAccount)
        return APIResponse.success(
            data=serializer.data,
            message="Demat account fetched successfully.",
            status_code=status.HTTP_200_OK
        )


class DematAccountUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, demat_account_id):
        try:
            demat_account = DematAccount.objects.get(
                demat_account_id=demat_account_id,
                company__user=request.user
            )
        except DematAccount.DoesNotExist:
            return APIResponse.error(
                message="Demat account not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = DemateAccountUpdateSerializer(
            instance=demat_account,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            data = serializer.save()
            return APIResponse.success(
                message=data["message"],
                data={
                    "demat_account_id": data["demat_account_id"],
                    "dp_name": data["dp_name"],
                    "depository_participant": data["depository_participant"],
                    "dp_id": data["dp_id"],
                    "demat_account_number": data["demat_account_number"],
                    "client_id_bo_id": data["client_id_bo_id"],
                },
                status_code=status.HTTP_200_OK
            )

        return APIResponse.error(
            message="Validation failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class DematAccountDelateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, demat_account_id):
        try:
            demat_account = DematAccount.objects.get(
                demat_account_id=demat_account_id,
                company__user=request.user,
                del_flag=0
            )
        except DematAccount.DoesNotExist:
            return APIResponse.error(
                message="Demat account details not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        demat_account.del_flag = 1
        demat_account.user_id_updated_by = request.user.user.id
        demat_account.save(update_fields=["del_flag", "user_id_updated_by", "updated_at"])

        return APIResponse.success(
            message="Demat account details deleted successfully.",
            data=None,
            status_code=status.HTTP_200_OK
        )
