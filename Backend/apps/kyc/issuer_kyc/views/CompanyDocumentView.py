
# from rest_framework import status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.parsers import MultiPartParser, FormParser
# from django.db import transaction
# from drf_yasg.utils import swagger_auto_schema
# from drf_yasg import openapi

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


# class CompanyDocumentBulkUploadView(
#     APIView,
#     ApplicationStepUpdateMixin
# ):
#     """
#     Bulk upload all company documents at once.
#     Matches the UI design where all 4 documents are uploaded together.
    
#     NOTE: This is a public endpoint (no authentication required).
#     Used during initial company registration before user login.
#     """
#     permission_classes = []
#     parser_classes = [MultiPartParser, FormParser]

#     @swagger_auto_schema(
#         operation_description="""
#         Upload all company documents at once (as shown in UI design).
        
#         Required files:
#         - certificate_of_incorporation - Mandatory
#         - memorandum_of_association (MoA/AoA) - Mandatory
#         - msme_certificate - Mandatory
#         - import_export_certificate - Mandatory
        
#         All files should be PDF, JPEG, JPG, or PNG format, max 5MB each.
#         """,
#         manual_parameters=[
#             openapi.Parameter(
#                 'company_id',
#                 openapi.IN_PATH,
#                 description="Company ID (UUID)",
#                 type=openapi.TYPE_STRING,
#                 required=True
#             ),
#             openapi.Parameter(
#                 'certificate_of_incorporation',
#                 openapi.IN_FORM,
#                 description="Certificate of Incorporation - Mandatory",
#                 type=openapi.TYPE_FILE,
#                 required=True
#             ),
#             openapi.Parameter(
#                 'memorandum_of_association',
#                 openapi.IN_FORM,
#                 description="Memorandum of Association (MoA/AoA) - Mandatory",
#                 type=openapi.TYPE_FILE,
#                 required=True
#             ),
#             openapi.Parameter(
#                 'msme_certificate',
#                 openapi.IN_FORM,
#                 description="MSME / Udyam Certificate - Mandatory",
#                 type=openapi.TYPE_FILE,
#                 required=True
#             ),
#             openapi.Parameter(
#                 'import_export_certificate',
#                 openapi.IN_FORM,
#                 description="Import Export Certificate (IEC) - Mandatory",
#                 type=openapi.TYPE_FILE,
#                 required=True
#             ),
#         ],
#         responses={
#             201: openapi.Response(
#                 description="Documents uploaded successfully",
#                 examples={
#                     "application/json": {
#                         "success": True,
#                         "message": "All documents uploaded successfully",
#                         "data": {
#                             "uploaded_count": 4,
#                             "documents": [],
#                             "step_completed": True
#                         }
#                     }
#                 }
#             ),
#             400: "Bad Request - Validation errors",
#             404: "Company not found"
#         }
#     )
#     def post(self, request, company_id):
#         """Upload all documents at once - public endpoint for onboarding"""
#         from ..models.CompanyInformationModel import CompanyInformation
#         from ..models.CompanyDocumentModel import CompanyDocument
        
#         try:
#             company = CompanyInformation.objects.select_related('application').get(
#                 company_id=company_id,
#                 del_flag=0
#             )
#         except CompanyInformation.DoesNotExist:
#             return Response(
#                 {
#                     'success': False,
#                     'message': 'Company not found'
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
        
#         existing_docs = CompanyDocument.objects.filter(
#             company_id=company_id,
#             del_flag=0
#         ).count()
        
#         if existing_docs > 0:
#             return Response(
#                 {
#                     'success': False,
#                     'message': 'Documents already uploaded. Use update endpoint to modify.',
#                     'existing_count': existing_docs
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         serializer = CompanyDocumentBulkUploadSerializer(
#             data=request.data,
#             context={
#                 'company_id': company_id,
#                 'request': request
#             }
#         )
        
#         if serializer.is_valid():
#             try:
#                 with transaction.atomic():
#                     documents = serializer.save()
                    
#                     if hasattr(company, 'application') and company.application:
#                         self.update_document_step(company)
#             except Exception as e:
#                 return Response(
#                     {
#                         'success': False,
#                         'message': f'Failed to upload documents: {str(e)}'
#                     },
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )
            
#             documents_data = [
#                 {
#                     'document_id': str(doc.document_id),
#                     'document_name': doc.document_name,
#                     'document_name_display': doc.get_document_name_display(),
#                     'document_type': doc.document_type,
#                     'file_size': doc.file_size,
#                     'uploaded_at': doc.uploaded_at.isoformat(),
#                     'is_mandatory': doc.is_mandatory,
#                 }
#                 for doc in documents
#             ]
            
#             step_completed = CompanyDocument.check_company_documents_complete(company_id)
            
#             return Response(
#                 {
#                     'success': True,
#                     'message': 'All documents uploaded successfully',
#                     'data': {
#                         'uploaded_count': len(documents),
#                         'documents': documents_data,
#                         'step_completed': step_completed
#                     }
#                 },
#                 status=status.HTTP_201_CREATED
#             )
        
#         return Response(
#             DocumentResponseFormatter.format_error_response(
#                 "Validation failed",
#                 serializer.errors
#             ),
#             status=status.HTTP_400_BAD_REQUEST
#         )


# class CompanyDocumentListView(
#     APIView,
#     DocumentQueryOptimizationMixin
# ):
#     """
#     List all documents for a company with upload status.
#     Public endpoint - no authentication required.
#     """
#     permission_classes = []

