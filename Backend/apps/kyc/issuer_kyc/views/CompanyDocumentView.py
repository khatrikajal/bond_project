

# from rest_framework import status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.parsers import MultiPartParser, FormParser
# from django.db import transaction
# from drf_yasg.utils import swagger_auto_schema
# from drf_yasg import openapi
# import logging
# from django.utils import timezone

# # ✅ import your centralized APIResponse helper
# from config.common.response import APIResponse

# from ..serializers.CompanyDocumentSerializer import (
#     CompanyDocumentBulkUploadSerializer,
#     CompanyDocumentListSerializer,
#     CompanyDocumentDetailSerializer,
#     CompanyDocumentStatusSerializer,
#     CompanySingleDocumentUploadSerializer
# )
# from ..mixins.DocumentMixins import (
#     CompanyOwnershipMixin,
#     DocumentQueryOptimizationMixin,
#     ApplicationStepUpdateMixin,
#     SoftDeleteMixin
# )
# from ..utils.DocumentUtils import (
#     DocumentStatusChecker,
#     DocumentResponseFormatter
# )

# logger = logging.getLogger(__name__)


# # ============================================================================
# # BULK UPLOAD VIEW
# # ============================================================================
# class CompanyDocumentBulkUploadView(APIView):
#     """Bulk upload company documents"""
#     permission_classes = []
#     parser_classes = [MultiPartParser, FormParser]

#     def update_step_three(self, company, documents):
#         """Update onboarding step 3 without serialization issues"""
#         application = getattr(company, "application", None)
#         if not application:
#             return

#         step_key = "3"
#         mandatory_uploaded = any(doc.is_mandatory for doc in documents)

#         step_state = {
#             "completed": mandatory_uploaded,
#             "completed_at": timezone.now().isoformat(),
#             "record_id": [str(doc.document_id) for doc in documents],
#         }

#         application.step_completion[step_key] = step_state

#         if application.status == "INITIATED":
#             application.status = "IN_PROGRESS"

#         application.save(update_fields=["step_completion", "status", "updated_at"])

#     @swagger_auto_schema(
#         operation_description="Bulk upload company documents",
#         manual_parameters=[
#             openapi.Parameter('company_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True),
#             openapi.Parameter('certificate_of_incorporation', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
#             openapi.Parameter('moa_aoa_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
#             openapi.Parameter('moa_aoa_file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
#             openapi.Parameter('msme_udyam_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
#             openapi.Parameter('msme_udyam_file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
#             openapi.Parameter('import_export_certificate', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
#         ],
#         responses={201: "Success", 400: "Validation error", 404: "Company not found"}
#     )
#     def post(self, request, company_id):
#         from ..models.CompanyInformationModel import CompanyInformation
#         from ..models.CompanyDocumentModel import CompanyDocument

#         logger.info(f"[BULK_UPLOAD] company_id={company_id}")

#         # ✅ Validate company
#         try:
#             company = CompanyInformation.objects.select_related("application").get(
#                 company_id=company_id, del_flag=0
#             )
#         except CompanyInformation.DoesNotExist:
#             return APIResponse.error(
#                 message="Company not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         # ✅ Validate input data
#         serializer = CompanyDocumentBulkUploadSerializer(
#             data=request.data,
#             context={"company_id": company_id, "request": request}
#         )

#         if not serializer.is_valid():
#             return APIResponse.error(
#                 message="Validation failed",
#                 errors=serializer.errors
#             )

#         # ✅ Save documents in transaction
#         try:
#             with transaction.atomic():
#                 documents = serializer.save()
#                 self.update_step_three(company, documents)
#         except Exception as e:
#             logger.error(f"[BULK_UPLOAD] Error: {str(e)}", exc_info=True)
#             return APIResponse.error(
#                 message="Failed to upload documents",
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#         # ✅ Prepare response
#         step_completed = CompanyDocument.check_company_documents_complete(company_id)
        
