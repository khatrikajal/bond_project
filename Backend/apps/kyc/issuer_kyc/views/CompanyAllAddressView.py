from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status,serializers
from django.utils import timezone
from apps.kyc.issuer_kyc.models.CompanyAdressModel import CompanyAddress
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from apps.kyc.issuer_kyc.serializers.CompanyAddressSerializer import CompanyAddressSerializer
from rest_framework.permissions import IsAuthenticated
from apps.kyc.issuer_kyc.utils.extract_address import extract_address_from_bill 
import os
import tempfile



class ComapnyAllAdressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CompanyAddressSerializer()
        try:
            address_list = serializer.get_all_active_addresses()
            return Response(
                {
                    "success": True,
                    "total_records": len(address_list),
                    "addresses": address_list
                },
                status=status.HTTP_200_OK
            )
        except serializers.ValidationError as e:
            return Response(
                {"success": False, "errors": e.detail},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"success": False, "error": f"Failed to fetch active addresses: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    # def get(self, request):
    #     return Response({"msg": "ok"})



    ##Extract address doc API
    """
    API that accepts a file (PDF or Image), performs OCR extraction, 
    and returns structured address details.
    """
    def post(self, request):
        uploaded_file = request.FILES.get("document")

        # 1️⃣ Validate file input
        if not uploaded_file:
            return Response(
                {"success": False, "error": "No document uploaded. Please attach a file using key 'document'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        temp_file_path = None

        try:
            # 2️⃣ Save the uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            # 3️⃣ Call OCR + address extraction utility
            extracted_data = extract_address_from_bill(temp_file_path)

            # 4️⃣ Delete temporary file
            os.remove(temp_file_path)

            # 5️⃣ Return structured OCR response
            return Response(
                {
                    "success": True,
                    "message": "Address extracted successfully.",
                    "data": extracted_data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            # Cleanup on error
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return Response(
                {"success": False, "error": f"OCR extraction failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
