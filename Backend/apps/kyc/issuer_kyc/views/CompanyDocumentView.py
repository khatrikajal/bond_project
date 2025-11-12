
# # from rest_framework import status
# # from rest_framework.views import APIView
# # from rest_framework.response import Response
# # from rest_framework.permissions import IsAuthenticated
# # from rest_framework.parsers import MultiPartParser, FormParser
# # from django.db import transaction
# # from drf_yasg.utils import swagger_auto_schema
# # from drf_yasg import openapi

# # from ..serializers.CompanyDocumentSerializer import (
# #     CompanyDocumentBulkUploadSerializer,
# #     CompanyDocumentListSerializer,
# #     CompanyDocumentDetailSerializer,
# #     CompanyDocumentStatusSerializer,
# #     CompanySingleDocumentUploadSerializer
# # )
# # from ..mixins.DocumentMixins import (
# #     CompanyOwnershipMixin,
# #     DocumentQueryOptimizationMixin,
# #     ApplicationStepUpdateMixin,
# #     SoftDeleteMixin
# # )
# # from ..utils.DocumentUtils import (
# #     DocumentStatusChecker,
# #     DocumentResponseFormatter
# # )


# # class CompanyDocumentBulkUploadView(
# #     APIView,
# #     ApplicationStepUpdateMixin
# # ):
# #     """
# #     Bulk upload all company documents at once.
# #     Matches the UI design where all 4 documents are uploaded together.
    
# #     NOTE: This is a public endpoint (no authentication required).
# #     Used during initial company registration before user login.
# #     """
# #     permission_classes = []
# #     parser_classes = [MultiPartParser, FormParser]

# #     @swagger_auto_schema(
# #         operation_description="""
# #         Upload all company documents at once (as shown in UI design).
        
# #         Required files:
# #         - certificate_of_incorporation - Mandatory
# #         - memorandum_of_association (MoA/AoA) - Mandatory
# #         - msme_certificate - Mandatory
# #         - import_export_certificate - Mandatory
        
# #         All files should be PDF, JPEG, JPG, or PNG format, max 5MB each.
# #         """,
# #         manual_parameters=[
# #             openapi.Parameter(
# #                 'company_id',
# #                 openapi.IN_PATH,
# #                 description="Company ID (UUID)",
# #                 type=openapi.TYPE_STRING,
# #                 required=True
# #             ),
# #             openapi.Parameter(
# #                 'certificate_of_incorporation',
# #                 openapi.IN_FORM,
# #                 description="Certificate of Incorporation - Mandatory",
# #                 type=openapi.TYPE_FILE,
# #                 required=True
# #             ),
# #             openapi.Parameter(
# #                 'memorandum_of_association',
# #                 openapi.IN_FORM,
# #                 description="Memorandum of Association (MoA/AoA) - Mandatory",
# #                 type=openapi.TYPE_FILE,
# #                 required=True
# #             ),
# #             openapi.Parameter(
# #                 'msme_certificate',
# #                 openapi.IN_FORM,
# #                 description="MSME / Udyam Certificate - Mandatory",
# #                 type=openapi.TYPE_FILE,
# #                 required=True
# #             ),
# #             openapi.Parameter(
# #                 'import_export_certificate',
# #                 openapi.IN_FORM,
# #                 description="Import Export Certificate (IEC) - Mandatory",
# #                 type=openapi.TYPE_FILE,
# #                 required=True
# #             ),
# #         ],
# #         responses={
# #             201: openapi.Response(
# #                 description="Documents uploaded successfully",
# #                 examples={
# #                     "application/json": {
# #                         "success": True,
# #                         "message": "All documents uploaded successfully",
# #                         "data": {
# #                             "uploaded_count": 4,
# #                             "documents": [],
# #                             "step_completed": True
# #                         }
# #                     }
# #                 }
# #             ),
# #             400: "Bad Request - Validation errors",
# #             404: "Company not found"
# #         }
# #     )
# #     def post(self, request, company_id):
# #         """Upload all documents at once - public endpoint for onboarding"""
# #         from ..models.CompanyInformationModel import CompanyInformation
# #         from ..models.CompanyDocumentModel import CompanyDocument
        
# #         try:
# #             company = CompanyInformation.objects.select_related('application').get(
# #                 company_id=company_id,
# #                 del_flag=0
# #             )
# #         except CompanyInformation.DoesNotExist:
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': 'Company not found'
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         existing_docs = CompanyDocument.objects.filter(
# #             company_id=company_id,
# #             del_flag=0
# #         ).count()
        
# #         if existing_docs > 0:
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': 'Documents already uploaded. Use update endpoint to modify.',
# #                     'existing_count': existing_docs
# #                 },
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )
        
# #         serializer = CompanyDocumentBulkUploadSerializer(
# #             data=request.data,
# #             context={
# #                 'company_id': company_id,
# #                 'request': request
# #             }
# #         )
        
# #         if serializer.is_valid():
# #             try:
# #                 with transaction.atomic():
# #                     documents = serializer.save()
                    
# #                     if hasattr(company, 'application') and company.application:
# #                         self.update_document_step(company)
# #             except Exception as e:
# #                 return Response(
# #                     {
# #                         'success': False,
# #                         'message': f'Failed to upload documents: {str(e)}'
# #                     },
# #                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
# #                 )
            
# #             documents_data = [
# #                 {
# #                     'document_id': str(doc.document_id),
# #                     'document_name': doc.document_name,
# #                     'document_name_display': doc.get_document_name_display(),
# #                     'document_type': doc.document_type,
# #                     'file_size': doc.file_size,
# #                     'uploaded_at': doc.uploaded_at.isoformat(),
# #                     'is_mandatory': doc.is_mandatory,
# #                 }
# #                 for doc in documents
# #             ]
            
# #             step_completed = CompanyDocument.check_company_documents_complete(company_id)
            
# #             return Response(
# #                 {
# #                     'success': True,
# #                     'message': 'All documents uploaded successfully',
# #                     'data': {
# #                         'uploaded_count': len(documents),
# #                         'documents': documents_data,
# #                         'step_completed': step_completed
# #                     }
# #                 },
# #                 status=status.HTTP_201_CREATED
# #             )
        
# #         return Response(
# #             DocumentResponseFormatter.format_error_response(
# #                 "Validation failed",
# #                 serializer.errors
# #             ),
# #             status=status.HTTP_400_BAD_REQUEST
# #         )


# # class CompanyDocumentListView(
# #     APIView,
# #     DocumentQueryOptimizationMixin
# # ):
# #     """
# #     List all documents for a company with upload status.
# #     Public endpoint - no authentication required.
# #     """
# #     permission_classes = []

# #     @swagger_auto_schema(
# #         operation_description="Get list of all documents for a company",
# #         manual_parameters=[
# #             openapi.Parameter(
# #                 'company_id',
# #                 openapi.IN_PATH,
# #                 description="Company ID (UUID)",
# #                 type=openapi.TYPE_STRING,
# #                 required=True
# #             )
# #         ],
# #         responses={
# #             200: CompanyDocumentListSerializer(many=True),
# #             404: "Company not found"
# #         }
# #     )
# #     def get(self, request, company_id):
# #         """Get all documents for company - public endpoint"""
# #         from ..models.CompanyInformationModel import CompanyInformation
        
# #         try:
# #             company = CompanyInformation.objects.get(
# #                 company_id=company_id,
# #                 del_flag=0
# #             )
# #         except CompanyInformation.DoesNotExist:
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': 'Company not found'
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         documents = self.get_optimized_documents_queryset(company_id)
# #         doc_status = DocumentStatusChecker.get_company_document_status(company_id)
# #         serializer = CompanyDocumentListSerializer(documents, many=True)
        
# #         return Response(
# #             DocumentResponseFormatter.format_list_response(
# #                 serializer.data,
# #                 doc_status
# #             ),
# #             status=status.HTTP_200_OK
# #         )


# # class CompanyDocumentDetailView(
# #     APIView,
# #     DocumentQueryOptimizationMixin,
# #     SoftDeleteMixin
# # ):
# #     """
# #     Retrieve, update or delete a specific document.
# #     Public endpoint - no authentication required during onboarding.
# #     """
# #     permission_classes = []
# #     parser_classes = [MultiPartParser, FormParser]

# #     @swagger_auto_schema(
# #         operation_description="Get document details with file data",
# #         manual_parameters=[
# #             openapi.Parameter(
# #                 'company_id',
# #                 openapi.IN_PATH,
# #                 description="Company ID (UUID)",
# #                 type=openapi.TYPE_STRING,
# #                 required=True
# #             ),
# #             openapi.Parameter(
# #                 'document_id',
# #                 openapi.IN_PATH,
# #                 description="Document ID (UUID)",
# #                 type=openapi.TYPE_STRING,
# #                 required=True
# #             )
# #         ],
# #         responses={
# #             200: CompanyDocumentDetailSerializer(),
# #             404: "Document or Company not found"
# #         }
# #     )
# #     def get(self, request, company_id, document_id):
# #         """Get document with file data - public endpoint"""
# #         from ..models.CompanyInformationModel import CompanyInformation
        
# #         try:
# #             CompanyInformation.objects.get(
# #                 company_id=company_id,
# #                 del_flag=0
# #             )
# #         except CompanyInformation.DoesNotExist:
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': 'Company not found'
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         try:
# #             document = self.get_document_with_company(document_id, company_id)
# #         except Exception as e:
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': 'Document not found'
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         serializer = CompanyDocumentDetailSerializer(document)
        