#         return APIResponse.success(
#             data={
#                 "uploaded_count": len(documents),
#                 "step_completed": step_completed,
#                 "documents": [
#                     {
#                         "id": str(doc.document_id),
#                         "name": doc.get_document_name_display(),
#                         "type": doc.document_type,
#                         "size": doc.file_size,
#                         "mandatory": doc.is_mandatory
#                     }
#                     for doc in documents
#                 ]
#             },
#             message="Documents uploaded successfully",
#             status_code=status.HTTP_201_CREATED
#         )

# # ============================================================================
# # LIST DOCUMENTS VIEW
# # ============================================================================
# class CompanyDocumentListView(APIView, DocumentQueryOptimizationMixin):
#     """List all documents for a company"""
#     permission_classes = []

#     @swagger_auto_schema(
#         operation_description="Get list of all documents",
#         manual_parameters=[
#             openapi.Parameter('company_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True)
#         ],
#         responses={200: CompanyDocumentListSerializer(many=True), 404: "Company not found"}
#     )
#     def get(self, request, company_id):
#         from ..models.CompanyInformationModel import CompanyInformation

#         logger.info(f"[LIST_DOCS] company_id={company_id}")

#         # Validate company
#         try:
#             CompanyInformation.objects.get(company_id=company_id, del_flag=0)
#         except CompanyInformation.DoesNotExist:
#             return APIResponse.error(
#                 message="Company not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         try:
#             documents = self.get_optimized_documents_queryset(company_id)
#             doc_status = DocumentStatusChecker.get_company_document_status(company_id)
#             serializer = CompanyDocumentListSerializer(documents, many=True)

#             return APIResponse.success(
#                 data={
#                     "documents": serializer.data,
#                     "summary": {
#                         "total": doc_status.get("total_documents", 0),
#                         "mandatory_uploaded": doc_status.get("uploaded_mandatory", 0),
#                         "optional_uploaded": doc_status.get("uploaded_optional", 0),
#                         "all_mandatory_complete": doc_status.get("all_mandatory_uploaded", False)
#                     }
#                 },
#                 message="Documents retrieved successfully"
#             )

#         except Exception as e:
#             logger.error(f"[LIST_DOCS] Error: {str(e)}", exc_info=True)
#             return APIResponse.error(
#                 message="Failed to retrieve documents",
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# # ============================================================================
# # DOCUMENT DETAIL VIEW
# # ============================================================================
# class CompanyDocumentDetailView(APIView, DocumentQueryOptimizationMixin, SoftDeleteMixin):
#     """Retrieve, update or delete a specific document"""
#     permission_classes = []
#     parser_classes = [MultiPartParser, FormParser]

#     @swagger_auto_schema(
#         operation_description="Get document details",
#         manual_parameters=[
#             openapi.Parameter('company_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True),
#             openapi.Parameter('document_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True)
#         ],
#         responses={200: CompanyDocumentDetailSerializer(), 404: "Not found"}
#     )
#     def get(self, request, company_id, document_id):
#         from ..models.CompanyInformationModel import CompanyInformation

#         logger.info(f"[GET_DOC] company_id={company_id}, document_id={document_id}")

#         try:
#             CompanyInformation.objects.get(company_id=company_id, del_flag=0)
#         except CompanyInformation.DoesNotExist:
#             return APIResponse.error(
#                 message="Company not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         try:
#             document = self.get_document_with_company(document_id, company_id)
#             serializer = CompanyDocumentDetailSerializer(document, context={'request': request})

#             return APIResponse.success(
#                 data=serializer.data,
#                 message="Document retrieved successfully"
#             )

#         except Exception as e:
#             logger.error(f"[GET_DOC] Error: {str(e)}", exc_info=True)
#             return APIResponse.error(
#                 message="Document not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#     @swagger_auto_schema(
#         operation_description="Update document",
#         manual_parameters=[
#             openapi.Parameter('company_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True),
#             openapi.Parameter('document_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True),
#             openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True)
#         ],
#         responses={200: "Updated", 400: "Validation error", 404: "Not found"}
#     )
#     def put(self, request, company_id, document_id):
#         from ..models.CompanyInformationModel import CompanyInformation

