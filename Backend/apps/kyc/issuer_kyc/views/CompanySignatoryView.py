from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from ..models import CompanyInformation, CompanySignatory
from ..serializers.CompanySignatorySerializer import CompanySignatoryCreateSerializer,CompanySignatoryListSerializer,CompanySignatoryUpdateSerializer,CompanySignatoryStatusUpdateSerializer
from config.common.response import APIResponse
from rest_framework.permissions import IsAuthenticated
from apps.utils.get_company_from_token import get_company_from_token
from rest_framework.pagination import PageNumberPagination



# class CompanySignatoryCreateView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def post(self,request,company_id):
#         serializer = CompanySignatoryCreateSerializer(
#             data=request.data,
#             context={"request": request, "company_id": company_id}
#         )

#         serializer.is_valid(raise_exception=True)
#         data = serializer.save()
#         return Response({
#             "status":"success",
#             "message":data["message"],
#             "data":{
#                "signatory_id":data['signatory_id'],
#                "company_id":data['company_id'],
#                "name_of_signatory":data['name_of_signatory'],
#                "designation":data['designation'],
#                "din":data['din'],
#                "pan_number":data['pan_number'],
#                "aadhaar_number":data['aadhaar_number'],
#                "email_address":data['email_address'],
#             }
#         },status=status.HTTP_200_OK)
    
# class CompanySignatoryPagination(PageNumberPagination):
#     page_size = 10
#     page_size_query_param = 'page_size'
#     max_page_size = 100


# class CompanySignatoryListView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def get(self, request, company_id):
#         try:
#             company = CompanyInformation.objects.get(company_id=company_id, user=request.user)
#         except CompanyInformation.DoesNotExist:
#             return Response(
#                 {"status": "error", "message": "Company not found or not accessible."},
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         signatories = CompanySignatory.objects.filter(company=company).order_by("-created_at")

#         if not signatories.exists():
#             return Response(
#                 {
#                     "status": "success",
#                     "message": "No signatories found for this company.",
#                     "company_id": str(company.company_id),
#                     "company_name": company.company_name,
#                     "total_signatories": 0,
#                     "data": [],
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         paginator = CompanySignatoryPagination()
#         paginated_signatories = paginator.paginate_queryset(signatories, request)
#         serializer = CompanySignatoryListSerializer(paginated_signatories, many=True)

#         response_data = {
#             "status": "success",
#             "company_id": str(company.company_id),
#             "company_name": company.company_name,
#             "total_signatories": signatories.count(),
#             "next": paginator.get_next_link(),
#             "previous": paginator.get_previous_link(),
#             "count": paginator.page.paginator.count,
#             "data": serializer.data,  
#         }

#         return Response(response_data, status=status.HTTP_200_OK)




# class CompanySignatoryDetailView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def get(self, request, signatory_id):
#         try:
#             # ✅ Fetch the signatory directly and ensure it belongs to a company owned by this user
#             signatory = CompanySignatory.objects.select_related("company").get(
#                 signatory_id=signatory_id,
#                 company__user=request.user
#             )
#         except CompanySignatory.DoesNotExist:
#             return Response(
#                 {
#                     "status": "error",
#                     "message": "Signatory not found or not accessible."
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = CompanySignatoryListSerializer(signatory)

#         return Response(
#             {
#                 "status": "success",
#                 "company_id": str(signatory.company.company_id),
#                 "company_name": signatory.company.company_name,
#                 "signatory_id": str(signatory.signatory_id),
#                 "data": serializer.data,
#             },
#             status=status.HTTP_200_OK
#         )

# # class CompanySignatoryDetailView(APIView):
# #     authentication_classes = [JWTAuthentication]
# #     permission_classes = [IsAuthenticated]

# #     def get(self, request, signatory_id):
# #         try:
# #             # Ensure company belongs to this user
# #             company = CompanyInformation.objects.get(user=request.user)
# #         except CompanyInformation.DoesNotExist:
# #             return Response(
# #                 {
# #                     "status": "error",
# #                     "message": "Company not found or not accessible."
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND
# #             )

# #         try:
# #             # Get specific signatory of this company
# #             signatory = CompanySignatory.objects.get(company=company, signatory_id=signatory_id)
# #         except CompanySignatory.DoesNotExist:
# #             return Response(
# #                 {
# #                     "status": "error",
# #                     "message": "Signatory not found for this company."
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND
# #             )

# #         serializer = CompanySignatoryListSerializer(signatory)