# #         return Response(
# #             {
# #                 'success': True,
# #                 'data': serializer.data
# #             },
# #             status=status.HTTP_200_OK
# #         )

# #     @swagger_auto_schema(
# #         operation_description="Update/Replace a specific document",
# #         manual_parameters=[
# #             openapi.Parameter(
# #                 'company_id',
# #                 openapi.IN_PATH,
# #                 description="Company ID (UUID)",
# #                 type=openapi.TYPE_STRING,
# #                 required=True
# #             ),
# #             openapi.Parameter(
# #                 'document_id',
# #                 openapi.IN_PATH,
# #                 description="Document ID (UUID)",
# #                 type=openapi.TYPE_STRING,
# #                 required=True
# #             ),
# #             openapi.Parameter(
# #                 'file',
# #                 openapi.IN_FORM,
# #                 description="New document file",
# #                 type=openapi.TYPE_FILE,
# #                 required=True
# #             )
# #         ],
# #         responses={
# #             200: openapi.Response(
# #                 description="Document updated successfully"
# #             ),
# #             400: "Validation failed",
# #             404: "Document or Company not found"
# #         }
# #     )
# #     def put(self, request, company_id, document_id):
# #         """Replace existing document using serializer.update() method"""
# #         from ..models.CompanyInformationModel import CompanyInformation
        
# #         try:
# #             CompanyInformation.objects.get(
# #                 company_id=company_id,
# #                 del_flag=0
# #             )
# #         except CompanyInformation.DoesNotExist:
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': 'Company not found'
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         try:
# #             document = self.get_document_with_company(document_id, company_id)
# #         except Exception as e:
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': 'Document not found'
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         update_data = {
# #             'document_name': document.document_name,
# #             'file': request.FILES.get('file')
# #         }
        
# #         if not update_data['file']:
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': 'No file provided'
# #                 },
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )
        
# #         serializer = CompanySingleDocumentUploadSerializer(
# #             instance=document,
# #             data=update_data,
# #             context={
# #                 'company_id': company_id,
# #                 'request': request
# #             }
# #         )
        
# #         if serializer.is_valid():
# #             try:
# #                 updated_document = serializer.save()
                
# #                 return Response(
# #                     DocumentResponseFormatter.format_success_response(
# #                         updated_document,
# #                         "Document updated successfully"
# #                     ),
# #                     status=status.HTTP_200_OK
# #                 )
# #             except Exception as e:
# #                 return Response(
# #                     {
# #                         'success': False,
# #                         'message': f'Failed to update document: {str(e)}'
# #                     },
# #                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
# #                 )
        
# #         return Response(
# #             DocumentResponseFormatter.format_error_response(
# #                 "Failed to update document",
# #                 serializer.errors
# #             ),
# #             status=status.HTTP_400_BAD_REQUEST
# #         )

# #     @swagger_auto_schema(
# #         operation_description="Soft delete a document and revalidate application step",
# #         manual_parameters=[
# #             openapi.Parameter(
# #                 'company_id',
# #                 openapi.IN_PATH,
# #                 description="Company ID (UUID)",
# #                 type=openapi.TYPE_STRING,
# #                 required=True
# #             ),
# #             openapi.Parameter(
# #                 'document_id',
# #                 openapi.IN_PATH,
# #                 description="Document ID (UUID)",
# #                 type=openapi.TYPE_STRING,
# #                 required=True
# #             )
# #         ],
# #         responses={
# #             200: openapi.Response(
# #                 description="Document deleted successfully",
# #                 examples={
# #                     "application/json": {
# #                         "success": True,
# #                         "message": "Document deleted successfully",
# #                         "step_invalidated": True
# #                     }
# #                 }
# #             ),
# #             404: "Document or Company not found"
# #         }
# #     )
# #     def delete(self, request, company_id, document_id):
# #         """Soft delete document and revalidate application completion"""
# #         from ..models.CompanyInformationModel import CompanyInformation
        
# #         try:
# #             CompanyInformation.objects.get(
# #                 company_id=company_id,
# #                 del_flag=0
# #             )
# #         except CompanyInformation.DoesNotExist:
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': 'Company not found'
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         try:
# #             document = self.get_document_with_company(document_id, company_id)
# #         except Exception as e:
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': 'Document not found'
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         serializer = CompanySingleDocumentUploadSerializer(
# #             context={
# #                 'company_id': company_id,
# #                 'request': request
# #             }
# #         )
        
# #         try:
# #             step_invalidated = serializer.soft_delete(document)
            
# #             return Response(
# #                 {
# #                     'success': True,
# #                     'message': 'Document deleted successfully',
# #                     'step_invalidated': step_invalidated
# #                 },
# #                 status=status.HTTP_200_OK
# #             )
# #         except Exception as e:
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': f'Failed to delete document: {str(e)}'
# #                 },
# #                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
# #             )


# # class CompanyDocumentStatusView(APIView):
# #     """
# #     Check document upload status for a company.
# #     Shows which mandatory documents are missing.
# #     Public endpoint - no authentication required.
# #     """
# #     permission_classes = []

# #     @swagger_auto_schema(
# #         operation_description="""
# #         Get document upload status for a company.
        
# #         Returns:
# #         - Total documents count
# #         - Mandatory documents count  
# #         - Uploaded mandatory documents count
# #         - List of missing mandatory documents
# #         - All mandatory uploaded status (boolean)
# #         """,
# #         manual_parameters=[
# #             openapi.Parameter(
# #                 'company_id',
# #                 openapi.IN_PATH,
# #                 description="Company ID (UUID)",
# #                 type=openapi.TYPE_STRING,
# #                 required=True
# #             )
# #         ],
# #         responses={
# #             200: CompanyDocumentStatusSerializer(),
# #             404: "Company not found"
# #         }
# #     )
# #     def get(self, request, company_id):
# #         """Get document upload status - public endpoint"""
# #         from ..models.CompanyInformationModel import CompanyInformation
        
# #         try:
# #             CompanyInformation.objects.get(
# #                 company_id=company_id,
# #                 del_flag=0
# #             )
# #         except CompanyInformation.DoesNotExist:
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': 'Company not found'
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         status_data = DocumentStatusChecker.get_company_document_status(company_id)
# #         serializer = CompanyDocumentStatusSerializer(status_data)
        
# #         return Response(
# #             {
# #                 'success': True,
# #                 'data': serializer.data
# #             },
# #             status=status.HTTP_200_OK
# #         )


# # class CompanySingleDocumentUploadView(
# #     APIView,
# #     ApplicationStepUpdateMixin
# # ):
# #     """
# #     Upload a single document (used for adding individual documents).
# #     Public endpoint - no authentication required during onboarding.
# #     """
# #     permission_classes = []
# #     parser_classes = [MultiPartParser, FormParser]

# #     @swagger_auto_schema(
# #         operation_description="""
# #         Upload a single document for a company.
        
# #         Required:
# #         - document_name: Choose from available document types
# #         - file: PDF, JPEG, JPG, or PNG (max 5MB)
# #         """,
# #         manual_parameters=[
# #             openapi.Parameter(
# #                 'company_id',
# #                 openapi.IN_PATH,
# #                 description="Company ID (UUID)",
# #                 type=openapi.TYPE_STRING,
# #                 required=True
# #             ),
# #             openapi.Parameter(
# #                 'document_name',
# #                 openapi.IN_FORM,
# #                 description="Document type",
# #                 type=openapi.TYPE_STRING,
# #                 required=True,
# #                 enum=['CERTIFICATE_INC', 'MOA', 'MSME', 'IEC']
# #             ),
# #             openapi.Parameter(
# #                 'file',
# #                 openapi.IN_FORM,
# #                 description="Document file",
# #                 type=openapi.TYPE_FILE,
# #                 required=True
# #             )
# #         ],
# #         responses={
# #             201: openapi.Response(
# #                 description="Document uploaded successfully",
# #                 examples={
# #                     "application/json": {
# #                         "success": True,
# #                         "message": "Document uploaded successfully",
# #                         "data": {
# #                             "document_id": "uuid",
# #                             "document_name": "MOA",
# #                             "step_completed": False
# #                         }
# #                     }
# #                 }
# #             ),
# #             400: "Validation failed",
# #             404: "Company not found",
# #             409: "Document already exists"
# #         }
# #     )
# #     def post(self, request, company_id):
# #         """Upload single document - public endpoint"""
# #         from ..models.CompanyInformationModel import CompanyInformation
# #         from ..models.CompanyDocumentModel import CompanyDocument
        
# #         try:
# #             company = CompanyInformation.objects.select_related('application').get(
# #                 company_id=company_id,
# #                 del_flag=0
# #             )
# #         except CompanyInformation.DoesNotExist:
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': 'Company not found'
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         document_name = request.data.get('document_name')
# #         if document_name:
# #             existing_doc = CompanyDocument.objects.filter(
# #                 company_id=company_id,
# #                 document_name=document_name,
# #                 del_flag=0
# #             ).exists()
            
# #             if existing_doc:
# #                 return Response(
# #                     {
# #                         'success': False,
# #                         'message': f'Document {document_name} already exists. Use update endpoint to modify.'
# #                     },
# #                     status=status.HTTP_409_CONFLICT
# #                 )
        
# #         serializer = CompanySingleDocumentUploadSerializer(
# #             data=request.data,
# #             context={
# #                 'company_id': company_id,
# #                 'request': request
# #             }
# #         )
        
# #         if serializer.is_valid():
# #             try:
# #                 with transaction.atomic():
# #                     document = serializer.save()
                    
# #                     if hasattr(company, 'application') and company.application:
# #                         self.update_document_step(company)
                
# #                 step_completed = CompanyDocument.check_company_documents_complete(company_id)
                
# #                 return Response(
# #                     {
# #                         'success': True,
# #                         'message': 'Document uploaded successfully',
# #                         'data': {
# #                             'document_id': str(document.document_id),
# #                             'document_name': document.document_name,
# #                             'document_name_display': document.get_document_name_display(),
# #                             'document_type': document.document_type,
# #                             'file_size': document.file_size,
# #                             'uploaded_at': document.uploaded_at.isoformat(),
# #                             'is_mandatory': document.is_mandatory,
# #                             'step_completed': step_completed
# #                         }
# #                     },
# #                     status=status.HTTP_201_CREATED
# #                 )
# #             except Exception as e:
# #                 return Response(
# #                     {
# #                         'success': False,
# #                         'message': f'Failed to upload document: {str(e)}'
# #                     },
# #                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
# #                 )
        
# #         return Response(
# #             DocumentResponseFormatter.format_error_response(
# #                 "Validation failed",
# #                 serializer.errors
# #             ),
# #             status=status.HTTP_400_BAD_REQUEST
# #         )


# # class CompanyDocumentVerificationView(APIView):
# #     """
# #     Admin endpoint to verify/reject uploaded documents.
# #     Requires authentication and admin permissions.
# #     """
# #     permission_classes = [IsAuthenticated]

# #     @swagger_auto_schema(
# #         operation_description="""
# #         Verify or reject a company document (Admin only).
        
# #         Request body:
# #         {
# #             "is_verified": true/false,
# #             "rejection_reason": "Optional reason if rejected"
# #         }
# #         """,
# #         manual_parameters=[
# #             openapi.Parameter(
# #                 'company_id',
# #                 openapi.IN_PATH,
# #                 description="Company ID (UUID)",
# #                 type=openapi.TYPE_STRING,
# #                 required=True
# #             ),
# #             openapi.Parameter(
# #                 'document_id',
# #                 openapi.IN_PATH,
# #                 description="Document ID (UUID)",
# #                 type=openapi.TYPE_STRING,
# #                 required=True
# #             )
# #         ],
# #         request_body=openapi.Schema(
# #             type=openapi.TYPE_OBJECT,
# #             required=['is_verified'],
# #             properties={
# #                 'is_verified': openapi.Schema(
# #                     type=openapi.TYPE_BOOLEAN,
# #                     description='Verification status'
# #                 ),
# #                 'rejection_reason': openapi.Schema(
# #                     type=openapi.TYPE_STRING,
# #                     description='Reason for rejection (if not verified)'
# #                 )
# #             }
# #         ),
# #         responses={
# #             200: openapi.Response(
# #                 description="Document verification updated",
# #                 examples={
# #                     "application/json": {
# #                         "success": True,
# #                         "message": "Document verified successfully",
# #                         "data": {
# #                             "document_id": "uuid",
# #                             "is_verified": True
# #                         }
# #                     }
# #                 }
# #             ),
# #             403: "Permission denied",
# #             404: "Document not found"
# #         }
# #     )
# #     def patch(self, request, company_id, document_id):
# #         """Update document verification status - admin only"""
# #         from ..models.CompanyDocumentModel import CompanyDocument
# #         from ..models.CompanyInformationModel import CompanyInformation
        
# #         if not request.user.is_staff:
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': 'Permission denied. Admin access required.'
# #                 },
# #                 status=status.HTTP_403_FORBIDDEN
# #             )
        
# #         try:
# #             CompanyInformation.objects.get(
# #                 company_id=company_id,
# #                 del_flag=0
# #             )
# #         except CompanyInformation.DoesNotExist:
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': 'Company not found'
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         try:
# #             document = CompanyDocument.objects.get(
# #                 document_id=document_id,
# #                 company_id=company_id,
# #                 del_flag=0
# #             )
# #         except CompanyDocument.DoesNotExist:
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': 'Document not found'
# #                 },
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         is_verified = request.data.get('is_verified')
# #         if is_verified is None:
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': 'is_verified field is required'
# #                 },
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )
        
