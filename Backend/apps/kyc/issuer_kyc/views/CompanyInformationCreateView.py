# from rest_framework.views import APIView
# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.parsers import MultiPartParser, FormParser
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework.permissions import IsAuthenticated, AllowAny
# from config.common.response import APIResponse
# import re

# from ..models import CompanyInformation
# from ..models.CompanyInformationModel import SectorChoices
# from ..serializers.CompanyInfoSerializer import (
#     CompanyInfoSerializer,
#     PanExtractionSerializer,
#     CompanyInfoGetSerializer,
#     CompanyInfoUpdateSerializer
# )
# from ..services.company_information.company_info_service import CompanyInfoService


# # -------------------------------------------------------------------
# # 1️⃣ PAN OCR EXTRACTION (upload once, return extracted data + token)
# # -------------------------------------------------------------------
# class PanExtractionView(APIView):
#     parser_classes = [MultiPartParser, FormParser]
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = PanExtractionSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         result = serializer.save()

#         return APIResponse.success(
#             data=result,
#             message="PAN details extracted successfully",
#             status_code=status.HTTP_200_OK
#         )


# # -------------------------------------------------------------------
# # 2️⃣ FINAL COMPANY CREATION (NO FILE UPLOAD, only file_token)
# # -------------------------------------------------------------------
# class CompanyInformationCreateView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = CompanyInfoSerializer(data=request.data, context={"request": request})

#         if serializer.is_valid():
#             data = serializer.save()

#             response_data = {
#                 "company_id": data["company_id"],
#                 "company_name": data["company_name"],
#                 "company_pan_number": data["company_pan_number"],
#                 "pan_holder_name": data["pan_holder_name"],
#                 "date_of_birth": data["date_of_birth"],
#             }

#             return APIResponse.success(
#                 data=response_data,
#                 message=data["message"],
#                 status_code=status.HTTP_201_CREATED
#             )

#         return APIResponse.error(
#             message="Validation error",
#             errors=serializer.errors,
#             status_code=status.HTTP_400_BAD_REQUEST
#         )


# # -------------------------------------------------------------------
# # 3️⃣ GET COMPANY INFO
# # -------------------------------------------------------------------
# class CompanyInfoGetView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def get(self, request, company_id):
#         try:
#             company = CompanyInformation.objects.get(
#                 company_id=company_id, user=request.user, del_flag=0
#             )
#         except CompanyInformation.DoesNotExist:
#             return APIResponse.error(
#                 message="Company information not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         serializer = CompanyInfoGetSerializer(company)
#         return APIResponse.success(
#             data=serializer.data,
#             message="Company information fetched successfully",
#             status_code=status.HTTP_200_OK
#         )


# # -------------------------------------------------------------------
# # 4️⃣ UPDATE COMPANY INFO (NO FILE UPDATE, NO OCR)
# # -------------------------------------------------------------------
# class CompanyInformationUpdateView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def patch(self, request, company_id):
#         try:
#             company = CompanyInformation.objects.get(
#                 company_id=company_id, user=request.user, del_flag=0
#             )
#         except CompanyInformation.DoesNotExist:
#             return APIResponse.error(
#                 message="Company information not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         serializer = CompanyInfoUpdateSerializer(
#             instance=company, data=request.data, partial=True, context={"request": request}
#         )

#         if serializer.is_valid():
#             company = serializer.save()

#             response_data = {
#                 "company_id": company.company_id,
#                 "company_name": company.company_name,
#                 "company_pan_number": company.company_pan_number,
#                 "pan_holder_name": company.pan_holder_name,
#                 "date_of_birth": company.date_of_birth,
#             }

#             return APIResponse.success(
#                 data=response_data,
#                 message="Company information updated successfully",
#                 status_code=status.HTTP_200_OK
#             )

#         return APIResponse.error(
#             message="Validation error",
#             errors=serializer.errors,
#             status_code=status.HTTP_400_BAD_REQUEST
#         )


# # -------------------------------------------------------------------
# # 5️⃣ DELETE COMPANY (Soft delete)
# # -------------------------------------------------------------------
# class CompanyInfoDeleteView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def delete(self, request, company_id):
#         try:
#             company = CompanyInformation.objects.get(
#                 company_id=company_id, user=request.user, del_flag=0
#             )
#         except CompanyInformation.DoesNotExist:
#             return APIResponse.error(
#                 message="Company information not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         company.del_flag = 1
#         company.user_id_updated_by = request.user
#         company.save(update_fields=["del_flag", "user_id_updated_by", "updated_at"])

#         return APIResponse.success(
#             message="Company deleted successfully",
#             status_code=status.HTTP_200_OK
#         )


# # -------------------------------------------------------------------
# # 6️⃣ CIN LOOKUP API
# # -------------------------------------------------------------------
# class CompanyInfoByCINView(APIView):
#     permission_classes = [IsAuthenticated]

#     CIN_REGEX = re.compile(r'^[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$')

#     def get(self, request, cin):
#         if not self.CIN_REGEX.match(cin):
#             return APIResponse.error(
#                 message="Invalid CIN format",
#                 status_code=status.HTTP_400_BAD_REQUEST
#             )

#         result = CompanyInfoService.get_company_data_by_cin(cin)

#         if not result or not result.get("data"):
#             return APIResponse.error(
#                 message="No company data found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         return APIResponse.success(
#             data=result["data"],
#             message="Company information fetched successfully",
#             status_code=status.HTTP_200_OK
#         )