#         logger.info(f"[UPDATE_DOC] company_id={company_id}, document_id={document_id}")

#         try:
#             CompanyInformation.objects.get(company_id=company_id, del_flag=0)
#         except CompanyInformation.DoesNotExist:
#             return APIResponse.error(
#                 message="Company not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         try:
#             document = self.get_document_with_company(document_id, company_id)
#         except Exception:
#             return APIResponse.error(
#                 message="Document not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         if not request.FILES.get('file'):
#             return APIResponse.error(message="File is required")

#         update_data = {
#             'document_name': document.document_name,
#             'file': request.FILES.get('file')
#         }

#         serializer = CompanySingleDocumentUploadSerializer(
#             instance=document,
#             data=update_data,
#             context={'company_id': company_id, 'request': request}
#         )

#         if not serializer.is_valid():
#             return APIResponse.error(
#                 message="Validation failed",
#                 errors=serializer.errors
#             )

#         try:
#             updated_document = serializer.save()

#             return APIResponse.success(
#                 data={
#                     "id": str(updated_document.document_id),
#                     "name": updated_document.get_document_name_display(),
#                     "type": updated_document.document_type,
#                     "size": updated_document.file_size,
#                     "updated_at": updated_document.updated_at.isoformat()
#                 },
#                 message="Document updated successfully"
#             )

#         except Exception as e:
#             logger.error(f"[UPDATE_DOC] Error: {str(e)}", exc_info=True)
#             return APIResponse.error(
#                 message="Failed to update document",
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#     @swagger_auto_schema(
#         operation_description="Delete document",
#         manual_parameters=[
#             openapi.Parameter('company_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True),
#             openapi.Parameter('document_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True)
#         ],
#         responses={200: "Deleted", 404: "Not found"}
#     )
#     def delete(self, request, company_id, document_id):
#         from ..models.CompanyInformationModel import CompanyInformation

#         logger.info(f"[DELETE_DOC] company_id={company_id}, document_id={document_id}")

#         try:
#             CompanyInformation.objects.get(company_id=company_id, del_flag=0)
#         except CompanyInformation.DoesNotExist:
#             return APIResponse.error(
#                 message="Company not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         try:
#             document = self.get_document_with_company(document_id, company_id)
#         except Exception:
#             return APIResponse.error(
#                 message="Document not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         serializer = CompanySingleDocumentUploadSerializer(
#             context={'company_id': company_id, 'request': request}
#         )

#         try:
#             serializer.soft_delete(document)

#             return APIResponse.success(
#                 data={
#                     "id": str(document.document_id),
#                     "name": document.get_document_name_display()
#                 },
#                 message="Document deleted successfully"
#             )

#         except Exception as e:
#             logger.error(f"[DELETE_DOC] Error: {str(e)}", exc_info=True)
#             return APIResponse.error(
#                 message="Failed to delete document",
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# # ============================================================================
# # DOCUMENT STATUS VIEW
# # ============================================================================
# class CompanyDocumentStatusView(APIView):
#     """Check document verification status"""
#     permission_classes = []

#     @swagger_auto_schema(
#         operation_description="Get document verification status",
#         manual_parameters=[
#             openapi.Parameter('company_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True)
#         ],
#         responses={200: CompanyDocumentStatusSerializer(), 404: "Company not found"}
#     )
#     def get(self, request, company_id):
#         from ..models.CompanyInformationModel import CompanyInformation
#         from ..models.CompanyDocumentModel import CompanyDocument

#         logger.info(f"[DOC_STATUS] company_id={company_id}")

