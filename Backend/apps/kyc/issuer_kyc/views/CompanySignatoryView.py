from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from ..serializers.CompanySignatorySerializer import CompanySignatoryCreateSerializer,CompanySignatoryListSerializer,CompanySignatoryUpdateSerializer,CompanySignatoryStatusUpdateSerializer
from rest_framework.response import Response
from ..models.CompanyInformationModel import CompanyInformation
from ..models.CompanySignatoryModel import CompanySignatory
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
class CompanySignatoryCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request,company_id):
        serializer = CompanySignatoryCreateSerializer(
            data=request.data,
            context={"request": request, "company_id": company_id}
        )

        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response({
            "status":"success",
            "message":data["message"],
            "data":{
               "signatory_id":data['signatory_id'],
               "company_id":data['company_id'],
               "name_of_signatory":data['name_of_signatory'],
               "designation":data['designation'],
               "din":data['din'],
               "pan_number":data['pan_number'],
               "aadhaar_number":data['aadhaar_number'],
               "email_address":data['email_address'],
            }
        },status=status.HTTP_200_OK)
    
class CompanySignatoryPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CompanySignatoryListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        try:
            company = CompanyInformation.objects.get(company_id=company_id, user=request.user)
        except CompanyInformation.DoesNotExist:
            return Response(
                {"status": "error", "message": "Company not found or not accessible."},
                status=status.HTTP_404_NOT_FOUND,
            )

        signatories = CompanySignatory.objects.filter(company=company).order_by("-created_at")

        if not signatories.exists():
            return Response(
                {
                    "status": "success",
                    "message": "No signatories found for this company.",
                    "company_id": str(company.company_id),
                    "company_name": company.company_name,
                    "total_signatories": 0,
                    "data": [],
                },
                status=status.HTTP_200_OK,
            )

        paginator = CompanySignatoryPagination()
        paginated_signatories = paginator.paginate_queryset(signatories, request)
        serializer = CompanySignatoryListSerializer(paginated_signatories, many=True)

        response_data = {
            "status": "success",
            "company_id": str(company.company_id),
            "company_name": company.company_name,
            "total_signatories": signatories.count(),
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "count": paginator.page.paginator.count,
            "data": serializer.data,  
        }

        return Response(response_data, status=status.HTTP_200_OK)

class CompanySignatoryDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, signatory_id):
        try:
            # ✅ Fetch the signatory directly and ensure it belongs to a company owned by this user
            signatory = CompanySignatory.objects.select_related("company").get(
                signatory_id=signatory_id,
                company__user=request.user
            )
        except CompanySignatory.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "message": "Signatory not found or not accessible."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CompanySignatoryListSerializer(signatory)

        return Response(
            {
                "status": "success",
                "company_id": str(signatory.company.company_id),
                "company_name": signatory.company.company_name,
                "signatory_id": str(signatory.signatory_id),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK
        )


class CompanySignatoryUpdateView(APIView):
    authentication_classes =[JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self,request,signatory_id):
        try:
            signatory = CompanySignatory.objects.select_related("company").get(
                signatory_id=signatory_id,
                company__user=request.user
            )
        except CompanySignatory.DoesNotExist:
            return Response({
                "status":"error",
                "message":"Signatory not found or not accessible."
            },status=status.HTTP_404_NOT_FOUND)
        
        serializer = CompanySignatoryUpdateSerializer(instance=signatory,
            data=request.data,
            partial=True,
            context={"request": request})
        
        if serializer.is_valid():
            data = serializer.save()

            return Response({
                    "status": "success",
                    "message": data["message"],
                    "data": {
                        "signatory_id": data["signatory_id"],
                        "name_of_signatory": data["name_of_signatory"],
                        "designation": data["designation"],
                        "din": data["din"],
                        "pan_number": data["pan_number"],
                        "aadhaar_number": data["aadhaar_number"],
                        "email_address": data["email_address"],
                        "status": data["status"],
                        "verified": data["verified"],
                    },
                },
                status=status.HTTP_200_OK,)
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    
class CompanySignatoryDelete(APIView):
    authentication_classes =[JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self,request,signatory_id):
        try:
            signatory_account = CompanySignatory.objects.get(signatory_id=signatory_id,company__user=request.user,del_flag=0)

        except CompanySignatory.DoesNotExist:
            return Response({
                "status":"error",
                "message":"Signatory not found or not accessible."
            },status=status.HTTP_404_NOT_FOUND)
        
        signatory_account.del_flag = 1
        signatory_account.user_id_updated_by = request.user
        signatory_account.save(update_fields=["del_flag", "user_id_updated_by", "updated_at"])
        
        # signatory_account.delete()

        return Response({
            "status": "success",
             "message":"Signatory account details deleted successfully."

        },status=status.HTTP_200_OK)
    

class CompanySignatoryStatusUpdate(APIView):
    authentication_classes =[JWTAuthentication]
    permission_classes =[IsAuthenticated]

    def patch(self,request,signatory_id):
        try:
            signatory = CompanySignatory.objects.select_related("company").get(
                signatory_id=signatory_id,
                company__user=request.user
            )
        except CompanySignatory.DoesNotExist:
            return Response(
                {"status": "error", "message": "Signatory not found or not accessible."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = CompanySignatoryStatusUpdateSerializer(instance = signatory,data=request.data,context={"request": request},
            partial=True)
        
        if serializer.is_valid():
            data = serializer.save()
            return Response(
                {
                    "status": "success",
                    "message": f"Signatory status updated to '{data.status}'.",
                    "data": {
                        "signatory_id": str(data.signatory_id),
                        "status": data.status,
                    },
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


        
    