# # -------------------------------------------------------------------
# # 7️⃣ SECTOR DROPDOWN API
# # -------------------------------------------------------------------
# class SectorChoicesView(APIView):
#     permission_classes = [AllowAny]

#     def get(self, request):
#         data = [{"key": key, "label": label} for key, label in SectorChoices.choices]

#         return APIResponse.success(
#             data=data,
#             message="Sector list fetched successfully",
#             status_code=status.HTTP_200_OK
#         )
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny

from config.common.response import APIResponse
import re

from ..models import CompanyInformation
from ..models.CompanyInformationModel import SectorChoices

from ..serializers.CompanyInfoSerializer import (
    CompanyInfoSerializer,
    PanExtractionSerializer,
    CompanyInfoGetSerializer,
    CompanyInfoUpdateSerializer
)

from ..services.company_information.company_info_service import CompanyInfoService
from apps.utils.get_company_from_token import get_company_from_token


# ======================================================================
# 1️⃣ PAN OCR EXTRACTION
# ======================================================================
class PanExtractionView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PanExtractionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return APIResponse.success(
            data=result,
            message="PAN details extracted successfully",
            status_code=status.HTTP_200_OK
        )


# ======================================================================
# 2️⃣ FINAL COMPANY CREATION (FIRST TIME)
# ======================================================================
class CompanyInformationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CompanyInfoSerializer(
            data=request.data,
            context={"request": request}
        )

        if not serializer.is_valid():
            return APIResponse.error(
                message="Validation error",
                errors=serializer.errors
            )

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


# ======================================================================
# 3️⃣ GET, UPDATE, DELETE — USING TOKEN (NO company_id IN URL)
# ======================================================================
class CompanyProfileView(APIView):
    """
    GET → Fetch company using token
    PUT → Full update company using token
    PATCH → Partial update company using token
    DELETE → Soft delete company using token
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    # -------------------- GET --------------------
    def get(self, request):
        try:
            company = get_company_from_token(request)
        except Exception as e:
            return APIResponse.error(message=str(e), status_code=401)

        serializer = CompanyInfoGetSerializer(company)
        return APIResponse.success(
            data=serializer.data,
            message="Company information fetched successfully",
            status_code=200
        )

    # -------------------- PUT (FULL UPDATE) --------------------
    def put(self, request):
        try:
            company = get_company_from_token(request)
        except Exception as e:
            return APIResponse.error(message=str(e), status_code=401)

        # FULL UPDATE → partial=False
        serializer = CompanyInfoUpdateSerializer(
            instance=company,
            data=request.data,
            partial=False,
            context={"request": request}
        )

        if not serializer.is_valid():
            return APIResponse.error(
                message="Validation error",
                errors=serializer.errors
            )

        company = serializer.save()

        response_data = {
            "company_id": company.company_id,
            "company_name": company.company_name,
            "company_pan_number": company.company_pan_number,
            "pan_holder_name": company.pan_holder_name,
            "date_of_birth": company.date_of_birth,
        }

        return APIResponse.success(
            data=response_data,
            message="Company information fully updated successfully",
            status_code=200
        )

    # -------------------- PATCH --------------------
    def patch(self, request):
        try:
            company = get_company_from_token(request)
        except Exception as e:
            return APIResponse.error(message=str(e), status_code=401)

        # PARTIAL UPDATE → partial=True
        serializer = CompanyInfoUpdateSerializer(
            instance=company,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if not serializer.is_valid():
            return APIResponse.error(
                message="Validation error",
                errors=serializer.errors
            )

        company = serializer.save()

        response_data = {
            "company_id": company.company_id,
            "company_name": company.company_name,
            "company_pan_number": company.company_pan_number,
            "pan_holder_name": company.pan_holder_name,
            "date_of_birth": company.date_of_birth,
        }

        return APIResponse.success(
            data=response_data,
            message="Company information updated successfully",
            status_code=200
        )

    # -------------------- DELETE --------------------
    def delete(self, request):
        try:
            company = get_company_from_token(request)
        except Exception as e:
            return APIResponse.error(message=str(e), status_code=401)

        company.del_flag = 1
        company.user_id_updated_by = request.user
        company.save(update_fields=["del_flag", "user_id_updated_by", "updated_at"])

        return APIResponse.success(
            message="Company deleted successfully",
            status_code=200
        )

# ======================================================================
# 4️⃣ CIN LOOKUP API
# ======================================================================
class CompanyInfoByCINView(APIView):
    permission_classes = [IsAuthenticated]

    CIN_REGEX = re.compile(r'^[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$')

    def get(self, request, cin):
        if not self.CIN_REGEX.match(cin):
            return APIResponse.error(
                message="Invalid CIN format",
                status_code=400
            )

        result = CompanyInfoService.get_company_data_by_cin(cin)

        if not result or not result.get("data"):
            return APIResponse.error(
                message="No company data found",
                status_code=404
            )

        return APIResponse.success(
            data=result["data"],
            message="Company information fetched successfully",
            status_code=200
        )


# ======================================================================
# 5️⃣ SECTOR DROPDOWN API
# ======================================================================
class SectorChoicesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        data = [{"key": key, "label": label} for key, label in SectorChoices.choices]

        return APIResponse.success(
            data=data,
            message="Sector list fetched successfully",
            status_code=200
        )