#     @swagger_auto_schema(
#         operation_description="Get list of all documents for a company",
#         manual_parameters=[
#             openapi.Parameter(
#                 'company_id',
#                 openapi.IN_PATH,
#                 description="Company ID (UUID)",
#                 type=openapi.TYPE_STRING,
#                 required=True
#             )
#         ],
#         responses={
#             200: CompanyDocumentListSerializer(many=True),
#             404: "Company not found"
#         }
#     )
#     def get(self, request, company_id):
#         """Get all documents for company - public endpoint"""
#         from ..models.CompanyInformationModel import CompanyInformation
        
#         try:
#             company = CompanyInformation.objects.get(
#                 company_id=company_id,
#                 del_flag=0
#             )
#         except CompanyInformation.DoesNotExist:
#             return Response(
#                 {
#                     'success': False,
#                     'message': 'Company not found'
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
        
#         documents = self.get_optimized_documents_queryset(company_id)
#         doc_status = DocumentStatusChecker.get_company_document_status(company_id)
#         serializer = CompanyDocumentListSerializer(documents, many=True)
        
#         return Response(
#             DocumentResponseFormatter.format_list_response(
#                 serializer.data,
#                 doc_status
#             ),
#             status=status.HTTP_200_OK
#         )


# class CompanyDocumentDetailView(
#     APIView,
#     DocumentQueryOptimizationMixin,
#     SoftDeleteMixin
# ):
#     """
#     Retrieve, update or delete a specific document.
#     Public endpoint - no authentication required during onboarding.
#     """
#     permission_classes = []
#     parser_classes = [MultiPartParser, FormParser]

#     @swagger_auto_schema(
#         operation_description="Get document details with file data",
#         manual_parameters=[
#             openapi.Parameter(
#                 'company_id',
#                 openapi.IN_PATH,
#                 description="Company ID (UUID)",
#                 type=openapi.TYPE_STRING,
#                 required=True
#             ),
#             openapi.Parameter(
#                 'document_id',
#                 openapi.IN_PATH,
#                 description="Document ID (UUID)",
#                 type=openapi.TYPE_STRING,
#                 required=True
#             )
#         ],
#         responses={
#             200: CompanyDocumentDetailSerializer(),
#             404: "Document or Company not found"
#         }
#     )
#     def get(self, request, company_id, document_id):
#         """Get document with file data - public endpoint"""
#         from ..models.CompanyInformationModel import CompanyInformation
        
#         try:
#             CompanyInformation.objects.get(
#                 company_id=company_id,
#                 del_flag=0
#             )
#         except CompanyInformation.DoesNotExist:
#             return Response(
#                 {
#                     'success': False,
#                     'message': 'Company not found'
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
        
#         try:
#             document = self.get_document_with_company(document_id, company_id)
#         except Exception as e:
#             return Response(
#                 {
#                     'success': False,
#                     'message': 'Document not found'
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
        
#         serializer = CompanyDocumentDetailSerializer(document)
        
#         return Response(
#             {
#                 'success': True,
#                 'data': serializer.data
#             },
#             status=status.HTTP_200_OK
#         )

#     @swagger_auto_schema(
#         operation_description="Update/Replace a specific document",
#         manual_parameters=[
#             openapi.Parameter(
#                 'company_id',
#                 openapi.IN_PATH,
#                 description="Company ID (UUID)",
#                 type=openapi.TYPE_STRING,
#                 required=True
#             ),
#             openapi.Parameter(
#                 'document_id',
#                 openapi.IN_PATH,
#                 description="Document ID (UUID)",
#                 type=openapi.TYPE_STRING,
#                 required=True
#             ),
#             openapi.Parameter(
#                 'file',
#                 openapi.IN_FORM,
#                 description="New document file",
#                 type=openapi.TYPE_FILE,
#                 required=True
#             )
#         ],
#         responses={
#             200: openapi.Response(
#                 description="Document updated successfully"
#             ),
#             400: "Validation failed",
#             404: "Document or Company not found"
#         }
#     )
#     def put(self, request, company_id, document_id):
#         """Replace existing document using serializer.update() method"""
#         from ..models.CompanyInformationModel import CompanyInformation
        
#         try:
#             CompanyInformation.objects.get(
#                 company_id=company_id,
#                 del_flag=0
#             )
#         except CompanyInformation.DoesNotExist:
#             return Response(
#                 {
#                     'success': False,
#                     'message': 'Company not found'
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
        
#         try:
#             document = self.get_document_with_company(document_id, company_id)
#         except Exception as e:
#             return Response(
#                 {
#                     'success': False,
#                     'message': 'Document not found'
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
        
#         update_data = {
#             'document_name': document.document_name,
#             'file': request.FILES.get('file')
#         }
        
#         if not update_data['file']:
#             return Response(
#                 {
#                     'success': False,
#                     'message': 'No file provided'
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         serializer = CompanySingleDocumentUploadSerializer(
#             instance=document,
#             data=update_data,
#             context={
#                 'company_id': company_id,
#                 'request': request
#             }
#         )
        
#         if serializer.is_valid():
#             try:
#                 updated_document = serializer.save()
                
#                 return Response(
#                     DocumentResponseFormatter.format_success_response(
#                         updated_document,
#                         "Document updated successfully"
#                     ),
#                     status=status.HTTP_200_OK
#                 )
#             except Exception as e:
#                 return Response(
#                     {
#                         'success': False,
#                         'message': f'Failed to update document: {str(e)}'
#                     },
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )
        