#         try:
#             CompanyInformation.objects.get(company_id=company_id, del_flag=0)
#         except CompanyInformation.DoesNotExist:
#             return APIResponse.error(
#                 message="Company not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         try:
#             documents = CompanyDocument.objects.filter(
#                 company_id=company_id,
#                 del_flag=0
#             ).values('document_id', 'document_name', 'is_mandatory', 'is_verified', 'uploaded_at')

#             total_docs = len(documents)
#             verified_docs = sum(1 for doc in documents if doc['is_verified'])
#             pending_docs = total_docs - verified_docs
            
#             mandatory_docs = [doc for doc in documents if doc['is_mandatory']]
#             mandatory_verified = sum(1 for doc in mandatory_docs if doc['is_verified'])
            
#             optional_docs = [doc for doc in documents if not doc['is_mandatory']]
#             optional_verified = sum(1 for doc in optional_docs if doc['is_verified'])

#             document_list = [
#                 {
#                     "id": str(doc['document_id']),
#                     "name": dict(CompanyDocument.DOCUMENT_NAMES).get(doc['document_name'], doc['document_name']),
#                     "mandatory": doc['is_mandatory'],
#                     "verification_status": "verified" if doc['is_verified'] else "pending",
#                     "uploaded_at": doc['uploaded_at'].isoformat()
#                 }
#                 for doc in documents
#             ]

#             return APIResponse.success(
#                 data={
#                     "overall_status": "all_verified" if verified_docs == total_docs else "pending_verification",
#                     "statistics": {
#                         "total_documents": total_docs,
#                         "verified": verified_docs,
#                         "pending": pending_docs
#                     },
#                     "mandatory": {
#                         "total": len(mandatory_docs),
#                         "verified": mandatory_verified,
#                         "pending": len(mandatory_docs) - mandatory_verified,
#                         "all_verified": mandatory_verified == len(mandatory_docs) if mandatory_docs else False
#                     },
#                     "optional": {
#                         "total": len(optional_docs),
#                         "verified": optional_verified,
#                         "pending": len(optional_docs) - optional_verified
#                     },
#                     "documents": document_list
#                 },
#                 message="Document verification status retrieved successfully"
#             )

#         except Exception as e:
#             logger.error(f"[DOC_STATUS] Error: {str(e)}", exc_info=True)
#             return APIResponse.error(
#                 message="Failed to retrieve verification status",
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# # ============================================================================
# # SINGLE DOCUMENT UPLOAD VIEW
# # ============================================================================
# class CompanySingleDocumentUploadView(APIView, ApplicationStepUpdateMixin):
#     """Upload a single document"""
#     permission_classes = []
#     parser_classes = [MultiPartParser, FormParser]

#     @swagger_auto_schema(
#         operation_description="Upload a single document",
#         manual_parameters=[
#             openapi.Parameter('company_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True),
#             openapi.Parameter('document_name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
#             openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True)
#         ],
#         responses={201: "Created", 400: "Validation error", 404: "Not found", 409: "Conflict"}
#     )
#     def post(self, request, company_id):
#         from ..models.CompanyDocumentModel import CompanyDocument
#         from ..models.CompanyInformationModel import CompanyInformation

#         logger.info(f"[SINGLE_UPLOAD] company_id={company_id}")

#         try:
#             company = CompanyInformation.objects.get(company_id=company_id, del_flag=0)
#         except CompanyInformation.DoesNotExist:
#             return APIResponse.error(
#                 message="Company not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         document_name = request.data.get("document_name")
#         if document_name:
#             exists = CompanyDocument.objects.filter(
#                 company_id=company_id,
#                 document_name=document_name,
#                 del_flag=0
#             ).exists()

#             if exists:
#                 return APIResponse.error(
#                     message=f"Document '{document_name}' already exists",
#                     status_code=status.HTTP_409_CONFLICT
#                 )

#         serializer = CompanySingleDocumentUploadSerializer(
#             data=request.data,
#             context={"company_id": company_id, "request": request}
#         )