# #         document.is_verified = is_verified
# #         document.user_id_updated_by = request.user
# #         document.save(update_fields=['is_verified', 'user_id_updated_by', 'updated_at'])
        
# #         message = "Document verified successfully" if is_verified else "Document rejected"
        
# #         return Response(
# #             {
# #                 'success': True,
# #                 'message': message,
# #                 'data': {
# #                     'document_id': str(document.document_id),
# #                     'document_name': document.document_name,
# #                     'is_verified': document.is_verified,
# #                     'verified_by': str(request.user.user_id),
# #                     'verified_at': document.updated_at.isoformat()
# #                 }
# #             },
# #             status=status.HTTP_200_OK
# #         )

# # from rest_framework import status
# # from rest_framework.views import APIView
# # from rest_framework.response import Response
# # from rest_framework.permissions import IsAuthenticated
# # from rest_framework.parsers import MultiPartParser, FormParser
# # from django.db import transaction
# # from drf_yasg.utils import swagger_auto_schema
# # from drf_yasg import openapi
# # import logging

# # from ..serializers.CompanyDocumentSerializer import (
# #     CompanyDocumentBulkUploadSerializer,
# #     CompanyDocumentListSerializer,
# #     CompanyDocumentDetailSerializer,
# #     CompanyDocumentStatusSerializer,
# #     CompanySingleDocumentUploadSerializer
# # )
# # from ..mixins.DocumentMixins import (
# #     CompanyOwnershipMixin,
# #     DocumentQueryOptimizationMixin,
# #     ApplicationStepUpdateMixin,
# #     SoftDeleteMixin
# # )
# # from ..utils.DocumentUtils import (
# #     DocumentStatusChecker,
# #     DocumentResponseFormatter
# # )
# # from django.utils import timezone


# # logger = logging.getLogger(__name__)


# # class CompanyDocumentBulkUploadView(APIView):
# #     """
# #     Bulk upload company documents at once.
# #     Only Certificate of Incorporation is MANDATORY.
# #     Optimized for clean response and no UUID serialization errors.
# #     """
# #     permission_classes = []
# #     parser_classes = [MultiPartParser, FormParser]

# #     # ---------------------------------------------------------
# #     # ✅ MANUAL STEP UPDATE (NO update_state())
# #     # ---------------------------------------------------------
# #     def update_step_three(self, company, documents):
# #         """
# #         Safely update onboarding step 3 (Documents)
# #         without using update_state() to avoid UUID serialization.
# #         """
# #         application = getattr(company, "application", None)
# #         if not application:
# #             return

# #         step_key = "3"

# #         # ✅ Step completed only if mandatory document uploaded
# #         mandatory_uploaded = any(doc.is_mandatory for doc in documents)

# #         step_state = {
# #             "completed": mandatory_uploaded,
# #             "completed_at": timezone.now().isoformat(),
# #             "record_id": [str(doc.document_id) for doc in documents],
# #         }

# #         application.step_completion[step_key] = step_state

# #         # ✅ Update status
# #         if application.status == "INITIATED":
# #             application.status = "IN_PROGRESS"

# #         application.save(update_fields=["step_completion", "status", "updated_at"])

# #     # ---------------------------------------------------------
# #     # ✅ MAIN POST METHOD
# #     # ---------------------------------------------------------
# #     @swagger_auto_schema(
# #         operation_description="Bulk upload company documents.",
# #         manual_parameters=[
# #             openapi.Parameter('company_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True),
# #             openapi.Parameter('certificate_of_incorporation', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
# #             openapi.Parameter('moa_aoa_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
# #             openapi.Parameter('moa_aoa_file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
# #             openapi.Parameter('msme_udyam_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
# #             openapi.Parameter('msme_udyam_file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
# #             openapi.Parameter('import_export_certificate', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
# #         ],
# #         responses={201: "Success", 400: "Validation error", 404: "Company not found"}
# #     )
# #     def post(self, request, company_id):
# #         from ..models.CompanyInformationModel import CompanyInformation
# #         from ..models.CompanyDocumentModel import CompanyDocument
# #         from ..serializers.CompanyDocumentSerializer import CompanyDocumentBulkUploadSerializer

# #         logger.info(
# #             f"[BULK_UPLOAD] Request for company_id={company_id}, files={list(request.FILES.keys())}"
# #         )

# #         # ✅ Validate company
# #         try:
# #             company = CompanyInformation.objects.select_related("application").get(
# #                 company_id=company_id,
# #                 del_flag=0,
# #             )
# #         except CompanyInformation.DoesNotExist:
# #             return Response(
# #                 {"success": False, "message": "Company not found"},
# #                 status=status.HTTP_404_NOT_FOUND,
# #             )

# #         serializer = CompanyDocumentBulkUploadSerializer(
# #             data=request.data,
# #             context={"company_id": company_id, "request": request},
# #         )

# #         if serializer.is_valid():
# #             try:
# #                 with transaction.atomic():
# #                     documents = serializer.save()