#         return Response(
#             DocumentResponseFormatter.format_error_response(
#                 "Failed to update document",
#                 serializer.errors
#             ),
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     @swagger_auto_schema(
#         operation_description="Soft delete a document and revalidate application step",
#         manual_parameters=[
#             openapi.Parameter(
#                 'company_id',
#                 openapi.IN_PATH,
#                 description="Company ID (UUID)",
#                 type=openapi.TYPE_STRING,
#                 required=True
#             ),
#             openapi.Parameter(
#                 'document_id',
#                 openapi.IN_PATH,
#                 description="Document ID (UUID)",
#                 type=openapi.TYPE_STRING,
#                 required=True
#             )
#         ],
#         responses={
#             200: openapi.Response(
#                 description="Document deleted successfully",
#                 examples={
#                     "application/json": {
#                         "success": True,
#                         "message": "Document deleted successfully",
#                         "step_invalidated": True
#                     }
#                 }
#             ),
#             404: "Document or Company not found"
#         }
#     )
#     def delete(self, request, company_id, document_id):
#         """Soft delete document and revalidate application completion"""
#         from ..models.CompanyInformationModel import CompanyInformation
        
#         try:
#             CompanyInformation.objects.get(
#                 company_id=company_id,
#                 del_flag=0
#             )
#         except CompanyInformation.DoesNotExist:
#             return Response(
#                 {
#                     'success': False,
#                     'message': 'Company not found'
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
        
#         try:
#             document = self.get_document_with_company(document_id, company_id)
#         except Exception as e:
#             return Response(
#                 {
#                     'success': False,
#                     'message': 'Document not found'
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
        
#         serializer = CompanySingleDocumentUploadSerializer(
#             context={
#                 'company_id': company_id,
#                 'request': request
#             }
#         )
        
#         try:
#             step_invalidated = serializer.soft_delete(document)
            
#             return Response(
#                 {
#                     'success': True,
#                     'message': 'Document deleted successfully',
#                     'step_invalidated': step_invalidated
#                 },
#                 status=status.HTTP_200_OK
#             )
#         except Exception as e:
#             return Response(
#                 {
#                     'success': False,
#                     'message': f'Failed to delete document: {str(e)}'
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# class CompanyDocumentStatusView(APIView):
#     """
#     Check document upload status for a company.
#     Shows which mandatory documents are missing.
#     Public endpoint - no authentication required.
#     """
#     permission_classes = []

#     @swagger_auto_schema(
#         operation_description="""
#         Get document upload status for a company.
        
#         Returns:
#         - Total documents count
#         - Mandatory documents count  
#         - Uploaded mandatory documents count
#         - List of missing mandatory documents
#         - All mandatory uploaded status (boolean)
#         """,
#         manual_parameters=[
#             openapi.Parameter(
#                 'company_id',
#                 openapi.IN_PATH,
#                 description="Company ID (UUID)",
#                 type=openapi.TYPE_STRING,
#                 required=True
#             )
#         ],
#         responses={
#             200: CompanyDocumentStatusSerializer(),
#             404: "Company not found"
#         }
#     )
#     def get(self, request, company_id):
#         """Get document upload status - public endpoint"""
#         from ..models.CompanyInformationModel import CompanyInformation
        
#         try:
#             CompanyInformation.objects.get(
#                 company_id=company_id,
#                 del_flag=0
#             )
#         except CompanyInformation.DoesNotExist:
#             return Response(
#                 {
#                     'success': False,
#                     'message': 'Company not found'
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
        
#         status_data = DocumentStatusChecker.get_company_document_status(company_id)
#         serializer = CompanyDocumentStatusSerializer(status_data)
        
#         return Response(
#             {
#                 'success': True,
#                 'data': serializer.data
#             },
#             status=status.HTTP_200_OK
#         )


# class CompanySingleDocumentUploadView(
#     APIView,
#     ApplicationStepUpdateMixin
# ):
#     """
#     Upload a single document (used for adding individual documents).
#     Public endpoint - no authentication required during onboarding.
#     """
#     permission_classes = []
#     parser_classes = [MultiPartParser, FormParser]

#     @swagger_auto_schema(
#         operation_description="""
#         Upload a single document for a company.
        
#         Required:
#         - document_name: Choose from available document types
#         - file: PDF, JPEG, JPG, or PNG (max 5MB)
#         """,
#         manual_parameters=[
#             openapi.Parameter(
#                 'company_id',
#                 openapi.IN_PATH,
#                 description="Company ID (UUID)",
#                 type=openapi.TYPE_STRING,
#                 required=True
#             ),
#             openapi.Parameter(
#                 'document_name',
#                 openapi.IN_FORM,
#                 description="Document type",
#                 type=openapi.TYPE_STRING,
#                 required=True,
#                 enum=['CERTIFICATE_INC', 'MOA', 'MSME', 'IEC']
#             ),
#             openapi.Parameter(
#                 'file',
#                 openapi.IN_FORM,
#                 description="Document file",
#                 type=openapi.TYPE_FILE,
#                 required=True
#             )
#         ],
#         responses={
#             201: openapi.Response(
#                 description="Document uploaded successfully",
#                 examples={
#                     "application/json": {
#                         "success": True,
#                         "message": "Document uploaded successfully",
#                         "data": {
#                             "document_id": "uuid",
#                             "document_name": "MOA",
#                             "step_completed": False
#                         }
#                     }
#                 }
#             ),
#             400: "Validation failed",
#             404: "Company not found",
#             409: "Document already exists"
#         }
#     )
#     def post(self, request, company_id):
#         """Upload single document - public endpoint"""
#         from ..models.CompanyInformationModel import CompanyInformation
#         from ..models.CompanyDocumentModel import CompanyDocument
        
#         try:
#             company = CompanyInformation.objects.select_related('application').get(
#                 company_id=company_id,
#                 del_flag=0
#             )
#         except CompanyInformation.DoesNotExist:
#             return Response(
#                 {
#                     'success': False,
#                     'message': 'Company not found'
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
        
#         document_name = request.data.get('document_name')
#         if document_name:
#             existing_doc = CompanyDocument.objects.filter(
#                 company_id=company_id,
#                 document_name=document_name,
#                 del_flag=0
#             ).exists()
            
#             if existing_doc:
#                 return Response(
#                     {
#                         'success': False,
#                         'message': f'Document {document_name} already exists. Use update endpoint to modify.'
#                     },
#                     status=status.HTTP_409_CONFLICT
#                 )
        
#         serializer = CompanySingleDocumentUploadSerializer(
#             data=request.data,
#             context={
#                 'company_id': company_id,
#                 'request': request
#             }
#         )
        
#         if serializer.is_valid():
#             try:
#                 with transaction.atomic():
#                     document = serializer.save()
                    
#                     if hasattr(company, 'application') and company.application:
#                         self.update_document_step(company)
                
#                 step_completed = CompanyDocument.check_company_documents_complete(company_id)
                
#                 return Response(
#                     {
#                         'success': True,
#                         'message': 'Document uploaded successfully',
#                         'data': {
#                             'document_id': str(document.document_id),
#                             'document_name': document.document_name,
#                             'document_name_display': document.get_document_name_display(),
#                             'document_type': document.document_type,
#                             'file_size': document.file_size,
#                             'uploaded_at': document.uploaded_at.isoformat(),
#                             'is_mandatory': document.is_mandatory,
#                             'step_completed': step_completed
#                         }
#                     },
#                     status=status.HTTP_201_CREATED
#                 )
#             except Exception as e:
#                 return Response(
#                     {
#                         'success': False,
#                         'message': f'Failed to upload document: {str(e)}'
#                     },
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )
        