#         if not serializer.is_valid():
#             return APIResponse.error(
#                 message="Validation failed",
#                 errors=serializer.errors
#             )

#         try:
#             with transaction.atomic():
#                 document = serializer.save()

#                 if hasattr(company, "application") and company.application:
#                     self.update_document_step(company)

#             step_completed = CompanyDocument.check_company_documents_complete(company_id)

#             return APIResponse.success(
#                 data={
#                     "id": str(document.document_id),
#                     "name": document.get_document_name_display(),
#                     "type": document.document_type,
#                     "size": document.file_size,
#                     "mandatory": document.is_mandatory,
#                     "step_completed": step_completed
#                 },
#                 message="Document uploaded successfully",
#                 status_code=status.HTTP_201_CREATED
#             )

#         except Exception as e:
#             logger.error(f"[SINGLE_UPLOAD] Error: {str(e)}", exc_info=True)
#             return APIResponse.error(
#                 message="Failed to upload document",
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# # ============================================================================
# # DOCUMENT VERIFICATION VIEW (ADMIN)
# # ============================================================================
# class CompanyDocumentVerificationView(APIView):
#     """Verify/reject documents (Admin only)"""
#     permission_classes = [IsAuthenticated]

#     @swagger_auto_schema(
#         operation_description="Verify or reject document (Admin only)",
#         manual_parameters=[
#             openapi.Parameter('company_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True),
#             openapi.Parameter('document_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True)
#         ],
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             required=['is_verified'],
#             properties={
#                 'is_verified': openapi.Schema(type=openapi.TYPE_BOOLEAN),
#                 'rejection_reason': openapi.Schema(type=openapi.TYPE_STRING)
#             }
#         ),
#         responses={200: "Verified", 403: "Permission denied", 404: "Not found"}
#     )
#     def patch(self, request, company_id, document_id):
#         from ..models.CompanyDocumentModel import CompanyDocument
#         from ..models.CompanyInformationModel import CompanyInformation

#         logger.info(f"[VERIFY_DOC] user={request.user.user_id}, document_id={document_id}")

#         if not request.user.is_staff:
#             return APIResponse.error(
#                 message="Admin access required",
#                 status_code=status.HTTP_403_FORBIDDEN
#             )

#         try:
#             CompanyInformation.objects.get(company_id=company_id, del_flag=0)
#         except CompanyInformation.DoesNotExist:
#             return APIResponse.error(
#                 message="Company not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         try:
#             document = CompanyDocument.objects.get(
#                 document_id=document_id,
#                 company_id=company_id,
#                 del_flag=0
#             )
#         except CompanyDocument.DoesNotExist:
#             return APIResponse.error(
#                 message="Document not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         is_verified = request.data.get('is_verified')
#         if is_verified is None:
#             return APIResponse.error(message="is_verified field is required")

#         try:
#             document.is_verified = is_verified
#             document.user_id_updated_by = request.user
#             document.save(update_fields=['is_verified', 'user_id_updated_by', 'updated_at'])

#             message = "Document verified successfully" if is_verified else "Document rejected"

#             return APIResponse.success(
#                 data={
#                     "id": str(document.document_id),
#                     "name": document.get_document_name_display(),
#                     "verified": document.is_verified,
#                     "verified_by": str(request.user.user_id),
#                     "verified_at": document.updated_at.isoformat()
#                 },
#                 message=message
#             )

#         except Exception as e:
#             logger.error(f"[VERIFY_DOC] Error: {str(e)}", exc_info=True)
#             return APIResponse.error(
#                 message="Failed to verify document",
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )



from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
import logging

from config.common.response import APIResponse

from ..serializers.CompanyDocumentSerializer import (
    CompanyDocumentBulkUploadSerializer,
    CompanyDocumentListSerializer,
    CompanyDocumentDetailSerializer,
    CompanyDocumentStatusSerializer,
    CompanySingleDocumentUploadSerializer
)