# #                     # ✅ Safe step update (manual)
# #                     self.update_step_three(company, documents)

# #             except Exception as e:
# #                 logger.error(f"[BULK_UPLOAD] Error: {str(e)}", exc_info=True)
# #                 return Response(
# #                     {"success": False, "message": f"Failed to upload: {str(e)}"},
# #                     status=status.HTTP_500_INTERNAL_SERVER_ERROR,
# #                 )

# #             # ✅ Minimal response
# #             documents_data = [
# #                 {
# #                     "id": str(doc.document_id),
# #                     "name": doc.document_name,
# #                     "display_name": doc.get_document_name_display(),
# #                     "type": doc.document_type,
# #                     "mandatory": doc.is_mandatory,
# #                     "uploaded_at": doc.uploaded_at.isoformat(),
# #                 }
# #                 for doc in documents
# #             ]

# #             step_completed = CompanyDocument.check_company_documents_complete(company_id)

# #             response_data = {
# #                 "success": True,
# #                 "message": "Documents uploaded successfully",
# #                 "data": {
# #                     "documents": documents_data,
# #                     "summary": {
# #                         "uploaded_count": len(documents),
# #                         "mandatory_uploaded": any(d.is_mandatory for d in documents),
# #                         "step_completed": step_completed,
# #                     },
# #                 },
# #             }

# #             return Response(response_data, status=status.HTTP_201_CREATED)

# #         # ❌ Validation failed
# #         return Response(
# #             {
# #                 "success": False,
# #                 "message": "Validation failed",
# #                 "errors": serializer.errors,
# #             },
# #             status=status.HTTP_400_BAD_REQUEST,
# #         )
# # class CompanyDocumentListView(APIView, DocumentQueryOptimizationMixin):
# #     """
# #     List all documents for a company with upload status.
# #     Public endpoint - no authentication required.
# #     """
# #     permission_classes = []

# #     @swagger_auto_schema(
# #         operation_description="Get list of all documents for a company",
# #         manual_parameters=[
# #             openapi.Parameter(
# #                 'company_id', openapi.IN_PATH,
# #                 description="Company ID (UUID)",
# #                 type=openapi.TYPE_STRING, required=True
# #             )
# #         ],
# #         responses={
# #             200: CompanyDocumentListSerializer(many=True),
# #             404: "Company not found"
# #         }
# #     )
# #     def get(self, request, company_id):
# #         """Get all documents for company - public endpoint"""
# #         logger.info(f"[LIST_DOCS] Request for company_id={company_id}")
        
# #         from ..models.CompanyInformationModel import CompanyInformation
        
# #         try:
# #             company = CompanyInformation.objects.get(
# #                 company_id=company_id,
# #                 del_flag=0
# #             )
# #             logger.debug(f"[LIST_DOCS] Company found: {company.company_name}")
# #         except CompanyInformation.DoesNotExist:
# #             logger.error(f"[LIST_DOCS] Company not found: company_id={company_id}")
# #             return Response(
# #                 {'success': False, 'message': 'Company not found'},
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         try:
# #             documents = self.get_optimized_documents_queryset(company_id)
# #             doc_status = DocumentStatusChecker.get_company_document_status(company_id)
# #             serializer = CompanyDocumentListSerializer(documents, many=True)
            
# #             logger.info(
# #                 f"[LIST_DOCS] Success for company_id={company_id}: "
# #                 f"{len(documents)} documents found"
# #             )
            
# #             return Response(
# #                 DocumentResponseFormatter.format_list_response(
# #                     serializer.data,
# #                     doc_status
# #                 ),
# #                 status=status.HTTP_200_OK
# #             )
# #         except Exception as e:
# #             logger.error(
# #                 f"[LIST_DOCS] Failed for company_id={company_id}: {str(e)}",
# #                 exc_info=True
# #             )
# #             return Response(
# #                 {'success': False, 'message': f'Failed to retrieve documents: {str(e)}'},
# #                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
# #             )


# # class CompanyDocumentDetailView(APIView, DocumentQueryOptimizationMixin, SoftDeleteMixin):
# #     """
# #     Retrieve, update or delete a specific document.
# #     Public endpoint - no authentication required during onboarding.
# #     """
# #     permission_classes = []
# #     parser_classes = [MultiPartParser, FormParser]

# #     @swagger_auto_schema(
# #         operation_description="Get document details with file data",
# #         manual_parameters=[
# #             openapi.Parameter(
# #                 'company_id', openapi.IN_PATH,
# #                 description="Company ID (UUID)",
# #                 type=openapi.TYPE_STRING, required=True
# #             ),
# #             openapi.Parameter(
# #                 'document_id', openapi.IN_PATH,
# #                 description="Document ID (UUID)",
# #                 type=openapi.TYPE_STRING, required=True
# #             )
# #         ],
# #         responses={
# #             200: CompanyDocumentDetailSerializer(),
# #             404: "Document or Company not found"
# #         }
# #     )
# #     def get(self, request, company_id, document_id):
# #         """Get document with file data - public endpoint"""
# #         logger.info(
# #             f"[GET_DOC] Request for company_id={company_id}, document_id={document_id}"
# #         )
        
# #         from ..models.CompanyInformationModel import CompanyInformation
        
# #         try:
# #             CompanyInformation.objects.get(company_id=company_id, del_flag=0)
# #             logger.debug(f"[GET_DOC] Company verified: company_id={company_id}")
# #         except CompanyInformation.DoesNotExist:
# #             logger.error(f"[GET_DOC] Company not found: company_id={company_id}")
# #             return Response(
# #                 {'success': False, 'message': 'Company not found'},
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         try:
# #             document = self.get_document_with_company(document_id, company_id)
# #             serializer = CompanyDocumentDetailSerializer(document)
            
# #             logger.info(
# #                 f"[GET_DOC] Success: document_id={document_id}, "
# #                 f"document_name={document.document_name}"
# #             )
            
# #             return Response(
# #                 {'success': True, 'data': serializer.data},
# #                 status=status.HTTP_200_OK
# #             )
# #         except Exception as e:
# #             logger.error(
# #                 f"[GET_DOC] Document not found: document_id={document_id}, "
# #                 f"company_id={company_id}, error={str(e)}",
# #                 exc_info=True
# #             )
# #             return Response(
# #                 {'success': False, 'message': 'Document not found'},
# #                 status=status.HTTP_404_NOT_FOUND
# #             )

# #     @swagger_auto_schema(
# #         operation_description="Update/Replace a specific document",
# #         manual_parameters=[
# #             openapi.Parameter(
# #                 'company_id', openapi.IN_PATH,
# #                 description="Company ID (UUID)",
# #                 type=openapi.TYPE_STRING, required=True
# #             ),
# #             openapi.Parameter(
# #                 'document_id', openapi.IN_PATH,
# #                 description="Document ID (UUID)",
# #                 type=openapi.TYPE_STRING, required=True
# #             ),
# #             openapi.Parameter(
# #                 'file', openapi.IN_FORM,
# #                 description="New document file",
# #                 type=openapi.TYPE_FILE, required=True
# #             )
# #         ],
# #         responses={
# #             200: openapi.Response(description="Document updated successfully"),
# #             400: "Validation failed",
# #             404: "Document or Company not found"
# #         }
# #     )
# #     def put(self, request, company_id, document_id):
# #         """Replace existing document using serializer.update() method"""
# #         logger.info(
# #             f"[UPDATE_DOC] Request for company_id={company_id}, document_id={document_id}"
# #         )
        
# #         from ..models.CompanyInformationModel import CompanyInformation
        
# #         try:
# #             CompanyInformation.objects.get(company_id=company_id, del_flag=0)
# #             logger.debug(f"[UPDATE_DOC] Company verified: company_id={company_id}")
# #         except CompanyInformation.DoesNotExist:
# #             logger.error(f"[UPDATE_DOC] Company not found: company_id={company_id}")
# #             return Response(
# #                 {'success': False, 'message': 'Company not found'},
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         try:
# #             document = self.get_document_with_company(document_id, company_id)
# #             logger.debug(
# #                 f"[UPDATE_DOC] Document found: {document.document_name}, "
# #                 f"is_mandatory={document.is_mandatory}"
# #             )
# #         except Exception as e:
# #             logger.error(
# #                 f"[UPDATE_DOC] Document not found: document_id={document_id}, "
# #                 f"error={str(e)}"
# #             )
# #             return Response(
# #                 {'success': False, 'message': 'Document not found'},
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         update_data = {
# #             'document_name': document.document_name,
# #             'file': request.FILES.get('file')
# #         }
        
# #         if not update_data['file']:
# #             logger.warning(f"[UPDATE_DOC] No file provided for document_id={document_id}")
# #             return Response(
# #                 {'success': False, 'message': 'No file provided'},
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )
        
# #         serializer = CompanySingleDocumentUploadSerializer(
# #             instance=document,
# #             data=update_data,
# #             context={'company_id': company_id, 'request': request}
# #         )
        
# #         if serializer.is_valid():
# #             try:
# #                 updated_document = serializer.save()
                
# #                 logger.info(
# #                     f"[UPDATE_DOC] Success: document_id={document_id}, "
# #                     f"new_size={updated_document.file_size}"
# #                 )
                