# #         return Response(
# #             {
# #                 "status": "success",
# #                 "company_id": str(company.company_id),
# #                 "company_name": company.company_name,
# #                 "signatory_id": str(signatory.signatory_id),
# #                 "data": serializer.data,
# #             },
# #             status=status.HTTP_200_OK
# #         )


# class CompanySignatoryUpdateView(APIView):
#     authentication_classes =[JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def patch(self,request,signatory_id):
#         try:
#             signatory = CompanySignatory.objects.select_related("company").get(
#                 signatory_id=signatory_id,
#                 company__user=request.user
#             )
#         except CompanySignatory.DoesNotExist:
#             return Response({
#                 "status":"error",
#                 "message":"Signatory not found or not accessible."
#             },status=status.HTTP_404_NOT_FOUND)
        
#         serializer = CompanySignatoryUpdateSerializer(instance=signatory,
#             data=request.data,
#             partial=True,
#             context={"request": request})
        
#         if serializer.is_valid():
#             data = serializer.save()

#             return Response({
#                     "status": "success",
#                     "message": data["message"],
#                     "data": {
#                         "signatory_id": data["signatory_id"],
#                         "name_of_signatory": data["name_of_signatory"],
#                         "designation": data["designation"],
#                         "din": data["din"],
#                         "pan_number": data["pan_number"],
#                         "aadhaar_number": data["aadhaar_number"],
#                         "email_address": data["email_address"],
#                         "status": data["status"],
#                         "verified": data["verified"],
#                     },
#                 },
#                 status=status.HTTP_200_OK,)
#         return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    
# class CompanySignatoryDelete(APIView):
#     authentication_classes =[JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def delete(self,request,signatory_id):
#         try:
#             signatory_account = CompanySignatory.objects.get(signatory_id=signatory_id,company__user=request.user,del_flag=0)

#         except CompanySignatory.DoesNotExist:
#             return Response({
#                 "status":"error",
#                 "message":"Signatory not found or not accessible."
#             },status=status.HTTP_404_NOT_FOUND)
        
#         signatory_account.del_flag = 1
#         signatory_account.user_id_updated_by = request.user
#         signatory_account.save(update_fields=["del_flag", "user_id_updated_by", "updated_at"])
        
#         # signatory_account.delete()

#         return Response({
#             "status": "success",
#              "message":"Signatory account details deleted successfully."

#         },status=status.HTTP_200_OK)
    

# class CompanySignatoryStatusUpdate(APIView):
#     authentication_classes =[JWTAuthentication]
#     permission_classes =[IsAuthenticated]