from ..mixins.DocumentMixins import (
    DocumentQueryOptimizationMixin,
    ApplicationStepUpdateMixin,
    SoftDeleteMixin
)

from ..utils.DocumentUtils import DocumentStatusChecker
from apps.utils.get_company_from_token import get_company_from_token

logger = logging.getLogger(__name__)


# ======================================================================
# 🔵 BULK UPLOAD – TOKEN BASED
# ======================================================================

class CompanyDocumentBulkUploadView(APIView):
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser]

    def update_step_three(self, company, documents):
        application = getattr(company, "application", None)
        if not application:
            return

        step_key = "3"
        mandatory_uploaded = any(doc.is_mandatory for doc in documents)

        step_state = {
            "completed": mandatory_uploaded,
            "completed_at": timezone.now().isoformat(),
            "record_id": [str(doc.document_id) for doc in documents],
        }

        application.step_completion[step_key] = step_state

        if application.status == "INITIATED":
            application.status = "IN_PROGRESS"

        application.save(update_fields=["step_completion", "status", "updated_at"])

    @swagger_auto_schema(
        operation_description="Bulk upload documents for authenticated company (resolved from token)",
        manual_parameters=[
            openapi.Parameter('certificate_of_incorporation', openapi.IN_FORM, type=openapi.TYPE_FILE),
            openapi.Parameter('moa_aoa_type', openapi.IN_FORM, type=openapi.TYPE_STRING),
            openapi.Parameter('moa_aoa_file', openapi.IN_FORM, type=openapi.TYPE_FILE),
            openapi.Parameter('msme_udyam_type', openapi.IN_FORM, type=openapi.TYPE_STRING),
            openapi.Parameter('msme_udyam_file', openapi.IN_FORM, type=openapi.TYPE_FILE),
            openapi.Parameter('import_export_certificate', openapi.IN_FORM, type=openapi.TYPE_FILE),
        ],
        responses={201: "Created", 400: "Validation Error", 401: "Unauthorized"}
    )
    def post(self, request):

        logger.info("[BULK_UPLOAD] Token-based request")

        # 1. Resolve company from token
        try:
            company = get_company_from_token(request)
        except Exception as e:
            return APIResponse.error(message=str(e), status_code=401)

        # 2. Pass company instance in context
        serializer = CompanyDocumentBulkUploadSerializer(
            data=request.data,
            context={
                "company": company,
                "request": request
            }
        )

        if not serializer.is_valid():
            return APIResponse.error(
                message="Validation failed",
                errors=serializer.errors
            )

        # 3. Save documents
        try:
            with transaction.atomic():
                documents = serializer.save()
                self.update_step_three(company, documents)

        except Exception as e:
            logger.error(f"[BULK_UPLOAD] Error: {str(e)}", exc_info=True)
            return APIResponse.error(message="Bulk upload failed", status_code=500)

        # 4. Return output
        from ..models.CompanyDocumentModel import CompanyDocument
        step_completed = CompanyDocument.check_company_documents_complete(company.company_id)

        return APIResponse.success(
            message="Documents uploaded successfully",
            data={
                "uploaded_count": len(documents),
                "step_completed": step_completed,
                "documents": [
                    {
                        "id": str(doc.document_id),
                        "name": doc.get_document_name_display(),
                        "type": doc.document_type,
                        "size": doc.file_size,
                        "mandatory": doc.is_mandatory
                    }
                    for doc in documents
                ]
            },
            status_code=201
        )


# ======================================================================
# 🔵 LIST DOCUMENTS – TOKEN BASED
# ======================================================================

class CompanyDocumentListView(APIView, DocumentQueryOptimizationMixin):
    permission_classes = []

    def get(self, request):
        logger.info("[LIST_DOCS] Token-based")

        try:
            company = get_company_from_token(request)
        except Exception as e:
            return APIResponse.error(message=str(e), status_code=401)

        documents = self.get_optimized_documents_queryset(company.company_id)
        doc_status = DocumentStatusChecker.get_company_document_status(company.company_id)

        serializer = CompanyDocumentListSerializer(documents, many=True)

        return APIResponse.success(
            message="Documents retrieved successfully",
            data={
                "documents": serializer.data,
                "summary": {
                    "total": doc_status.get("total_documents", 0),
                    "mandatory_uploaded": doc_status.get("uploaded_mandatory", 0),
                    "optional_uploaded": doc_status.get("uploaded_optional", 0),
                    "all_mandatory_complete": doc_status.get("all_mandatory_uploaded", False)
                }
            }
        )


# ======================================================================
# 🔵 DOCUMENT DETAIL (GET/UPDATE/DELETE)
# ======================================================================

class CompanyDocumentDetailView(APIView, DocumentQueryOptimizationMixin, SoftDeleteMixin):
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, document_id):
        logger.info(f"[GET_DOC] {document_id}")

        try:
            company = get_company_from_token(request)
        except Exception as e:
            return APIResponse.error(message=str(e), status_code=401)

        try:
            document = self.get_document_with_company(document_id, company.company_id)
        except Exception:
            return APIResponse.error(message="Document not found", status_code=404)

        serializer = CompanyDocumentDetailSerializer(document, context={"request": request})
        return APIResponse.success(message="Document retrieved successfully", data=serializer.data)

    def put(self, request, document_id):
        logger.info(f"[UPDATE_DOC] {document_id}")

        try:
            company = get_company_from_token(request)
        except Exception as e:
            return APIResponse.error(message=str(e), status_code=401)

        try:
            document = self.get_document_with_company(document_id, company.company_id)
        except Exception:
            return APIResponse.error(message="Document not found", status_code=404)

        # ensure a file is sent
        if not request.FILES.get("file"):
            return APIResponse.error(message="File is required")

        # Use serializer with instance so validate() can allow updating the same document
        serializer = CompanySingleDocumentUploadSerializer(
            instance=document,
            data={
                "document_name": document.document_name,
                "file": request.FILES["file"]
            },
            context={"company": company, "request": request}
        )

        if not serializer.is_valid():
            return APIResponse.error(message="Validation failed", errors=serializer.errors)

        # serializer.save() will call update() on the instance
        updated_doc = serializer.save()

        return APIResponse.success(
            message="Document updated successfully",
            data={
                "id": str(updated_doc.document_id),
                "name": updated_doc.get_document_name_display(),
                "type": updated_doc.document_type,
                "size": updated_doc.file_size,
                "updated_at": updated_doc.updated_at.isoformat()
            }
        )

    def delete(self, request, document_id):
        logger.info(f"[DELETE_DOC] {document_id}")

        try:
            company = get_company_from_token(request)
        except Exception as e:
            return APIResponse.error(message=str(e), status_code=401)

        try:
            document = self.get_document_with_company(document_id, company.company_id)
        except Exception:
            return APIResponse.error(message="Document not found", status_code=404)

        serializer = CompanySingleDocumentUploadSerializer(
            context={"company": company, "request": request}
        )

        serializer.soft_delete(document)

        return APIResponse.success(
            message="Document deleted successfully",
            data={"id": str(document.document_id)}
        )
# ======================================================================
# 🔵 STATUS VIEW – TOKEN BASED
# ======================================================================