#         return Response(
#             DocumentResponseFormatter.format_error_response(
#                 "Validation failed",
#                 serializer.errors
#             ),
#             status=status.HTTP_400_BAD_REQUEST
#         )


# class CompanyDocumentVerificationView(APIView):
#     """
#     Admin endpoint to verify/reject uploaded documents.
#     Requires authentication and admin permissions.
#     """
#     permission_classes = [IsAuthenticated]

#     @swagger_auto_schema(
#         operation_description="""
#         Verify or reject a company document (Admin only).
        
#         Request body:
#         {
#             "is_verified": true/false,
#             "rejection_reason": "Optional reason if rejected"
#         }
#         """,
#         manual_parameters=[
#             openapi.Parameter(
#                 'company_id',
#                 openapi.IN_PATH,
#                 description="Company ID (UUID)",
#                 type=openapi.TYPE_STRING,
#                 required=True
#             ),
#             openapi.Parameter(
#                 'document_id',
#                 openapi.IN_PATH,
#                 description="Document ID (UUID)",
#                 type=openapi.TYPE_STRING,
#                 required=True
#             )
#         ],
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             required=['is_verified'],
#             properties={
#                 'is_verified': openapi.Schema(
#                     type=openapi.TYPE_BOOLEAN,
#                     description='Verification status'
#                 ),
#                 'rejection_reason': openapi.Schema(
#                     type=openapi.TYPE_STRING,
#                     description='Reason for rejection (if not verified)'
#                 )
#             }
#         ),
#         responses={
#             200: openapi.Response(
#                 description="Document verification updated",
#                 examples={
#                     "application/json": {
#                         "success": True,
#                         "message": "Document verified successfully",
#                         "data": {
#                             "document_id": "uuid",
#                             "is_verified": True
#                         }
#                     }
#                 }
#             ),
#             403: "Permission denied",
#             404: "Document not found"
#         }
#     )
#     def patch(self, request, company_id, document_id):
#         """Update document verification status - admin only"""
#         from ..models.CompanyDocumentModel import CompanyDocument
#         from ..models.CompanyInformationModel import CompanyInformation
        
#         if not request.user.is_staff:
#             return Response(
#                 {
#                     'success': False,
#                     'message': 'Permission denied. Admin access required.'
#                 },
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         try:
#             CompanyInformation.objects.get(
#                 company_id=company_id,
#                 del_flag=0
#             )
#         except CompanyInformation.DoesNotExist:
#             return Response(
#                 {
#                     'success': False,
#                     'message': 'Company not found'
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
        
#         try:
#             document = CompanyDocument.objects.get(
#                 document_id=document_id,
#                 company_id=company_id,
#                 del_flag=0
#             )
#         except CompanyDocument.DoesNotExist:
#             return Response(
#                 {
#                     'success': False,
#                     'message': 'Document not found'
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
        
#         is_verified = request.data.get('is_verified')
#         if is_verified is None:
#             return Response(
#                 {
#                     'success': False,
#                     'message': 'is_verified field is required'
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         document.is_verified = is_verified
#         document.user_id_updated_by = request.user
#         document.save(update_fields=['is_verified', 'user_id_updated_by', 'updated_at'])
        