# #                 return Response(
# #                     DocumentResponseFormatter.format_success_response(
# #                         updated_document,
# #                         "Document updated successfully"
# #                     ),
# #                     status=status.HTTP_200_OK
# #                 )
# #             except Exception as e:
# #                 logger.error(
# #                     f"[UPDATE_DOC] Update failed for document_id={document_id}: {str(e)}",
# #                     exc_info=True
# #                 )
# #                 return Response(
# #                     {
# #                         'success': False,
# #                         'message': f'Failed to update document: {str(e)}'
# #                     },
# #                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
# #                 )
        
# #         logger.error(
# #             f"[UPDATE_DOC] Validation failed for document_id={document_id}: "
# #             f"{serializer.errors}"
# #         )
# #         return Response(
# #             DocumentResponseFormatter.format_error_response(
# #                 "Failed to update document",
# #                 serializer.errors
# #             ),
# #             status=status.HTTP_400_BAD_REQUEST
# #         )

# #     @swagger_auto_schema(
# #         operation_description="Soft delete a document and revalidate application step",
# #         manual_parameters=[
# #             openapi.Parameter(
# #                 'company_id', openapi.IN_PATH,
# #                 description="Company ID (UUID)",
# #                 type=openapi.TYPE_STRING, required=True
# #             ),
# #             openapi.Parameter(
# #                 'document_id', openapi.IN_PATH,
# #                 description="Document ID (UUID)",
# #                 type=openapi.TYPE_STRING, required=True
# #             )
# #         ],
# #         responses={
# #             200: openapi.Response(
# #                 description="Document deleted successfully",
# #                 examples={
# #                     "application/json": {
# #                         "success": True,
# #                         "message": "Document deleted successfully",
# #                         "step_invalidated": True
# #                     }
# #                 }
# #             ),
# #             404: "Document or Company not found"
# #         }
# #     )
# #     def delete(self, request, company_id, document_id):
# #         """Soft delete document and revalidate application completion"""
# #         logger.info(
# #             f"[DELETE_DOC] Request for company_id={company_id}, document_id={document_id}"
# #         )
        
# #         from ..models.CompanyInformationModel import CompanyInformation
        
# #         try:
# #             CompanyInformation.objects.get(company_id=company_id, del_flag=0)
# #             logger.debug(f"[DELETE_DOC] Company verified: company_id={company_id}")
# #         except CompanyInformation.DoesNotExist:
# #             logger.error(f"[DELETE_DOC] Company not found: company_id={company_id}")
# #             return Response(
# #                 {'success': False, 'message': 'Company not found'},
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         try:
# #             document = self.get_document_with_company(document_id, company_id)
# #             logger.debug(
# #                 f"[DELETE_DOC] Document found: {document.document_name}, "
# #                 f"is_mandatory={document.is_mandatory}"
# #             )
# #         except Exception as e:
# #             logger.error(
# #                 f"[DELETE_DOC] Document not found: document_id={document_id}, "
# #                 f"error={str(e)}"
# #             )
# #             return Response(
# #                 {'success': False, 'message': 'Document not found'},
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         serializer = CompanySingleDocumentUploadSerializer(
# #             context={'company_id': company_id, 'request': request}
# #         )
        
# #         try:
# #             step_invalidated = serializer.soft_delete(document)
            
# #             logger.info(
# #                 f"[DELETE_DOC] Success: document_id={document_id}, "
# #                 f"step_invalidated={step_invalidated}"
# #             )
            
# #             return Response(
# #                 {
# #                     'success': True,
# #                     'message': 'Document deleted successfully',
# #                     'step_invalidated': step_invalidated
# #                 },
# #                 status=status.HTTP_200_OK
# #             )
# #         except Exception as e:
# #             logger.error(
# #                 f"[DELETE_DOC] Delete failed for document_id={document_id}: {str(e)}",
# #                 exc_info=True
# #             )
# #             return Response(
# #                 {'success': False, 'message': f'Failed to delete document: {str(e)}'},
# #                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
# #             )


# # class CompanyDocumentStatusView(APIView):
# #     """
# #     Check document upload status for a company.
# #     Shows which mandatory documents are missing.
# #     Public endpoint - no authentication required.
# #     """
# #     permission_classes = []

# #     @swagger_auto_schema(
# #         operation_description="""
# #         Get document upload status for a company.
        
# #         Returns:
# #         - Total documents count
# #         - Mandatory documents count  
# #         - Optional documents count
# #         - Uploaded mandatory/optional counts
# #         - List of missing mandatory documents
# #         - All mandatory uploaded status (boolean)
# #         """,
# #         manual_parameters=[
# #             openapi.Parameter(
# #                 'company_id', openapi.IN_PATH,
# #                 description="Company ID (UUID)",
# #                 type=openapi.TYPE_STRING, required=True
# #             )
# #         ],
# #         responses={
# #             200: CompanyDocumentStatusSerializer(),
# #             404: "Company not found"
# #         }
# #     )
# #     def get(self, request, company_id):
# #         """Get document upload status - public endpoint"""
# #         logger.info(f"[DOC_STATUS] Request for company_id={company_id}")
        
# #         from ..models.CompanyInformationModel import CompanyInformation
        
# #         try:
# #             CompanyInformation.objects.get(company_id=company_id, del_flag=0)
# #             logger.debug(f"[DOC_STATUS] Company verified: company_id={company_id}")
# #         except CompanyInformation.DoesNotExist:
# #             logger.error(f"[DOC_STATUS] Company not found: company_id={company_id}")
# #             return Response(
# #                 {'success': False, 'message': 'Company not found'},
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         try:
# #             status_data = DocumentStatusChecker.get_company_document_status(company_id)
# #             serializer = CompanyDocumentStatusSerializer(status_data)
            
# #             logger.info(
# #                 f"[DOC_STATUS] Success for company_id={company_id}: "
# #                 f"mandatory={status_data.get('uploaded_mandatory')}/{status_data.get('mandatory_documents')}, "
# #                 f"optional={status_data.get('uploaded_optional')}/{status_data.get('optional_documents')}"
# #             )
            
# #             return Response(
# #                 {'success': True, 'data': serializer.data},
# #                 status=status.HTTP_200_OK
# #             )
# #         except Exception as e:
# #             logger.error(
# #                 f"[DOC_STATUS] Failed for company_id={company_id}: {str(e)}",
# #                 exc_info=True
# #             )
# #             return Response(
# #                 {'success': False, 'message': f'Failed to retrieve status: {str(e)}'},
# #                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
# #             )


# # class CompanySingleDocumentUploadView(APIView, ApplicationStepUpdateMixin):
# #     """
# #     Upload a single document BEFORE login.
# #     Public endpoint.
# #     """
# #     permission_classes = []
# #     parser_classes = [MultiPartParser, FormParser]

# #     def post(self, request, company_id):
# #         from ..models.CompanyDocumentModel import CompanyDocument
# #         from ..models.CompanyInformationModel import CompanyInformation

# #         # ✅ SAFE user id for logs
# #         safe_user_id = getattr(request.user, "user_id", "anonymous")

# #         logger.info(
# #             f"[SINGLE_UPLOAD] Start | company={company_id}, "
# #             f"user={safe_user_id}, data={dict(request.data)}"
# #         )

# #         # ✅ Validate company
# #         try:
# #             company = CompanyInformation.objects.get(company_id=company_id, del_flag=0)
# #         except CompanyInformation.DoesNotExist:
# #             return Response(
# #                 {"success": False, "message": "Company not found"},
# #                 status=404
# #             )

# #         document_name = request.data.get("document_name")

# #         # ✅ Check duplicates
# #         if document_name:
# #             exists = CompanyDocument.objects.filter(
# #                 company_id=company_id,
# #                 document_name=document_name,
# #                 del_flag=0
# #             ).exists()

# #             if exists:
# #                 return Response(
# #                     {
# #                         "success": False,
# #                         "message": f"Document '{document_name}' already exists. Delete it before uploading new one."
# #                     },
# #                     status=409
# #                 )

# #         # ✅ Validate serializer
# #         serializer = CompanySingleDocumentUploadSerializer(
# #             data=request.data,
# #             context={"company_id": company_id, "request": request}
# #         )

# #         if not serializer.is_valid():
# #             return Response(
# #                 {"success": False, "message": "Validation failed", "errors": serializer.errors},
# #                 status=400
# #             )

# #         # ✅ Save document
# #         try:
# #             with transaction.atomic():
# #                 document = serializer.save()

# #                 # ✅ Update onboarding step
# #                 if hasattr(company, "application") and company.application:
# #                     self.update_document_step(company)

# #         except Exception as e:
# #             logger.error(f"[SINGLE_UPLOAD] Failed: {e}", exc_info=True)
# #             return Response(
# #                 {"success": False, "message": f"Failed to upload document: {str(e)}"},
# #                 status=500
# #             )

# #         step_completed = CompanyDocument.check_company_documents_complete(company_id)

# #         return Response(
# #             {
# #                 "success": True,
# #                 "message": "Document uploaded successfully",
# #                 "data": {
# #                     "document_id": str(document.document_id),
# #                     "document_name": document.document_name,
# #                     "document_name_display": document.get_document_name_display(),
# #                     "document_type": document.document_type,
# #                     "file_size": document.file_size,
# #                     "uploaded_at": document.uploaded_at.isoformat(),
# #                     "is_mandatory": document.is_mandatory,
# #                     "step_completed": step_completed
# #                 }
# #             },
# #             status=201
# #         )

# # class CompanyDocumentVerificationView(APIView):
# #     """
# #     Admin endpoint to verify/reject uploaded documents.
# #     Requires authentication and admin permissions.
# #     """
# #     permission_classes = [IsAuthenticated]

# #     @swagger_auto_schema(
# #         operation_description="""
# #         Verify or reject a company document (Admin only).
        
# #         Request body:
# #         {
# #             "is_verified": true/false,
# #             "rejection_reason": "Optional reason if rejected"
# #         }
# #         """,
# #         manual_parameters=[
# #             openapi.Parameter(
# #                 'company_id', openapi.IN_PATH,
# #                 description="Company ID (UUID)",
# #                 type=openapi.TYPE_STRING, required=True
# #             ),
# #             openapi.Parameter(
# #                 'document_id', openapi.IN_PATH,
# #                 description="Document ID (UUID)",
# #                 type=openapi.TYPE_STRING, required=True
# #             )
# #         ],
# #         request_body=openapi.Schema(
# #             type=openapi.TYPE_OBJECT,
# #             required=['is_verified'],
# #             properties={
# #                 'is_verified': openapi.Schema(
# #                     type=openapi.TYPE_BOOLEAN,
# #                     description='Verification status'
# #                 ),
# #                 'rejection_reason': openapi.Schema(
# #                     type=openapi.TYPE_STRING,
# #                     description='Reason for rejection (if not verified)'
# #                 )
# #             }
# #         ),
# #         responses={
# #             200: openapi.Response(
# #                 description="Document verification updated",
# #                 examples={
# #                     "application/json": {
# #                         "success": True,
# #                         "message": "Document verified successfully",
# #                         "data": {
# #                             "document_id": "uuid",
# #                             "is_verified": True
# #                         }
# #                     }
# #                 }
# #             ),
# #             403: "Permission denied",
# #             404: "Document not found"
# #         }
# #     )
# #     def patch(self, request, company_id, document_id):
# #         """Update document verification status - admin only"""
# #         logger.info(
# #             f"[VERIFY_DOC] Request from user={request.user.user_id}, "
# #             f"company_id={company_id}, document_id={document_id}"
# #         )
        
# #         from ..models.CompanyDocumentModel import CompanyDocument
# #         from ..models.CompanyInformationModel import CompanyInformation
        
# #         if not request.user.is_staff:
# #             logger.warning(
# #                 f"[VERIFY_DOC] Permission denied for user={request.user.user_id}"
# #             )
# #             return Response(
# #                 {
# #                     'success': False,
# #                     'message': 'Permission denied. Admin access required.'
# #                 },
# #                 status=status.HTTP_403_FORBIDDEN
# #             )
        
# #         try:
# #             CompanyInformation.objects.get(company_id=company_id, del_flag=0)
# #             logger.debug(f"[VERIFY_DOC] Company verified: company_id={company_id}")
# #         except CompanyInformation.DoesNotExist:
# #             logger.error(f"[VERIFY_DOC] Company not found: company_id={company_id}")
# #             return Response(
# #                 {'success': False, 'message': 'Company not found'},
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         try:
# #             document = CompanyDocument.objects.get(
# #                 document_id=document_id,
# #                 company_id=company_id,
# #                 del_flag=0
# #             )
# #             logger.debug(
# #                 f"[VERIFY_DOC] Document found: {document.document_name}, "
# #                 f"current_verification={document.is_verified}"
# #             )
# #         except CompanyDocument.DoesNotExist:
# #             logger.error(
# #                 f"[VERIFY_DOC] Document not found: document_id={document_id}"
# #             )
# #             return Response(
# #                 {'success': False, 'message': 'Document not found'},
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         is_verified = request.data.get('is_verified')
# #         if is_verified is None:
# #             logger.warning("[VERIFY_DOC] Missing is_verified field in request")
# #             return Response(
# #                 {'success': False, 'message': 'is_verified field is required'},
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )
        
