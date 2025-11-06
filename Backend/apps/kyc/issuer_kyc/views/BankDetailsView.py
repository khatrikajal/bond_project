from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.kyc.issuer_kyc.models.BankDetailsModel import BankDetails
from apps.kyc.issuer_kyc.serializers.BankDetailsSerializer import BankDetailsSerializer
from apps.kyc.issuer_kyc.serializers.BankDetailsVerifySerializer import BankDetailsVerifySerializer
from apps.kyc.issuer_kyc.serializers.BankDocumentExtractSerializer import BankDocumentExtractSerializer
from apps.kyc.issuer_kyc.services.bank_details.extract_bank_details import DocumentExtractorFactory 
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from apps.kyc.issuer_kyc.services.onboarding_service import update_step_4_status
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class BankDocumentExtractView(APIView):
    """
    POST - Upload a single bank document (any type)
    Only one document is allowed per company; previous document is removed.
    """

    def post(self, request, company_id):
        # Verify company exists
        try:
            company = CompanyInformation.objects.get(pk=company_id)
        except CompanyInformation.DoesNotExist:
            return Response({"detail": "Company not found"}, status=404)

        serializer = BankDocumentExtractSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        doc_type = serializer.validated_data["document_type"]
        uploaded_file = serializer.validated_data["file"]

        field_map = {
            "cheque": "cancelled_cheque",
            "bank_statement": "bank_statement",
            "passbook": "passbook",
        }
        file_field_name = field_map[doc_type]

        try:
            # Get or create BankDetails
            bank_details, _ = BankDetails.objects.get_or_create(company=company)

            with transaction.atomic():
                # Delete any existing document (regardless of type) and clear DB fields
                update_fields = []
                for field in ["cancelled_cheque", "bank_statement", "passbook"]:
                    existing_file = getattr(bank_details, field)
                    if existing_file and existing_file.name:
                        existing_file.delete(save=False)  # remove file from storage
                        setattr(bank_details, field, None)
                        update_fields.append(field)

                # Save new file in the correct field
                setattr(bank_details, file_field_name, uploaded_file)
                update_fields.append(file_field_name)

                # Save all changes together
                bank_details.save(update_fields=update_fields)

            # Extract data using OCR for frontend preview
            file_obj = getattr(bank_details, file_field_name)
            with file_obj.open("rb") as f:
                bytes_data = f.read()

            extractor = DocumentExtractorFactory.get_extractor(doc_type)
            extracted_data = extractor.extract(bytes_data)

            return Response({
                "message": "Document uploaded successfully",
                "file_url": file_obj.url,
                "extracted_data": extracted_data,
                "bank_detail_id": bank_details.bank_detail_id,
            }, status=200)

        except Exception as e:
            logger.exception("Document upload or extraction failed")
            return Response(
                {"detail": f"Upload failed: {str(e)}"},
                status=500
            )



class BankDTO:
    def __init__(self, data: dict):
        for key, value in data.items():
            setattr(self, key, value)


class BankDetailsVerifyView(APIView):
    """
    Verifies a company's bank details and updates the BankDetails model.
    """

    def post(self, request, company_id):
        # Validate input
        serializer = BankDetailsVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        # Fetch BankDetails instance
        try:
            bank_details = BankDetails.objects.get(company_id=company_id)
        except BankDetails.DoesNotExist:
            return Response({"detail": "Bank details not found for this company"}, status=404)

        # Create DTO for verification logic
        bank = BankDTO(serializer.validated_data)

        # Run verification safely
        try:
            from apps.kyc.issuer_kyc.services.bank_details.verify_bank_details import verify_bank_details
            result = verify_bank_details(bank)
        except Exception as e:
            return Response({"detail": f"Verification service failed: {str(e)}"}, status=500)

        # Update only verified fields
        with transaction.atomic():
            bank_details.is_verified = result.get("success", False)
            if result.get("success"):
                bank_details.verified_at = timezone.now()
            else:
                bank_details.verified_at = None  # Clear if verification fails
            bank_details.save(update_fields=["is_verified", "verified_at"])

        return Response(result, status=200)
    







class BankDetailsView(APIView):
    """
    Handles GET, POST, PUT/PATCH for a company's bank details.
    NOTE: Documents are handled separately via BankDocumentExtractView.
    """

    def get_object(self, company_id):
        try:
            return BankDetails.objects.get(company_id=company_id, del_flag=0)
        except BankDetails.DoesNotExist:
            return None


    def get(self, request, company_id):
        bank = self.get_object(company_id)
        if not bank:
            return Response({"detail": "Not found"}, status=404)
        return Response(BankDetailsSerializer(bank).data)

    def post(self, request, company_id):
        """Create or update bank details, including document upload"""
        serializer = BankDetailsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        bank = serializer.save(company_id=company_id)
        return Response(BankDetailsSerializer(bank).data, status=200)

    def put(self, request, company_id):
        """Full update of bank details (all fields except existing documents unless uploaded)"""
        bank = self.get_object(company_id)
        if not bank:
            return Response({"detail": "Not found"}, status=404)

        serializer = BankDetailsSerializer(bank, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        bank = serializer.save(company_id=company_id)
        return Response(BankDetailsSerializer(bank).data, status=200)

    def patch(self, request, company_id):
        """Partial update - only update provided fields, including new documents"""
        bank = self.get_object(company_id)
        if not bank:
            return Response({"detail": "Not found"}, status=404)

        serializer = BankDetailsSerializer(bank, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        bank = serializer.save(company_id=company_id)
        return Response(BankDetailsSerializer(bank).data, status=200)
    def delete(self, request, company_id):
        bank = self.get_object(company_id)
        if not bank:
            return Response({"detail": "Not found"}, status=404)

        company = bank.company
        try:
            with transaction.atomic():
                # Soft delete
                bank.del_flag = 1
                bank.save(update_fields=["del_flag"])

                # Update onboarding step 4 (pass empty list for bank_ids)
                if hasattr(company, "application") and company.application:
                    update_step_4_status(company.application, bank_ids=[])

        except Exception as e:
            return Response({"detail": f"Delete failed: {str(e)}"}, status=500)

        return Response({"detail": f"Bank details {bank.bank_detail_id} soft-deleted successfully"}, status=200)