#     def patch(self,request,signatory_id):
#         try:
#             signatory = CompanySignatory.objects.select_related("company").get(
#                 signatory_id=signatory_id,
#                 company__user=request.user
#             )
#         except CompanySignatory.DoesNotExist:
#             return Response(
#                 {"status": "error", "message": "Signatory not found or not accessible."},
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         serializer = CompanySignatoryStatusUpdateSerializer(instance = signatory,data=request.data,context={"request": request},
#             partial=True)
        
#         if serializer.is_valid():
#             data = serializer.save()
#             return Response(
#                 {
#                     "status": "success",
#                     "message": f"Signatory status updated to '{data.status}'.",
#                     "data": {
#                         "signatory_id": str(data.signatory_id),
#                         "status": data.status,
#                     },
#                 },
#                 status=status.HTTP_200_OK,
#             )
#         return Response(
#             {"status": "error", "errors": serializer.errors},
#             status=status.HTTP_400_BAD_REQUEST
#         )




#------------------- Lasted Verison 18-11-2025 -------------


# class CompanySignatoryCreateView(APIView):
  
#     permission_classes = [IsAuthenticated]

#     def post(self, request, company_id):
#         serializer = CompanySignatoryCreateSerializer(
#             data=request.data,
#             context={"request": request, "company_id": company_id}
#         )

#         serializer.is_valid(raise_exception=True)
#         data = serializer.save()

#         return APIResponse.success(
#             message=data["message"],
#             data={
#                 "signatory_id": data['signatory_id'],
#                 "company_id": data['company_id'],
#                 "name_of_signatory": data['name_of_signatory'],
#                 "designation": data['designation'],
#                 "din": data['din'],
#                 "pan_number": data['pan_number'],
#                 "aadhaar_number": data['aadhaar_number'],
#                 "email_address": data['email_address'],
#             }
#         )


# class CompanySignatoryPagination(PageNumberPagination):
#     page_size = 10
#     page_size_query_param = 'page_size'
#     max_page_size = 100


# class CompanySignatoryListView(APIView):
  
#     permission_classes = [IsAuthenticated]

#     def get(self, request, company_id):
#         try:
#             company = CompanyInformation.objects.get(
#                 company_id=company_id,
#                 user=request.user
#             )
#         except CompanyInformation.DoesNotExist:
#             return APIResponse.error(
#                 message="Company not found or not accessible.",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         signatories = CompanySignatory.objects.filter(
#             company=company
#         ).order_by("-created_at")

#         if not signatories.exists():
#             return APIResponse.success(
#                 message="No signatories found for this company.",
#                 data={
#                     "company_id": str(company.company_id),
#                     "company_name": company.company_name,
#                     "total_signatories": 0,
#                     "data": []
#                 }
#             )

        # paginator = CompanySignatoryPagination()
#         paginated_signatories = paginator.paginate_queryset(signatories, request)
#         serializer = CompanySignatoryListSerializer(paginated_signatories, many=True)

#         response_data = {
#             "company_id": str(company.company_id),
#             "company_name": company.company_name,
#             "total_signatories": signatories.count(),
#             "next": paginator.get_next_link(),
#             "previous": paginator.get_previous_link(),
#             "count": paginator.page.paginator.count,
#             "data": serializer.data,
#         }

#         return APIResponse.success(data=response_data)


# class CompanySignatoryDetailView(APIView):
  
#     permission_classes = [IsAuthenticated]

#     def get(self, request, signatory_id):
#         try:
#             signatory = CompanySignatory.objects.select_related("company").get(
#                 signatory_id=signatory_id,
#                 company__user=request.user
#             )
#         except CompanySignatory.DoesNotExist:
#             return APIResponse.error(
#                 message="Signatory not found or not accessible.",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         serializer = CompanySignatoryListSerializer(signatory)

#         return APIResponse.success(
#             data={
#                 "company_id": str(signatory.company.company_id),
#                 "company_name": signatory.company.company_name,
#                 "signatory_id": str(signatory.signatory_id),
#                 "data": serializer.data,
#             }
#         )


# class CompanySignatoryUpdateView(APIView):
  
#     permission_classes = [IsAuthenticated]

#     def patch(self, request, signatory_id):
#         try:
#             signatory = CompanySignatory.objects.select_related("company").get(
#                 signatory_id=signatory_id,
#                 company__user=request.user
#             )
#         except CompanySignatory.DoesNotExist:
#             return APIResponse.error(
#                 message="Signatory not found or not accessible.",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         serializer = CompanySignatoryUpdateSerializer(
#             instance=signatory,
#             data=request.data,
#             partial=True,
#             context={"request": request}
#         )

#         if serializer.is_valid():
#             data = serializer.save()

#             return APIResponse.success(
#                 message=data["message"],
#                 data={
#                     "signatory_id": data["signatory_id"],
#                     "name_of_signatory": data["name_of_signatory"],
#                     "designation": data["designation"],
#                     "din": data["din"],
#                     "pan_number": data["pan_number"],
#                     "aadhaar_number": data["aadhaar_number"],
#                     "email_address": data["email_address"],
#                     "status": data["status"],
#                     "verified": data["verified"],
#                 }
#             )

#         return APIResponse.error(
#             message="Validation failed",
#             errors=serializer.errors,
#             status_code=status.HTTP_400_BAD_REQUEST
#         )


# class CompanySignatoryDelete(APIView):
  
#     permission_classes = [IsAuthenticated]

#     def delete(self, request, signatory_id):
#         try:
#             signatory_account = CompanySignatory.objects.get(
#                 signatory_id=signatory_id,
#                 company__user=request.user,
#                 del_flag=0
#             )
#         except CompanySignatory.DoesNotExist:
#             return APIResponse.error(
#                 message="Signatory not found or not accessible.",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         signatory_account.del_flag = 1
#         signatory_account.user_id_updated_by = request.user
#         signatory_account.save(update_fields=["del_flag", "user_id_updated_by", "updated_at"])

#         return APIResponse.success(
#             message="Signatory account details deleted successfully."
#         )


# class CompanySignatoryStatusUpdate(APIView):
  
#     permission_classes = [IsAuthenticated]

#     def patch(self, request, signatory_id):
#         try:
#             signatory = CompanySignatory.objects.select_related("company").get(
#                 signatory_id=signatory_id,
#                 company__user=request.user
#             )
#         except CompanySignatory.DoesNotExist:
#             return APIResponse.error(
#                 message="Signatory not found or not accessible.",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         serializer = CompanySignatoryStatusUpdateSerializer(
#             instance=signatory,
#             data=request.data,
#             partial=True,
#             context={"request": request}
#         )

#         if serializer.is_valid():
#             data = serializer.save()

#             return APIResponse.success(
#                 message=f"Signatory status updated to '{data.status}'.",
#                 data={
#                     "signatory_id": str(data.signatory_id),
#                     "status": data.status,
#                 }
#             )

#         return APIResponse.error(
#             message="Validation failed",
#             errors=serializer.errors,
#             status_code=400
#         )
     
#----------------------------------------------------


from apps.utils.get_company_from_token import get_company_from_token

class CompanySignatoryCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, company_id=None):
        # 🔥 Instead of using company_id from URL
        company = get_company_from_token(request)
        company_id = company.company_id  # keep serializer compatibility

        serializer = CompanySignatoryCreateSerializer(
            data=request.data,
            context={
                "request": request,
                "company_id": company_id      # unchanged logic
            }
        )

        serializer.is_valid(raise_exception=True)
        data = serializer.save()

        return APIResponse.success(
            message=data["message"],
            data={
                "signatory_id": data['signatory_id'],
                "company_id": data['company_id'],
                "name_of_signatory": data['name_of_signatory'],
                "designation": data['designation'],
                "din": data['din'],
                "pan_number": data['pan_number'],
                "aadhaar_number": data['aadhaar_number'],
                "email_address": data['email_address'],
            }
        )


class CompanySignatoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id=None):

        # 🔥 Replace URL company_id with token company
        company = get_company_from_token(request)

        signatories = CompanySignatory.objects.filter(
            company=company
        ).order_by("-created_at")

        if not signatories.exists():
            return APIResponse.success(
                message="No signatories found for this company.",
                data={
                    "company_id": str(company.company_id),
                    "company_name": company.company_name,
                    "total_signatories": 0,
                    "data": []
                }
            )

        paginator = PageNumberPagination()
        paginated_signatories = paginator.paginate_queryset(signatories, request)
        serializer = CompanySignatoryListSerializer(paginated_signatories, many=True)

        response_data = {
            "company_id": str(company.company_id),
            "company_name": company.company_name,
            "total_signatories": signatories.count(),
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "count": paginator.page.paginator.count,
            "data": serializer.data,
        }

        return APIResponse.success(data=response_data)


class CompanySignatoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, signatory_id):

        # 🔥 Only allow signatories of the company from token
        company = get_company_from_token(request)

        try:
            signatory = CompanySignatory.objects.select_related("company").get(
                signatory_id=signatory_id,
                company=company
            )
        except CompanySignatory.DoesNotExist:
            return APIResponse.error(
                message="Signatory not found or not accessible.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = CompanySignatoryListSerializer(signatory)

        return APIResponse.success(
            data={
                "company_id": str(signatory.company.company_id),
                "company_name": signatory.company.company_name,
                "signatory_id": str(signatory.signatory_id),
                "data": serializer.data,
            }
        )


class CompanySignatoryUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, signatory_id):

        company = get_company_from_token(request)

        try:
            signatory = CompanySignatory.objects.select_related("company").get(
                signatory_id=signatory_id,
                company=company
            )
        except CompanySignatory.DoesNotExist:
            return APIResponse.error(
                message="Signatory not found or not accessible.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = CompanySignatoryUpdateSerializer(
            instance=signatory,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            data = serializer.save()
            return APIResponse.success(
                message=data["message"],
                data={
                    "signatory_id": data["signatory_id"],
                    "name_of_signatory": data["name_of_signatory"],
                    "designation": data["designation"],
                    "din": data["din"],
                    "pan_number": data["pan_number"],
                    "aadhaar_number": data["aadhaar_number"],
                    "email_address": data["email_address"],
                    "status": data["status"],
                    "verified": data["verified"],
                }
            )

        return APIResponse.error(
            message="Validation failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class CompanySignatoryStatusUpdate(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, signatory_id):

        company = get_company_from_token(request)

        try:
            signatory = CompanySignatory.objects.select_related("company").get(
                signatory_id=signatory_id,
                company=company
            )
        except CompanySignatory.DoesNotExist:
            return APIResponse.error(
                message="Signatory not found or not accessible.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = CompanySignatoryStatusUpdateSerializer(
            instance=signatory,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            data = serializer.save()

            return APIResponse.success(
                message=f"Signatory status updated to '{data.status}'.",
                data={
                    "signatory_id": str(data.signatory_id),
                    "status": data.status,
                }
            )

        return APIResponse.error(
            message="Validation failed",
            errors=serializer.errors,
            status_code=400
        )