# #         try:
# #             document.is_verified = is_verified
# #             document.user_id_updated_by = request.user
# #             document.save(update_fields=['is_verified', 'user_id_updated_by', 'updated_at'])
            
# #             message = "Document verified successfully" if is_verified else "Document rejected"
            
# #             logger.info(
# #                 f"[VERIFY_DOC] Success: document_id={document_id}, "
# #                 f"is_verified={is_verified}, verified_by={request.user.user_id}"
# #             )
            
# #             return Response(
# #                 {
# #                     'success': True,
# #                     'message': message,
# #                     'data': {
# #                         'document_id': str(document.document_id),
# #                         'document_name': document.document_name,
# #                         'is_verified': document.is_verified,
# #                         'verified_by': str(request.user.user_id),
# #                         'verified_at': document.updated_at.isoformat()
# #                     }
# #                 },
# #                 status=status.HTTP_200_OK
# #             )
# #         except Exception as e:
# #             logger.error(
# #                 f"[VERIFY_DOC] Verification failed for document_id={document_id}: "
# #                 f"{str(e)}",
# #                 exc_info=True
# #             )
# #             return Response(
# #                 {'success': False, 'message': f'Failed to verify document: {str(e)}'},
# #                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             # )

# from rest_framework import status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.parsers import MultiPartParser, FormParser
# from django.db import transaction
# from drf_yasg.utils import swagger_auto_schema
# from drf_yasg import openapi
# import logging

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
# from django.utils import timezone


# logger = logging.getLogger(__name__)


# # ============================================================================
# # RESPONSE FORMATTER UTILITY
# # ============================================================================
# class StandardResponse:
#     """Standardized API response format"""
    
#     @staticmethod
#     def success(data=None, message="Success", status_code=status.HTTP_200_OK):
#         """Standard success response"""
#         response = {
#             "success": True,
#             "message": message
#         }
#         if data is not None:
#             response["data"] = data
#         return Response(response, status=status_code)
    
#     @staticmethod
#     def error(message="Error occurred", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
#         """Standard error response"""
#         response = {
#             "success": False,
#             "message": message
#         }
#         if errors:
#             response["errors"] = errors
#         return Response(response, status=status_code)
    
#     @staticmethod
#     def created(data=None, message="Created successfully"):
#         """Standard creation response"""
#         return StandardResponse.success(data, message, status.HTTP_201_CREATED)
    
#     @staticmethod
#     def not_found(message="Resource not found"):
#         """Standard 404 response"""
#         return StandardResponse.error(message, status_code=status.HTTP_404_NOT_FOUND)


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

#         # Validate company
#         try:
#             company = CompanyInformation.objects.select_related("application").get(
#                 company_id=company_id, del_flag=0
#             )
#         except CompanyInformation.DoesNotExist:
#             return StandardResponse.not_found("Company not found")

#         # Validate data
#         serializer = CompanyDocumentBulkUploadSerializer(
#             data=request.data,
#             context={"company_id": company_id, "request": request}
#         )

#         if not serializer.is_valid():
#             return StandardResponse.error(
#                 message="Validation failed",
#                 errors=serializer.errors
#             )

#         # Save documents
#         try:
#             with transaction.atomic():
#                 documents = serializer.save()
#                 self.update_step_three(company, documents)

#         except Exception as e:
#             logger.error(f"[BULK_UPLOAD] Error: {str(e)}", exc_info=True)
#             return StandardResponse.error(
#                 message="Failed to upload documents",
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#         # Format response
#         step_completed = CompanyDocument.check_company_documents_complete(company_id)
        
#         return StandardResponse.created(
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
#             message="Documents uploaded successfully"
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
#             return StandardResponse.not_found("Company not found")

#         try:
#             documents = self.get_optimized_documents_queryset(company_id)
#             doc_status = DocumentStatusChecker.get_company_document_status(company_id)
#             serializer = CompanyDocumentListSerializer(documents, many=True)

#             return StandardResponse.success(
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
#             return StandardResponse.error(
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

#         # Validate company
#         try:
#             CompanyInformation.objects.get(company_id=company_id, del_flag=0)
#         except CompanyInformation.DoesNotExist:
#             return StandardResponse.not_found("Company not found")

#         # Get document
#         try:
#             document = self.get_document_with_company(document_id, company_id)
#             serializer = CompanyDocumentDetailSerializer(document, context={'request': request})

#             return StandardResponse.success(
#                 data=serializer.data,
#                 message="Document retrieved successfully"
#             )

#         except Exception as e:
#             logger.error(f"[GET_DOC] Error: {str(e)}", exc_info=True)
#             return StandardResponse.not_found("Document not found")

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

#         # Validate company
#         try:
#             CompanyInformation.objects.get(company_id=company_id, del_flag=0)
#         except CompanyInformation.DoesNotExist:
#             return StandardResponse.not_found("Company not found")

#         # Get document
#         try:
#             document = self.get_document_with_company(document_id, company_id)
#         except Exception:
#             return StandardResponse.not_found("Document not found")

#         # Validate file
#         if not request.FILES.get('file'):
#             return StandardResponse.error("File is required")

#         # Update document
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
#             return StandardResponse.error(
#                 message="Validation failed",
#                 errors=serializer.errors
#             )

#         try:
#             updated_document = serializer.save()

#             return StandardResponse.success(
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
#             return StandardResponse.error(
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

#         # Validate company
#         try:
#             CompanyInformation.objects.get(company_id=company_id, del_flag=0)
#         except CompanyInformation.DoesNotExist:
#             return StandardResponse.not_found("Company not found")

