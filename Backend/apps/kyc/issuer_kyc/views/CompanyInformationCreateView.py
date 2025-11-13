from rest_framework.views import APIView
from ..serializers.CompanyInfoSerializer import CompanyInfoSerializer,PanExtractionSerializer,CompanyInfoGetSerializer,CompanyInfoUpdateSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from ..models import CompanyInformation,CompanyOnboardingApplication
from ..services.company_information.company_info_service import CompanyInfoService
from config.common.response import APIResponse  
import re

class CompanyInformationCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CompanyInfoSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            data = serializer.save()
            response_data = { 
                "company_id": data["company_id"], 
                "company_name": data["company_name"], 
                "company_pan_number": data["company_pan_number"],
                "pan_holder_name": data["pan_holder_name"], 
                "date_of_birth": data["date_of_birth"],
            }
            return APIResponse.success(
                data=response_data,
                message=data["message"],
                status_code=status.HTTP_201_CREATED
            )
        
        return APIResponse.error(
            message="Validation error",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class PanExtractionView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = PanExtractionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return APIResponse.success(
            data=result,
            message="PAN details extracted successfully",
            status_code=status.HTTP_200_OK
        )


class CompanyInfoGetView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        try:
            company = CompanyInformation.objects.get(company_id=company_id, user=request.user)
        except CompanyInformation.DoesNotExist:
            return APIResponse.error(
                message="Company information not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CompanyInfoGetSerializer(company)
        return APIResponse.success(
            data=serializer.data,
            message="Company information fetched successfully",
            status_code=status.HTTP_200_OK
        )


class CompanyInformationUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, company_id):
        try:
            company = CompanyInformation.objects.get(company_id=company_id, user=request.user)
        except CompanyInformation.DoesNotExist:
            return APIResponse.error(
                message="Company information not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = CompanyInfoUpdateSerializer(
            instance=company, 
            data=request.data, 
            partial=True, 
            context={'request': request}
        )

        if serializer.is_valid():
            data = serializer.save()
            response_data = {
                "company_id": data["company_id"],
                "company_name": data["company_name"],
                "company_pan_number": data["company_pan_number"],
                "pan_holder_name": data["pan_holder_name"],
                "date_of_birth": data["date_of_birth"],
            }
            return APIResponse.success(
                data=response_data,
                message=data["message"],
                status_code=status.HTTP_200_OK
            )

        return APIResponse.error(
            message="Validation error",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class CompanyInfoDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, company_id):
        try:
            company = CompanyInformation.objects.get(company_id=company_id, user=request.user, del_flag=0)
        except CompanyInformation.DoesNotExist:
            return APIResponse.error(
                message="Company information not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        company.del_flag = 1
        company.user_id_updated_by = request.user
        company.save(update_fields=["del_flag", "user_id_updated_by", "updated_at"])

        return APIResponse.success(
            message="Company information deleted successfully",
            data=None,
            status_code=status.HTTP_200_OK
        )

class CompanyInfoByCINView(APIView):
    """
    Fetch company info by CIN.
    - Can fetch from third-party API or fallback to local DB/dummy data.
    """
    permission_classes = [IsAuthenticated]

    CIN_REGEX = re.compile(r'^[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$')

    def get(self, request, cin):
        # ✅ Step 1: Validate CIN format
        if not cin or not self.CIN_REGEX.match(cin):
            return APIResponse.error(
                message="Invalid CIN format. CIN must be a 21-character alphanumeric code (e.g. U12345MH2010PTC123456).",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Step 2: Call service layer only if CIN is valid
        result = CompanyInfoService.get_company_data_by_cin(cin)

        # ✅ Step 3: Handle no data case
        if not result or not result.get("data"):
            return APIResponse.error(
                message="No company data found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # ✅ Step 4: Success response
        return APIResponse.success(
            data=result["data"],
            message="Company information fetched successfully",
            status_code=status.HTTP_200_OK
        )

# class CompanyInformationCreateView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]
    
#     def post(self,request):
#         serializer = CompanyInfoSerializer(data=request.data, context={'request': request})


#         if serializer.is_valid():
#             data = serializer.save()
#             return Response( { 
#                 "status": "success", 
#                 "message": data["message"], 
#                 "data": { 
#                     "company_id": data["company_id"], 
#                     "company_name": data["company_name"], 
#                     "company_pan_number": data["company_pan_number"],
                     
#                       "pan_holder_name": data["pan_holder_name"], 
#                       "date_of_birth": data["date_of_birth"],
#                         },
#                           }, 
#                       status=status.HTTP_201_CREATED, )
#         return Response( {"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST, )
    


# class PanExtractionView(APIView):
#     parser_classes = [MultiPartParser, FormParser]

#     def post(self, request, *args, **kwargs):
#         serializer = PanExtractionSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         result = serializer.save()
#         return Response(result, status=status.HTTP_200_OK)
    

# class CompanyInfoGetView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def get(self,request,company_id):
#         try:
#             company = CompanyInformation.objects.get(company_id=company_id,user=request.user)
#         except CompanyInformation.DoesNotExist:
#             return Response({
#                 "status":"error","message":"Company information not found."
#             },status=status.HTTP_404_NOT_FOUND)
#         serializer = CompanyInfoGetSerializer(company)
#         return Response({
#             "status":"success",
#             "data":serializer.data,
#         },status=status.HTTP_200_OK)
    
# class CompanyInformationUpdateView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def patch(self, request, company_id):
#         try:
#             company = CompanyInformation.objects.get(company_id=company_id, user=request.user)
#         except CompanyInformation.DoesNotExist:
#             return Response(
#                 {"status": "error", "message": "Company information not found."},
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         serializer = CompanyInfoUpdateSerializer(instance=company, data=request.data, partial=True, context={'request': request})
#         if serializer.is_valid():
#             data = serializer.save()
#             return Response(
#                 {
#                     "status": "success",
#                     "message": data["message"],
#                     "data": {
#                         "company_id": data["company_id"],
#                         "company_name": data["company_name"],
#                         "company_pan_number": data["company_pan_number"],
#                         "pan_holder_name": data["pan_holder_name"],
#                         "date_of_birth": data["date_of_birth"],
#                     },
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

# class CompanyInfoDeleteView(APIView):
#     authentication_classes =[JWTAuthentication]
#     permission_classes =[IsAuthenticated]

#     def delete(self,request,company_id):
#         try:
#             company = CompanyInformation.objects.get(company_id=company_id, user=request.user,del_flag=0)
#         except CompanyInformation.DoesNotExist:
#             return Response({
#                 "status": "error", "message": "Company information not found."
#             },status=status.HTTP_404_NOT_FOUND)
        
#         company.del_flag = 1
#         company.user_id_updated_by = request.user
#         company.save(update_fields=["del_flag", "user_id_updated_by", "updated_at"])
        
        
#         # CompanyOnboardingApplication.objects.filter(company_information=company,user=request.user).delete()

#         # company.delete()

#         return Response({
#             "status": "success",
#                 "message": "Company information deleted successfully."
#         },status=status.HTTP_200_OK)



