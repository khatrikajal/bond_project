from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from typing import Any, Optional, Dict
from django.conf import settings


# ----------  Example How to use ------------
# class CompanyView(APIView):
#     def get(self, request, pk):
#         try:
#             company = Company.objects.get(pk=pk)
#             serializer = CompanySerializer(company)
#             return APIResponse.success(
#                 data=serializer.data,
#                 message="Company fetched successfully"
#             )
#         except Company.DoesNotExist:
#             return APIResponse.error(
#                 message="Company not found",
#                 status_code=404
#             )

# class CompanyCreateView(APIView):
#     def post(self, request):
#         serializer = CompanySerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)  # auto handled by your exception handler
#         serializer.save()
#         return APIResponse.success(data=serializer.data, message="Company created successfully")

class APIResponse:
    """
    Standardized API Response wrapper for consistent response format
    """
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = status.HTTP_200_OK
    ) -> Response:
        """
        Return a success response
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            meta: Additional metadata
        """
        response_data = {
            "success": True,
            "message": message,
            "data": data,
            "errors": None,
           
        }
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(
        message: str = "An error occurred",
        errors: Any = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        data: Any = None
    ) -> Response:
        """
        Return an error response
        
        Args:
            message: Error message
            errors: Error details (can be dict, list, or string)
            status_code: HTTP status code
            data: Optional partial data
        """
        response_data = {
            "success": False,
            "message": message,
            "data": data,
            "errors": errors,
          
        }
        return Response(response_data, status=status_code)