#         # Get document
#         try:
#             document = self.get_document_with_company(document_id, company_id)
#         except Exception:
#             return StandardResponse.not_found("Document not found")

#         # Delete document
#         serializer = CompanySingleDocumentUploadSerializer(
#             context={'company_id': company_id, 'request': request}
#         )

#         try:
#             serializer.soft_delete(document)

#             return StandardResponse.success(
#                 data={
#                     "id": str(document.document_id),
#                     "name": document.get_document_name_display()
#                 },
#                 message="Document deleted successfully"
#             )

#         except Exception as e:
#             logger.error(f"[DELETE_DOC] Error: {str(e)}", exc_info=True)
#             return StandardResponse.error(
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

#         # Validate company
#         try:
#             CompanyInformation.objects.get(company_id=company_id, del_flag=0)
#         except CompanyInformation.DoesNotExist:
#             return StandardResponse.not_found("Company not found")

#         try:
#             # Get all documents with verification status
#             documents = CompanyDocument.objects.filter(
#                 company_id=company_id,
#                 del_flag=0
#             ).values('document_id', 'document_name', 'is_mandatory', 'is_verified', 'uploaded_at')

#             # Calculate verification statistics
#             total_docs = len(documents)
#             verified_docs = sum(1 for doc in documents if doc['is_verified'])
#             pending_docs = total_docs - verified_docs
            
#             mandatory_docs = [doc for doc in documents if doc['is_mandatory']]
#             mandatory_verified = sum(1 for doc in mandatory_docs if doc['is_verified'])
            
#             optional_docs = [doc for doc in documents if not doc['is_mandatory']]
#             optional_verified = sum(1 for doc in optional_docs if doc['is_verified'])

#             # Format document list with verification status
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

#             return StandardResponse.success(
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
#             return StandardResponse.error(
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

#         # Validate company
#         try:
#             company = CompanyInformation.objects.get(company_id=company_id, del_flag=0)
#         except CompanyInformation.DoesNotExist:
#             return StandardResponse.not_found("Company not found")

#         # Check for duplicate
#         document_name = request.data.get("document_name")
#         if document_name:
#             exists = CompanyDocument.objects.filter(
#                 company_id=company_id,
#                 document_name=document_name,
#                 del_flag=0
#             ).exists()

#             if exists:
#                 return StandardResponse.error(
#                     message=f"Document '{document_name}' already exists",
#                     status_code=status.HTTP_409_CONFLICT
#                 )

#         # Validate data
#         serializer = CompanySingleDocumentUploadSerializer(
#             data=request.data,
#             context={"company_id": company_id, "request": request}
#         )

#         if not serializer.is_valid():
#             return StandardResponse.error(
#                 message="Validation failed",
#                 errors=serializer.errors
#             )

#         # Save document
#         try:
#             with transaction.atomic():
#                 document = serializer.save()

#                 if hasattr(company, "application") and company.application:
#                     self.update_document_step(company)

#             step_completed = CompanyDocument.check_company_documents_complete(company_id)

#             return StandardResponse.created(
#                 data={
#                     "id": str(document.document_id),
#                     "name": document.get_document_name_display(),
#                     "type": document.document_type,
#                     "size": document.file_size,
#                     "mandatory": document.is_mandatory,
#                     "step_completed": step_completed
#                 },
#                 message="Document uploaded successfully"
#             )

#         except Exception as e:
#             logger.error(f"[SINGLE_UPLOAD] Error: {str(e)}", exc_info=True)
#             return StandardResponse.error(
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

#         # Check admin permission
#         if not request.user.is_staff:
#             return StandardResponse.error(
#                 message="Admin access required",
#                 status_code=status.HTTP_403_FORBIDDEN
#             )

#         # Validate company
#         try:
#             CompanyInformation.objects.get(company_id=company_id, del_flag=0)
#         except CompanyInformation.DoesNotExist:
#             return StandardResponse.not_found("Company not found")

#         # Get document
#         try:
#             document = CompanyDocument.objects.get(
#                 document_id=document_id,
#                 company_id=company_id,
#                 del_flag=0
#             )
#         except CompanyDocument.DoesNotExist:
#             return StandardResponse.not_found("Document not found")

#         # Validate request
#         is_verified = request.data.get('is_verified')
#         if is_verified is None:
#             return StandardResponse.error("is_verified field is required")

#         # Update verification
#         try:
#             document.is_verified = is_verified
#             document.user_id_updated_by = request.user
#             document.save(update_fields=['is_verified', 'user_id_updated_by', 'updated_at'])

#             message = "Document verified successfully" if is_verified else "Document rejected"

#             return StandardResponse.success(
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
#             return StandardResponse.error(
#                 message="Failed to verify document",
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging
from django.utils import timezone

# ✅ import your centralized APIResponse helper
from config.common.response import APIResponse

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


