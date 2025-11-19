# apps/authentication/views/CompanyRegistrationView.py

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from apps.authentication.serializers.CompanyRegistrationSerializer import CompanyRegistrationSerializer
from config.common.response import APIResponse
from django.db import IntegrityError


class RegisterCompanyView(APIView):
    """
    POST /api/auth/register-company/
    
    Stage 2 of registration flow:
    - Creates User with verified mobile/email
    - Creates CompanyInformation (KYC)
    - Validates PAN holder name
    - Applies human intervention logic
    - Sends appropriate email
    - Returns user_id, company_id, and verification_status
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = CompanyRegistrationSerializer(
            data=request.data,
            context={"request": request}
        )
        
        try:
            # Validate all fields and session
            serializer.is_valid(raise_exception=True)
            
            # Create User + Company (transaction-safe)
            result = serializer.save()
            
            user = result["user"]
            company = result["company"]
            verification_status = result["verification_status"]
            
            # Prepare response message
            if verification_status == "SUCCESS":
                message = "Registration completed successfully"
            else:
                message = "Registration pending manual verification"
            
            # Return success response
            return APIResponse.success(
                message=message,
                data={
                    "user_id": user.user_id,
                    "company_id": str(company.company_id),
                    "verification_status": verification_status
                }
            )
            
        except IntegrityError as e:
            # Handle unique constraint violations (CIN, PAN)
            error_message = str(e)
            
            if "unique_cin_active_only" in error_message:
                return APIResponse.error(
                    message="Registration failed",
                    errors={"corporate_identification_number": ["This CIN is already registered"]}
                )
            elif "unique_pan_active_only" in error_message:
                return APIResponse.error(
                    message="Registration failed",
                    errors={"company_pan_number": ["This PAN is already registered"]}
                )
            else:
                return APIResponse.error(
                    message="Registration failed",
                    errors={"non_field_errors": ["Database integrity error occurred"]}
                )
        
        except Exception as e:
            # Catch any unexpected errors
            return APIResponse.error(
                message="Registration failed",
                errors={"non_field_errors": [str(e)]}
            )