class CompanyDocumentStatusView(APIView):
    permission_classes = []

    def get(self, request):
        from ..models.CompanyDocumentModel import CompanyDocument

        logger.info("[DOC_STATUS] Token-based")

        try:
            company = get_company_from_token(request)
        except Exception as e:
            return APIResponse.error(message=str(e), status_code=401)

        documents = CompanyDocument.objects.filter(
            company_id=company.company_id, del_flag=0
        ).values("document_id", "document_name", "is_mandatory", "is_verified", "uploaded_at")

        total = len(documents)
        verified = sum(1 for d in documents if d["is_verified"])
        pending = total - verified

        mandatory = [d for d in documents if d["is_mandatory"]]
        mandatory_verified = sum(1 for d in mandatory if d["is_verified"])

        optional = [d for d in documents if not d["is_mandatory"]]
        optional_verified = sum(1 for d in optional if d["is_verified"])

        return APIResponse.success(
            message="Document status retrieved",
            data={
                "overall_status": "all_verified" if total == verified else "pending",
                "statistics": {
                    "total_documents": total,
                    "verified": verified,
                    "pending": pending
                },
                "mandatory": {
                    "total": len(mandatory),
                    "verified": mandatory_verified
                },
                "optional": {
                    "total": len(optional),
                    "verified": optional_verified
                }
            }
        )


# ======================================================================
# 🔵 SINGLE UPLOAD – TOKEN BASED
# ======================================================================

class CompanySingleDocumentUploadView(APIView, ApplicationStepUpdateMixin):
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        from ..models.CompanyDocumentModel import CompanyDocument

        logger.info("[SINGLE_UPLOAD] Token-based")

        try:
            company = get_company_from_token(request)
        except Exception as e:
            return APIResponse.error(message=str(e), status_code=401)

        document_name = request.data.get("document_name")

        if CompanyDocument.objects.filter(
            company_id=company.company_id,
            document_name=document_name,
            del_flag=0
        ).exists():
            return APIResponse.error(
                message=f"{document_name} already exists",
                status_code=409
            )

        serializer = CompanySingleDocumentUploadSerializer(
            data=request.data,
            context={"company": company, "request": request}
        )

        if not serializer.is_valid():
            return APIResponse.error(message="Validation failed", errors=serializer.errors)

        with transaction.atomic():
            doc = serializer.save()
            if hasattr(company, "application") and company.application:
                self.update_document_step(company)

        from ..models.CompanyDocumentModel import CompanyDocument
        step_completed = CompanyDocument.check_company_documents_complete(company.company_id)

        return APIResponse.success(
            message="Document uploaded successfully",
            data={
                "id": str(doc.document_id),
                "name": doc.get_document_name_display(),
                "type": doc.document_type,
                "mandatory": doc.is_mandatory,
                "step_completed": step_completed
            },
            status_code=201
        )


# ======================================================================
# 🔵 ADMIN DOCUMENT VERIFICATION (NO COMPANY ID REQUIRED)
# ======================================================================

class CompanyDocumentVerificationView(APIView):
    """Verify/reject documents (Admin only)"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Verify / reject a document (Admin only)",
        manual_parameters=[
            openapi.Parameter('document_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['is_verified'],
            properties={
                'is_verified': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'rejection_reason': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={200: "Verified", 403: "Permission denied", 404: "Not found"}
    )
    def patch(self, request, document_id):
        from ..models.CompanyDocumentModel import CompanyDocument

        if not request.user.is_staff:
            return APIResponse.error(
                message="Admin access required",
                status_code=403
            )

        try:
            doc = CompanyDocument.objects.get(document_id=document_id, del_flag=0)
        except CompanyDocument.DoesNotExist:
            return APIResponse.error(message="Document not found", status_code=404)

        is_verified = request.data.get("is_verified")

        if is_verified is None:
            return APIResponse.error(message="is_verified is required")

        doc.is_verified = is_verified
        doc.rejection_reason = request.data.get("rejection_reason", "")
        doc.user_id_updated_by = request.user
        doc.save(update_fields=["is_verified", "rejection_reason", "user_id_updated_by", "updated_at"])

        msg = "Document verified" if is_verified else "Document rejected"

        return APIResponse.success(
            message=msg,
            data={
                "id": str(doc.document_id),
                "verified": doc.is_verified,
                "verified_at": doc.updated_at.isoformat(),
                "verified_by": str(request.user.user_id)
            }
        )