# ============================================================================
# BULK UPLOAD VIEW
# ============================================================================
class CompanyDocumentBulkUploadView(APIView):
    """Bulk upload company documents"""
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser]

    def update_step_three(self, company, documents):
        """Update onboarding step 3 without serialization issues"""
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
        operation_description="Bulk upload company documents",
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
        from ..models.CompanyInformationModel import CompanyInformation
        from ..models.CompanyDocumentModel import CompanyDocument

        logger.info(f"[BULK_UPLOAD] company_id={company_id}")

        # ✅ Validate company
        try:
            company = CompanyInformation.objects.select_related("application").get(
                company_id=company_id, del_flag=0
            )
        except CompanyInformation.DoesNotExist:
            return APIResponse.error(
                message="Company not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # ✅ Validate input data
        serializer = CompanyDocumentBulkUploadSerializer(
            data=request.data,
            context={"company_id": company_id, "request": request}
        )

        if not serializer.is_valid():
            return APIResponse.error(
                message="Validation failed",
                errors=serializer.errors
            )

        # ✅ Save documents in transaction
        try:
            with transaction.atomic():
                documents = serializer.save()
                self.update_step_three(company, documents)
        except Exception as e:
            logger.error(f"[BULK_UPLOAD] Error: {str(e)}", exc_info=True)
            return APIResponse.error(
                message="Failed to upload documents",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # ✅ Prepare response
        step_completed = CompanyDocument.check_company_documents_complete(company_id)
        
        return APIResponse.success(
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
            message="Documents uploaded successfully",
            status_code=status.HTTP_201_CREATED
        )

# ============================================================================
# LIST DOCUMENTS VIEW
# ============================================================================
class CompanyDocumentListView(APIView, DocumentQueryOptimizationMixin):
    """List all documents for a company"""
    permission_classes = []

    @swagger_auto_schema(
        operation_description="Get list of all documents",
        manual_parameters=[
            openapi.Parameter('company_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True)
        ],
        responses={200: CompanyDocumentListSerializer(many=True), 404: "Company not found"}
    )
    def get(self, request, company_id):
        from ..models.CompanyInformationModel import CompanyInformation

        logger.info(f"[LIST_DOCS] company_id={company_id}")

        # Validate company
        try:
            CompanyInformation.objects.get(company_id=company_id, del_flag=0)
        except CompanyInformation.DoesNotExist:
            return APIResponse.error(
                message="Company not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        try:
            documents = self.get_optimized_documents_queryset(company_id)
            doc_status = DocumentStatusChecker.get_company_document_status(company_id)
            serializer = CompanyDocumentListSerializer(documents, many=True)

            return APIResponse.success(
                data={
                    "documents": serializer.data,
                    "summary": {
                        "total": doc_status.get("total_documents", 0),
                        "mandatory_uploaded": doc_status.get("uploaded_mandatory", 0),
                        "optional_uploaded": doc_status.get("uploaded_optional", 0),
                        "all_mandatory_complete": doc_status.get("all_mandatory_uploaded", False)
                    }
                },
                message="Documents retrieved successfully"
            )

        except Exception as e:
            logger.error(f"[LIST_DOCS] Error: {str(e)}", exc_info=True)
            return APIResponse.error(
                message="Failed to retrieve documents",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# DOCUMENT DETAIL VIEW
# ============================================================================
class CompanyDocumentDetailView(APIView, DocumentQueryOptimizationMixin, SoftDeleteMixin):
    """Retrieve, update or delete a specific document"""
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Get document details",
        manual_parameters=[
            openapi.Parameter('company_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('document_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True)
        ],
        responses={200: CompanyDocumentDetailSerializer(), 404: "Not found"}
    )
    def get(self, request, company_id, document_id):
        from ..models.CompanyInformationModel import CompanyInformation

        logger.info(f"[GET_DOC] company_id={company_id}, document_id={document_id}")

        try:
            CompanyInformation.objects.get(company_id=company_id, del_flag=0)
        except CompanyInformation.DoesNotExist:
            return APIResponse.error(
                message="Company not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        try:
            document = self.get_document_with_company(document_id, company_id)
            serializer = CompanyDocumentDetailSerializer(document, context={'request': request})

            return APIResponse.success(
                data=serializer.data,
                message="Document retrieved successfully"
            )

        except Exception as e:
            logger.error(f"[GET_DOC] Error: {str(e)}", exc_info=True)
            return APIResponse.error(
                message="Document not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Update document",
        manual_parameters=[
            openapi.Parameter('company_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('document_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True)
        ],
        responses={200: "Updated", 400: "Validation error", 404: "Not found"}
    )
    def put(self, request, company_id, document_id):
        from ..models.CompanyInformationModel import CompanyInformation

        logger.info(f"[UPDATE_DOC] company_id={company_id}, document_id={document_id}")

        try:
            CompanyInformation.objects.get(company_id=company_id, del_flag=0)
        except CompanyInformation.DoesNotExist:
            return APIResponse.error(
                message="Company not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        try:
            document = self.get_document_with_company(document_id, company_id)
        except Exception:
            return APIResponse.error(
                message="Document not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        if not request.FILES.get('file'):
            return APIResponse.error(message="File is required")

        update_data = {
            'document_name': document.document_name,
            'file': request.FILES.get('file')
        }

        serializer = CompanySingleDocumentUploadSerializer(
            instance=document,
            data=update_data,
            context={'company_id': company_id, 'request': request}
        )

        if not serializer.is_valid():
            return APIResponse.error(
                message="Validation failed",
                errors=serializer.errors
            )

        try:
            updated_document = serializer.save()

            return APIResponse.success(
                data={
                    "id": str(updated_document.document_id),
                    "name": updated_document.get_document_name_display(),
                    "type": updated_document.document_type,
                    "size": updated_document.file_size,
                    "updated_at": updated_document.updated_at.isoformat()
                },
                message="Document updated successfully"
            )

        except Exception as e:
            logger.error(f"[UPDATE_DOC] Error: {str(e)}", exc_info=True)
            return APIResponse.error(
                message="Failed to update document",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Delete document",
        manual_parameters=[
            openapi.Parameter('company_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('document_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True)
        ],
        responses={200: "Deleted", 404: "Not found"}
    )
    def delete(self, request, company_id, document_id):
        from ..models.CompanyInformationModel import CompanyInformation

        logger.info(f"[DELETE_DOC] company_id={company_id}, document_id={document_id}")

        try:
            CompanyInformation.objects.get(company_id=company_id, del_flag=0)
        except CompanyInformation.DoesNotExist:
            return APIResponse.error(
                message="Company not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        try:
            document = self.get_document_with_company(document_id, company_id)
        except Exception:
            return APIResponse.error(
                message="Document not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = CompanySingleDocumentUploadSerializer(
            context={'company_id': company_id, 'request': request}
        )

        try:
            serializer.soft_delete(document)

            return APIResponse.success(
                data={
                    "id": str(document.document_id),
                    "name": document.get_document_name_display()
                },
                message="Document deleted successfully"
            )

        except Exception as e:
            logger.error(f"[DELETE_DOC] Error: {str(e)}", exc_info=True)
            return APIResponse.error(
                message="Failed to delete document",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# DOCUMENT STATUS VIEW
# ============================================================================
class CompanyDocumentStatusView(APIView):
    """Check document verification status"""
    permission_classes = []

    @swagger_auto_schema(
        operation_description="Get document verification status",
        manual_parameters=[
            openapi.Parameter('company_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True)
        ],
        responses={200: CompanyDocumentStatusSerializer(), 404: "Company not found"}
    )
    def get(self, request, company_id):
        from ..models.CompanyInformationModel import CompanyInformation
        from ..models.CompanyDocumentModel import CompanyDocument

        logger.info(f"[DOC_STATUS] company_id={company_id}")

        try:
            CompanyInformation.objects.get(company_id=company_id, del_flag=0)
        except CompanyInformation.DoesNotExist:
            return APIResponse.error(
                message="Company not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        try:
            documents = CompanyDocument.objects.filter(
                company_id=company_id,
                del_flag=0
            ).values('document_id', 'document_name', 'is_mandatory', 'is_verified', 'uploaded_at')

            total_docs = len(documents)
            verified_docs = sum(1 for doc in documents if doc['is_verified'])
            pending_docs = total_docs - verified_docs
            
            mandatory_docs = [doc for doc in documents if doc['is_mandatory']]
            mandatory_verified = sum(1 for doc in mandatory_docs if doc['is_verified'])
            
            optional_docs = [doc for doc in documents if not doc['is_mandatory']]
            optional_verified = sum(1 for doc in optional_docs if doc['is_verified'])

            document_list = [
                {
                    "id": str(doc['document_id']),
                    "name": dict(CompanyDocument.DOCUMENT_NAMES).get(doc['document_name'], doc['document_name']),
                    "mandatory": doc['is_mandatory'],
                    "verification_status": "verified" if doc['is_verified'] else "pending",
                    "uploaded_at": doc['uploaded_at'].isoformat()
                }
                for doc in documents
            ]

            return APIResponse.success(
                data={
                    "overall_status": "all_verified" if verified_docs == total_docs else "pending_verification",
                    "statistics": {
                        "total_documents": total_docs,
                        "verified": verified_docs,
                        "pending": pending_docs
                    },
                    "mandatory": {
                        "total": len(mandatory_docs),
                        "verified": mandatory_verified,
                        "pending": len(mandatory_docs) - mandatory_verified,
                        "all_verified": mandatory_verified == len(mandatory_docs) if mandatory_docs else False
                    },
                    "optional": {
                        "total": len(optional_docs),
                        "verified": optional_verified,
                        "pending": len(optional_docs) - optional_verified
                    },
                    "documents": document_list
                },
                message="Document verification status retrieved successfully"
            )

        except Exception as e:
            logger.error(f"[DOC_STATUS] Error: {str(e)}", exc_info=True)
            return APIResponse.error(
                message="Failed to retrieve verification status",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# SINGLE DOCUMENT UPLOAD VIEW
# ============================================================================
class CompanySingleDocumentUploadView(APIView, ApplicationStepUpdateMixin):
    """Upload a single document"""
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Upload a single document",
        manual_parameters=[
            openapi.Parameter('company_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('document_name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True)
        ],
        responses={201: "Created", 400: "Validation error", 404: "Not found", 409: "Conflict"}
    )
    def post(self, request, company_id):
        from ..models.CompanyDocumentModel import CompanyDocument
        from ..models.CompanyInformationModel import CompanyInformation

        logger.info(f"[SINGLE_UPLOAD] company_id={company_id}")

        try:
            company = CompanyInformation.objects.get(company_id=company_id, del_flag=0)
        except CompanyInformation.DoesNotExist:
            return APIResponse.error(
                message="Company not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        document_name = request.data.get("document_name")
        if document_name:
            exists = CompanyDocument.objects.filter(
                company_id=company_id,
                document_name=document_name,
                del_flag=0
            ).exists()

            if exists:
                return APIResponse.error(
                    message=f"Document '{document_name}' already exists",
                    status_code=status.HTTP_409_CONFLICT
                )

        serializer = CompanySingleDocumentUploadSerializer(
            data=request.data,
            context={"company_id": company_id, "request": request}
        )

        if not serializer.is_valid():
            return APIResponse.error(
                message="Validation failed",
                errors=serializer.errors
            )

        try:
            with transaction.atomic():
                document = serializer.save()

                if hasattr(company, "application") and company.application:
                    self.update_document_step(company)

            step_completed = CompanyDocument.check_company_documents_complete(company_id)

            return APIResponse.success(
                data={
                    "id": str(document.document_id),
                    "name": document.get_document_name_display(),
                    "type": document.document_type,
                    "size": document.file_size,
                    "mandatory": document.is_mandatory,
                    "step_completed": step_completed
                },
                message="Document uploaded successfully",
                status_code=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"[SINGLE_UPLOAD] Error: {str(e)}", exc_info=True)
            return APIResponse.error(
                message="Failed to upload document",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# DOCUMENT VERIFICATION VIEW (ADMIN)
# ============================================================================
class CompanyDocumentVerificationView(APIView):
    """Verify/reject documents (Admin only)"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Verify or reject document (Admin only)",
        manual_parameters=[
            openapi.Parameter('company_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('document_id', openapi.IN_PATH, type=openapi.TYPE_STRING, required=True)
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
    def patch(self, request, company_id, document_id):
        from ..models.CompanyDocumentModel import CompanyDocument
        from ..models.CompanyInformationModel import CompanyInformation

        logger.info(f"[VERIFY_DOC] user={request.user.user_id}, document_id={document_id}")

        if not request.user.is_staff:
            return APIResponse.error(
                message="Admin access required",
                status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            CompanyInformation.objects.get(company_id=company_id, del_flag=0)
        except CompanyInformation.DoesNotExist:
            return APIResponse.error(
                message="Company not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        try:
            document = CompanyDocument.objects.get(
                document_id=document_id,
                company_id=company_id,
                del_flag=0
            )
        except CompanyDocument.DoesNotExist:
            return APIResponse.error(
                message="Document not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        is_verified = request.data.get('is_verified')
        if is_verified is None:
            return APIResponse.error(message="is_verified field is required")

        try:
            document.is_verified = is_verified
            document.user_id_updated_by = request.user
            document.save(update_fields=['is_verified', 'user_id_updated_by', 'updated_at'])

            message = "Document verified successfully" if is_verified else "Document rejected"

            return APIResponse.success(
                data={
                    "id": str(document.document_id),
                    "name": document.get_document_name_display(),
                    "verified": document.is_verified,
                    "verified_by": str(request.user.user_id),
                    "verified_at": document.updated_at.isoformat()
                },
                message=message
            )

        except Exception as e:
            logger.error(f"[VERIFY_DOC] Error: {str(e)}", exc_info=True)
            return APIResponse.error(
                message="Failed to verify document",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