#         message = "Document verified successfully" if is_verified else "Document rejected"
        
#         return Response(
#             {
#                 'success': True,
#                 'message': message,
#                 'data': {
#                     'document_id': str(document.document_id),
#                     'document_name': document.document_name,
#                     'is_verified': document.is_verified,
#                     'verified_by': str(request.user.user_id),
#                     'verified_at': document.updated_at.isoformat()
#                 }
#             },
#             status=status.HTTP_200_OK
#         )

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from ..serializers.CompanyDocumentSerializer import (
    CompanyDocumentBulkUploadSerializer,
    CompanyDocumentListSerializer,
    CompanyDocumentDetailSerializer,
    CompanyDocumentStatusSerializer,
    CompanySingleDocumentUploadSerializer
)
from ..mixins.DocumentMixins import (
    CompanyOwnershipMixin,
    DocumentQueryOptimizationMixin,
    ApplicationStepUpdateMixin,
    SoftDeleteMixin
)
from ..utils.DocumentUtils import (
    DocumentStatusChecker,
    DocumentResponseFormatter
)

logger = logging.getLogger(__name__)


class CompanyDocumentBulkUploadView(APIView, ApplicationStepUpdateMixin):
    """
    Bulk upload company documents at once.
    Only Certificate of Incorporation is MANDATORY.
    MOA, MSME, and IEC are OPTIONAL.
    """
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Bulk upload company documents.",
        manual_parameters=[
            openapi.Parameter('company_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True),

            openapi.Parameter('certificate_of_incorporation', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),

            openapi.Parameter('moa_aoa_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('moa_aoa_file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),

            openapi.Parameter('msme_udyam_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('msme_udyam_file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),

            openapi.Parameter('import_export_certificate', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
        ],
        responses={201: "Success", 400: "Validation error", 404: "Company not found"}
    )
    def post(self, request, company_id):
        logger.info(
            f"[BULK_UPLOAD] Request for company_id={company_id}, "
            f"files={list(request.FILES.keys())}"
        )

        from ..models.CompanyInformationModel import CompanyInformation
        from ..models.CompanyDocumentModel import CompanyDocument

        # ✅ Validate company exists
        try:
            company = CompanyInformation.objects.select_related("application").get(
                company_id=company_id,
                del_flag=0,
            )
        except CompanyInformation.DoesNotExist:
            return Response(
                {"success": False, "message": "Company not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ✅ Correct field-to-document mapping
        name_map = {
            "certificate_of_incorporation": "CERTIFICATE_INC",
            "moa_aoa_file": request.data.get("moa_aoa_type"),             # MOA or AOA
            "msme_udyam_file": request.data.get("msme_udyam_type"),       # MSME or UDYAM
            "import_export_certificate": "IEC",
        }

        # ✅ Collect ALL duplicate errors
        duplicate_errors = {}

        for field_name, internal_name in name_map.items():
            file_obj = request.FILES.get(field_name)

            if not file_obj:
                continue  # Skip field if no file uploaded

            if not internal_name:
                continue  # If user didn't select dropdown type (MOA/MSME)

            # ✅ Check if doc already exists
            exists = CompanyDocument.objects.filter(
                company_id=company_id,
                document_name=internal_name,
                del_flag=0,
            ).exists()

            if exists:
                duplicate_errors[field_name] = (
                    f"{internal_name} already exists. Delete it before uploading again."
                )

        # ✅ If ANY duplicates: return ALL errors TOGETHER
        if duplicate_errors:
            return Response(
                {
                    "success": False,
                    "message": "Validation failed",
                    "errors": duplicate_errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ Pass to serializer for deeper validation
        serializer = CompanyDocumentBulkUploadSerializer(
            data=request.data,
            context={"company_id": company_id, "request": request},
        )

        if serializer.is_valid():
            try:
                with transaction.atomic():

                    documents = serializer.save()

                    mandatory_count = sum(1 for d in documents if d.is_mandatory)
                    optional_count = len(documents) - mandatory_count

                    # ✅ Update application step
                    if hasattr(company, "application") and company.application:
                        self.update_document_step(company)

            except Exception as e:
                logger.error(f"[BULK_UPLOAD] Error: {str(e)}", exc_info=True)
                return Response(
                    {"success": False, "message": f"Failed to upload: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # ✅ Prepare successful response
            documents_data = [
                {
                    "document_id": str(doc.document_id),
                    "document_name": doc.document_name,
                    "document_name_display": doc.get_document_name_display(),
                    "document_type": doc.document_type,
                    "file_size": doc.file_size,
                    "uploaded_at": doc.uploaded_at.isoformat(),
                    "is_mandatory": doc.is_mandatory,
                }
                for doc in documents
            ]

            step_completed = CompanyDocument.check_company_documents_complete(company_id)

            return Response(
                {
                    "success": True,
                    "message": "Documents uploaded successfully",
                    "data": {
                        "uploaded_count": len(documents),
                        "mandatory_count": mandatory_count,
                        "optional_count": optional_count,
                        "documents": documents_data,
                        "step_completed": step_completed,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        # ❌ Serializer validation failed (size, file type, missing dropdown, mandatory)
        return Response(
            {
                "success": False,
                "message": "Validation failed",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

class CompanyDocumentListView(APIView, DocumentQueryOptimizationMixin):
    """
    List all documents for a company with upload status.
    Public endpoint - no authentication required.
    """
    permission_classes = []

    @swagger_auto_schema(
        operation_description="Get list of all documents for a company",
        manual_parameters=[
            openapi.Parameter(
                'company_id', openapi.IN_PATH,
                description="Company ID (UUID)",
                type=openapi.TYPE_STRING, required=True
            )
        ],
        responses={
            200: CompanyDocumentListSerializer(many=True),
            404: "Company not found"
        }
    )
    def get(self, request, company_id):
        """Get all documents for company - public endpoint"""
        logger.info(f"[LIST_DOCS] Request for company_id={company_id}")
        
        from ..models.CompanyInformationModel import CompanyInformation
        
        try:
            company = CompanyInformation.objects.get(
                company_id=company_id,
                del_flag=0
            )
            logger.debug(f"[LIST_DOCS] Company found: {company.company_name}")
        except CompanyInformation.DoesNotExist:
            logger.error(f"[LIST_DOCS] Company not found: company_id={company_id}")
            return Response(
                {'success': False, 'message': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            documents = self.get_optimized_documents_queryset(company_id)
            doc_status = DocumentStatusChecker.get_company_document_status(company_id)
            serializer = CompanyDocumentListSerializer(documents, many=True)
            
            logger.info(
                f"[LIST_DOCS] Success for company_id={company_id}: "
                f"{len(documents)} documents found"
            )
            
            return Response(
                DocumentResponseFormatter.format_list_response(
                    serializer.data,
                    doc_status
                ),
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(
                f"[LIST_DOCS] Failed for company_id={company_id}: {str(e)}",
                exc_info=True
            )
            return Response(
                {'success': False, 'message': f'Failed to retrieve documents: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CompanyDocumentDetailView(APIView, DocumentQueryOptimizationMixin, SoftDeleteMixin):
    """
    Retrieve, update or delete a specific document.
    Public endpoint - no authentication required during onboarding.
    """
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Get document details with file data",
        manual_parameters=[
            openapi.Parameter(
                'company_id', openapi.IN_PATH,
                description="Company ID (UUID)",
                type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'document_id', openapi.IN_PATH,
                description="Document ID (UUID)",
                type=openapi.TYPE_STRING, required=True
            )
        ],
        responses={
            200: CompanyDocumentDetailSerializer(),
            404: "Document or Company not found"
        }
    )
    def get(self, request, company_id, document_id):
        """Get document with file data - public endpoint"""
        logger.info(
            f"[GET_DOC] Request for company_id={company_id}, document_id={document_id}"
        )
        
        from ..models.CompanyInformationModel import CompanyInformation
        
        try:
            CompanyInformation.objects.get(company_id=company_id, del_flag=0)
            logger.debug(f"[GET_DOC] Company verified: company_id={company_id}")
        except CompanyInformation.DoesNotExist:
            logger.error(f"[GET_DOC] Company not found: company_id={company_id}")
            return Response(
                {'success': False, 'message': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            document = self.get_document_with_company(document_id, company_id)
            serializer = CompanyDocumentDetailSerializer(document)
            
            logger.info(
                f"[GET_DOC] Success: document_id={document_id}, "
                f"document_name={document.document_name}"
            )
            
            return Response(
                {'success': True, 'data': serializer.data},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(
                f"[GET_DOC] Document not found: document_id={document_id}, "
                f"company_id={company_id}, error={str(e)}",
                exc_info=True
            )
            return Response(
                {'success': False, 'message': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Update/Replace a specific document",
        manual_parameters=[
            openapi.Parameter(
                'company_id', openapi.IN_PATH,
                description="Company ID (UUID)",
                type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'document_id', openapi.IN_PATH,
                description="Document ID (UUID)",
                type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'file', openapi.IN_FORM,
                description="New document file",
                type=openapi.TYPE_FILE, required=True
            )
        ],
        responses={
            200: openapi.Response(description="Document updated successfully"),
            400: "Validation failed",
            404: "Document or Company not found"
        }
    )
    def put(self, request, company_id, document_id):
        """Replace existing document using serializer.update() method"""
        logger.info(
            f"[UPDATE_DOC] Request for company_id={company_id}, document_id={document_id}"
        )
        
        from ..models.CompanyInformationModel import CompanyInformation
        
        try:
            CompanyInformation.objects.get(company_id=company_id, del_flag=0)
            logger.debug(f"[UPDATE_DOC] Company verified: company_id={company_id}")
        except CompanyInformation.DoesNotExist:
            logger.error(f"[UPDATE_DOC] Company not found: company_id={company_id}")
            return Response(
                {'success': False, 'message': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            document = self.get_document_with_company(document_id, company_id)
            logger.debug(
                f"[UPDATE_DOC] Document found: {document.document_name}, "
                f"is_mandatory={document.is_mandatory}"
            )
        except Exception as e:
            logger.error(
                f"[UPDATE_DOC] Document not found: document_id={document_id}, "
                f"error={str(e)}"
            )
            return Response(
                {'success': False, 'message': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        update_data = {
            'document_name': document.document_name,
            'file': request.FILES.get('file')
        }
        
        if not update_data['file']:
            logger.warning(f"[UPDATE_DOC] No file provided for document_id={document_id}")
            return Response(
                {'success': False, 'message': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CompanySingleDocumentUploadSerializer(
            instance=document,
            data=update_data,
            context={'company_id': company_id, 'request': request}
        )
        
        if serializer.is_valid():
            try:
                updated_document = serializer.save()
                
                logger.info(
                    f"[UPDATE_DOC] Success: document_id={document_id}, "
                    f"new_size={updated_document.file_size}"
                )
                
                return Response(
                    DocumentResponseFormatter.format_success_response(
                        updated_document,
                        "Document updated successfully"
                    ),
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                logger.error(
                    f"[UPDATE_DOC] Update failed for document_id={document_id}: {str(e)}",
                    exc_info=True
                )
                return Response(
                    {
                        'success': False,
                        'message': f'Failed to update document: {str(e)}'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        logger.error(
            f"[UPDATE_DOC] Validation failed for document_id={document_id}: "
            f"{serializer.errors}"
        )
        return Response(
            DocumentResponseFormatter.format_error_response(
                "Failed to update document",
                serializer.errors
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    @swagger_auto_schema(
        operation_description="Soft delete a document and revalidate application step",
        manual_parameters=[
            openapi.Parameter(
                'company_id', openapi.IN_PATH,
                description="Company ID (UUID)",
                type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'document_id', openapi.IN_PATH,
                description="Document ID (UUID)",
                type=openapi.TYPE_STRING, required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Document deleted successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Document deleted successfully",
                        "step_invalidated": True
                    }
                }
            ),
            404: "Document or Company not found"
        }
    )
    def delete(self, request, company_id, document_id):
        """Soft delete document and revalidate application completion"""
        logger.info(
            f"[DELETE_DOC] Request for company_id={company_id}, document_id={document_id}"
        )
        
        from ..models.CompanyInformationModel import CompanyInformation
        
        try:
            CompanyInformation.objects.get(company_id=company_id, del_flag=0)
            logger.debug(f"[DELETE_DOC] Company verified: company_id={company_id}")
        except CompanyInformation.DoesNotExist:
            logger.error(f"[DELETE_DOC] Company not found: company_id={company_id}")
            return Response(
                {'success': False, 'message': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            document = self.get_document_with_company(document_id, company_id)
            logger.debug(
                f"[DELETE_DOC] Document found: {document.document_name}, "
                f"is_mandatory={document.is_mandatory}"
            )
        except Exception as e:
            logger.error(
                f"[DELETE_DOC] Document not found: document_id={document_id}, "
                f"error={str(e)}"
            )
            return Response(
                {'success': False, 'message': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CompanySingleDocumentUploadSerializer(
            context={'company_id': company_id, 'request': request}
        )
        
        try:
            step_invalidated = serializer.soft_delete(document)
            
            logger.info(
                f"[DELETE_DOC] Success: document_id={document_id}, "
                f"step_invalidated={step_invalidated}"
            )
            
            return Response(
                {
                    'success': True,
                    'message': 'Document deleted successfully',
                    'step_invalidated': step_invalidated
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(
                f"[DELETE_DOC] Delete failed for document_id={document_id}: {str(e)}",
                exc_info=True
            )
            return Response(
                {'success': False, 'message': f'Failed to delete document: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CompanyDocumentStatusView(APIView):
    """
    Check document upload status for a company.
    Shows which mandatory documents are missing.
    Public endpoint - no authentication required.
    """
    permission_classes = []

    @swagger_auto_schema(
        operation_description="""
        Get document upload status for a company.
        
        Returns:
        - Total documents count
        - Mandatory documents count  
        - Optional documents count
        - Uploaded mandatory/optional counts
        - List of missing mandatory documents
        - All mandatory uploaded status (boolean)
        """,
        manual_parameters=[
            openapi.Parameter(
                'company_id', openapi.IN_PATH,
                description="Company ID (UUID)",
                type=openapi.TYPE_STRING, required=True
            )
        ],
        responses={
            200: CompanyDocumentStatusSerializer(),
            404: "Company not found"
        }
    )
    def get(self, request, company_id):
        """Get document upload status - public endpoint"""
        logger.info(f"[DOC_STATUS] Request for company_id={company_id}")
        
        from ..models.CompanyInformationModel import CompanyInformation
        
        try:
            CompanyInformation.objects.get(company_id=company_id, del_flag=0)
            logger.debug(f"[DOC_STATUS] Company verified: company_id={company_id}")
        except CompanyInformation.DoesNotExist:
            logger.error(f"[DOC_STATUS] Company not found: company_id={company_id}")
            return Response(
                {'success': False, 'message': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            status_data = DocumentStatusChecker.get_company_document_status(company_id)
            serializer = CompanyDocumentStatusSerializer(status_data)
            
            logger.info(
                f"[DOC_STATUS] Success for company_id={company_id}: "
                f"mandatory={status_data.get('uploaded_mandatory')}/{status_data.get('mandatory_documents')}, "
                f"optional={status_data.get('uploaded_optional')}/{status_data.get('optional_documents')}"
            )
            
            return Response(
                {'success': True, 'data': serializer.data},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(
                f"[DOC_STATUS] Failed for company_id={company_id}: {str(e)}",
                exc_info=True
            )
            return Response(
                {'success': False, 'message': f'Failed to retrieve status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CompanySingleDocumentUploadView(APIView, ApplicationStepUpdateMixin):
    """
    Upload a single document BEFORE login.
    Public endpoint.
    """
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, company_id):
        from ..models.CompanyDocumentModel import CompanyDocument
        from ..models.CompanyInformationModel import CompanyInformation

        # ✅ SAFE user id for logs
        safe_user_id = getattr(request.user, "user_id", "anonymous")

        logger.info(
            f"[SINGLE_UPLOAD] Start | company={company_id}, "
            f"user={safe_user_id}, data={dict(request.data)}"
        )

        # ✅ Validate company
        try:
            company = CompanyInformation.objects.get(company_id=company_id, del_flag=0)
        except CompanyInformation.DoesNotExist:
            return Response(
                {"success": False, "message": "Company not found"},
                status=404
            )

        document_name = request.data.get("document_name")

        # ✅ Check duplicates
        if document_name:
            exists = CompanyDocument.objects.filter(
                company_id=company_id,
                document_name=document_name,
                del_flag=0
            ).exists()

            if exists:
                return Response(
                    {
                        "success": False,
                        "message": f"Document '{document_name}' already exists. Delete it before uploading new one."
                    },
                    status=409
                )

        # ✅ Validate serializer
        serializer = CompanySingleDocumentUploadSerializer(
            data=request.data,
            context={"company_id": company_id, "request": request}
        )

        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Validation failed", "errors": serializer.errors},
                status=400
            )

        # ✅ Save document
        try:
            with transaction.atomic():
                document = serializer.save()

                # ✅ Update onboarding step
                if hasattr(company, "application") and company.application:
                    self.update_document_step(company)

        except Exception as e:
            logger.error(f"[SINGLE_UPLOAD] Failed: {e}", exc_info=True)
            return Response(
                {"success": False, "message": f"Failed to upload document: {str(e)}"},
                status=500
            )

        step_completed = CompanyDocument.check_company_documents_complete(company_id)

        return Response(
            {
                "success": True,
                "message": "Document uploaded successfully",
                "data": {
                    "document_id": str(document.document_id),
                    "document_name": document.document_name,
                    "document_name_display": document.get_document_name_display(),
                    "document_type": document.document_type,
                    "file_size": document.file_size,
                    "uploaded_at": document.uploaded_at.isoformat(),
                    "is_mandatory": document.is_mandatory,
                    "step_completed": step_completed
                }
            },
            status=201
        )

class CompanyDocumentVerificationView(APIView):
    """
    Admin endpoint to verify/reject uploaded documents.
    Requires authentication and admin permissions.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="""
        Verify or reject a company document (Admin only).
        
        Request body:
        {
            "is_verified": true/false,
            "rejection_reason": "Optional reason if rejected"
        }
        """,
        manual_parameters=[
            openapi.Parameter(
                'company_id', openapi.IN_PATH,
                description="Company ID (UUID)",
                type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'document_id', openapi.IN_PATH,
                description="Document ID (UUID)",
                type=openapi.TYPE_STRING, required=True
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['is_verified'],
            properties={
                'is_verified': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Verification status'
                ),
                'rejection_reason': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Reason for rejection (if not verified)'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Document verification updated",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Document verified successfully",
                        "data": {
                            "document_id": "uuid",
                            "is_verified": True
                        }
                    }
                }
            ),
            403: "Permission denied",
            404: "Document not found"
        }
    )
    def patch(self, request, company_id, document_id):
        """Update document verification status - admin only"""
        logger.info(
            f"[VERIFY_DOC] Request from user={request.user.user_id}, "
            f"company_id={company_id}, document_id={document_id}"
        )
        
        from ..models.CompanyDocumentModel import CompanyDocument
        from ..models.CompanyInformationModel import CompanyInformation
        
        if not request.user.is_staff:
            logger.warning(
                f"[VERIFY_DOC] Permission denied for user={request.user.user_id}"
            )
            return Response(
                {
                    'success': False,
                    'message': 'Permission denied. Admin access required.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            CompanyInformation.objects.get(company_id=company_id, del_flag=0)
            logger.debug(f"[VERIFY_DOC] Company verified: company_id={company_id}")
        except CompanyInformation.DoesNotExist:
            logger.error(f"[VERIFY_DOC] Company not found: company_id={company_id}")
            return Response(
                {'success': False, 'message': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            document = CompanyDocument.objects.get(
                document_id=document_id,
                company_id=company_id,
                del_flag=0
            )
            logger.debug(
                f"[VERIFY_DOC] Document found: {document.document_name}, "
                f"current_verification={document.is_verified}"
            )
        except CompanyDocument.DoesNotExist:
            logger.error(
                f"[VERIFY_DOC] Document not found: document_id={document_id}"
            )
            return Response(
                {'success': False, 'message': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        is_verified = request.data.get('is_verified')
        if is_verified is None:
            logger.warning("[VERIFY_DOC] Missing is_verified field in request")
            return Response(
                {'success': False, 'message': 'is_verified field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            document.is_verified = is_verified
            document.user_id_updated_by = request.user
            document.save(update_fields=['is_verified', 'user_id_updated_by', 'updated_at'])
            
            message = "Document verified successfully" if is_verified else "Document rejected"
            
            logger.info(
                f"[VERIFY_DOC] Success: document_id={document_id}, "
                f"is_verified={is_verified}, verified_by={request.user.user_id}"
            )
            
            return Response(
                {
                    'success': True,
                    'message': message,
                    'data': {
                        'document_id': str(document.document_id),
                        'document_name': document.document_name,
                        'is_verified': document.is_verified,
                        'verified_by': str(request.user.user_id),
                        'verified_at': document.updated_at.isoformat()
                    }
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(
                f"[VERIFY_DOC] Verification failed for document_id={document_id}: "
                f"{str(e)}",
                exc_info=True
            )
            return Response(
                {'success': False, 'message': f'Failed to verify document: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )