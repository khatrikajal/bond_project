from apps.kyc.issuer_kyc.models.FinancialDocumentModel import (
    DocumentType, DocumentTag, PeriodType, VerificationSource
)
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.core.files.storage import default_storage
from django.utils import timezone
from apps.kyc.issuer_kyc.models.FinancialDocumentModel import FinancialDocument
from apps.kyc.issuer_kyc.serializers.FinancialDocumentsSerializers import (
    FinancialDocumentUploadSerializer,
    FinancialDocumentSerializer,
    BulkUploadSerializer,
    DocumentFilterSerializer,
    BulkDeleteSerializer,
    BulkUpdateSerializer
)
from calendar import month_name
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from django.http import Http404
from apps.kyc.issuer_kyc.services.financial_documents.financial_document_service import FinancialDocumentService
import hashlib
from config.common.response import APIResponse
import logging
from django.core.files import File
from django.conf import settings
import os


logger = logging.getLogger(__name__)





# class FinancialDocumentViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet for managing financial documents
    
#     Endpoints:
#     - POST /api/documents/ - Upload single document
#     - POST /api/documents/bulk_upload/ - Upload multiple documents
#     - GET /api/documents/ - List all documents (with filters)
#     - GET /api/documents/{id}/ - Get specific document
#     - PUT /api/documents/{id}/ - Update document
#     - DELETE /api/documents/{id}/ - Soft delete document
#     - POST /api/documents/{id}/verify/ - Trigger verification
#     - GET /api/documents/{id}/download/ - Download document
#     - GET /api/documents/missing_documents/ - Get missing documents report
#     """
    
#     queryset = FinancialDocument.objects.filter(del_flag=0)
#     serializer_class = FinancialDocumentSerializer
#     lookup_field = "document_id"
    
#     permission_classes = [IsAuthenticated]
    
#     def get_queryset(self):
#         qs = super().get_queryset()
#         # 1️⃣ PROTECT — ensure company belongs to logged-in user
#         company = CompanyInformation.objects.filter(
#             company_id=self.kwargs["company_id"],
#             user=self.request.user
#         ).first()

#         if not company:
#             return FinancialDocument.objects.none()
#         qs = qs.filter(company_id=self.kwargs["company_id"], del_flag=0)

#         fs = DocumentFilterSerializer(data=self.request.query_params)
#         if fs.is_valid():
#             f = fs.validated_data
#             if "document_type" in f: qs = qs.filter(document_type=f["document_type"])
#             if "document_tag" in f:  qs = qs.filter(document_tag=f["document_tag"])
#             if "financial_year" in f:qs = qs.filter(financial_year=f["financial_year"])
#             if "is_verified" in f:   qs = qs.filter(is_verified=f["is_verified"])
#             if "period_type" in f:   qs = qs.filter(period_type=f["period_type"])

#         return qs.order_by("-created_at")


       
#     def retrieve(self, request, company_id, document_id=None, *args, **kwargs):
#         try:
#             document = self.get_object()
#             serializer = FinancialDocumentSerializer(document)

#             return APIResponse.success(
#                 message="Document fetched successfully",
#                 data=serializer.data
#             )
        
#         except Http404:
#             return APIResponse.error( message=f"Document not found", status_code=404)
        
#         except Exception as e:
#             logger.error(f"Retrieve document failed: {e}", exc_info=True)
#             return APIResponse.error( message="Internal server error", status_code=500)

#     def list(self, request, company_id, *args, **kwargs):
#         try:
#             qs = self.filter_queryset(self.get_queryset())

#             serializer = FinancialDocumentSerializer(qs, many=True)
#             return APIResponse.success(
#                 message="Documents fetched successfully",
#                 data=serializer.data,
#                 status_code=200
#             )
#         except Exception as e:
#             logger.error(f"List documents failed: {e}", exc_info=True)
#             return APIResponse.error( message="Internal server error", status_code=500)


#     @transaction.atomic
#     def create(self, request, company_id, *args, **kwargs):
#         try:
#             if not company_id:
#                 return APIResponse.error( "company_id missing", status_code=400)

#             serializer = FinancialDocumentUploadSerializer(
#                 data=request.data,
#                 context={"company_id": company_id}
#             )
#             serializer.is_valid(raise_exception=True)
#             vd = serializer.validated_data

#             file = vd.pop("file")
#             auto_verify = vd.pop("auto_verify", True)
#             vd.pop("period_month", None)
#             vd.pop("period_quarter", None)

#             file_hash = self._compute_file_hash(file)

#             latest = self._get_latest_version(
#                 company_id,
#                 vd["document_type"],
#                 vd["period_start_date"],
#                 vd["period_end_date"],
#                 vd["document_tag"],
#             )

#             if latest and latest.file_hash == file_hash:
#                 return APIResponse.error(
                    
#                     message="This exact file is already uploaded",
#                     data={
#                         "document_id": latest.document_id,
#                         "version": latest.version
#                     },
#                     status_code=400
#                 )

#             version = latest.version + 1 if latest else 1

#             document = FinancialDocument(
#                 company_id=company_id,
#                 file_hash=file_hash,
#                 user_id_updated_by=request.user,
#                 **vd,
#             )

#             document.file_name = file.name
#             document.file_size = file.size
#             document.mime_type = getattr(file, "content_type", "application/pdf")
#             document.file_path.save(file.name, file, save=True)
#             FinancialDocumentService.update_onboarding_state(company_id)


#             if auto_verify:
#                 logger.info(f"Triggering verification for document {document.document_id}")
#                 self._trigger_verification(document)

#             return APIResponse.success(
                
#                 message="Document uploaded successfully",
#                 data={
#                     "verification_triggered": auto_verify,
#                     **FinancialDocumentSerializer(document).data
#                 },
#                 status_code=201
#             )
#         except ValidationError as e:
#             # return proper serializer errors
#             return APIResponse.error(
                
#                 message="Validation failed",
#                 data=e.detail,               # serializer error dict
#                 status_code=400
#             )
#         except Exception as e:
#             logger.error(f"CREATE document failed: {e}", exc_info=True)
#             return APIResponse.error(message="Internal server error", status_code=500)
        
   
#     def update(self, request, company_id,document_id=None, *args, **kwargs):
#         try:
#             document = self.get_object()

#             serializer = FinancialDocumentUploadSerializer(
#                 data=request.data, partial=True,
#                 context={"company_id": company_id}
#             )
#             serializer.is_valid(raise_exception=True)
#             vd = serializer.validated_data

#             file = vd.pop("file", None)
#             auto_verify = vd.pop("auto_verify", True)
#             vd.pop("period_month", None)
#             vd.pop("period_quarter", None)

#             # CASE 1 — new version due to file change
#             if file:
#                 new_hash = self._compute_file_hash(file)

#                 if new_hash == document.file_hash:
#                     return APIResponse.error(
#                         message="Uploaded file is identical to existing version",
#                         status_code=400
#                     )

#                 # replace PDF file
#                 document.file_path.delete(save=False)
#                 document.file_path.save(file.name, file, save=True)

#                 # update meta
#                 document.file_hash = new_hash
#                 document.file_name = file.name
#                 document.file_size = file.size
#                 document.mime_type = getattr(file, "content_type", "application/pdf")

#                 # reset verification (because file changed)
#                 document.is_verified = False
#                 document.verified_at = None

#             # CASE 2 — metadata update only
#             for k, v in vd.items():
#                 setattr(document, k, v)

#             document.user_id_updated_by = request.user
#             document.save()
#             if any(field in vd for field in [
#                 "financial_year",
#                 "period_type",
#                 "period_start_date",
#                 "period_end_date",
#                 "period_month",
#                 "period_quarter",
#                 "document_type",
#             ]):
#                 FinancialDocumentService.update_onboarding_state(company_id)



#             return APIResponse.success(
#                 message="Document metadata updated",
#                 data=FinancialDocumentSerializer(document).data
#             )
#         except ValidationError as e:
#             # return proper serializer errors
#             return APIResponse.error(
              
#                 message="Validation failed",
#                 data=e.detail,               # serializer error dict
#                 status_code=400
#             )
        
#         except Exception as e:
#             logger.error(f"Update failed: {e}", exc_info=True)
#             return APIResponse.error(message="Internal server error", status_code=500)


#     def partial_update(self, request, company_id, document_id=None, *args, **kwargs):
#         try:
#             document = self.get_object()

#             serializer = FinancialDocumentUploadSerializer(
#                 data=request.data,
#                 partial=True,                       # partial update
#                 context={"company_id": company_id}
#             )
#             serializer.is_valid(raise_exception=True)
#             vd = serializer.validated_data

#             file = vd.pop("file", None)
#             auto_verify = vd.pop("auto_verify", True)
#             vd.pop("period_month", None)
#             vd.pop("period_quarter", None)

#             # FILE update (optional)
#             if file:
#                 new_hash = self._compute_file_hash(file)

#                 if new_hash == document.file_hash:
#                     return APIResponse.error(
                      
#                         message="Uploaded file is identical to existing version",
#                         status_code=400
#                     )

#                 # replace file
#                 document.file_path.delete(save=False)
#                 document.file_path.save(file.name, file, save=True)

#                 document.file_hash = new_hash
#                 document.file_name = file.name
#                 document.file_size = file.size
#                 document.mime_type = getattr(file, "content_type", "application/pdf")

#                 document.is_verified = False
#                 document.verified_at = None

#             # METADATA update (only fields provided)
#             for k, v in vd.items():
#                 setattr(document, k, v)

#             document.user_id_updated_by = request.user
#             document.save()
#             if any(field in vd for field in [
#                 "financial_year",
#                 "period_type",
#                 "period_start_date",
#                 "period_end_date",
#                 "period_month",
#                 "period_quarter",
#             ]):
#                 FinancialDocumentService.update_onboarding_state(company_id)

#             return APIResponse.success(
#                 message="Document partially updated",
#                 data=FinancialDocumentSerializer(document).data
#             )

#         except ValidationError as e:
#             return APIResponse.error(
                
#                 message="Validation failed",
#                 data=e.detail,
#                 status_code=400
#             )

#         except Exception as e:
#             logger.error(f"Partial update failed: {e}", exc_info=True)
#             return APIResponse.error(message="Internal server error", status_code=500)
   
#     def destroy(self, request, *args, **kwargs):
#         try:
#             document = self.get_object()
#             document.del_flag = 1
#             document.user_id_updated_by = request.user
#             document.save()
#             company_id = document.company_id
#             FinancialDocumentService.update_onboarding_state(company_id)
#             return APIResponse.success(message="Document deleted successfully")
        
#         except Exception as e:
#             logger.error(f"Delete failed: {e}", exc_info=True)
#             return APIResponse.error(message="Internal server error", status_code=500)
    

#     #--------------- Bulk Operations ------------
    
#     @action(detail=False, methods=["post"])
#     @transaction.atomic
#     def bulk_upload(self, request, company_id):
#         try:
#             if not company_id:
#                 return APIResponse.error(message="company_id missing", status_code=400)

#             bulk = BulkUploadSerializer(
#                 data=request.data,
#                 context={"company_id": company_id}
#             )
#             bulk.is_valid(raise_exception=True)

#             documents = bulk.validated_data["documents"]
#             files = bulk.validated_data["files"]

#             results = {"success": [], "failed": []}

#             for idx, doc_meta in enumerate(documents):
#                 try:
#                     file = files[idx]

#                     payload = {
#                         **doc_meta,
#                         "file": file,
#                         "auto_verify": doc_meta.get("auto_verify", True)
#                     }

#                     serializer = FinancialDocumentUploadSerializer(
#                         data=payload,
#                         context={"company_id": company_id}
#                     )

#                     if not serializer.is_valid():
#                         results["failed"].append({
#                             "index": idx,
#                             "errors": serializer.errors
#                         })
#                         continue

#                     vd = serializer.validated_data
#                     vd.pop("period_month", None)
#                     vd.pop("period_quarter", None)
#                     auto_verify = vd.pop("auto_verify", True)
#                     file = vd.pop("file")

#                     file_hash = self._compute_file_hash(file)

#                     latest = self._get_latest_version(
#                         company_id,
#                         vd["document_type"],
#                         vd["period_start_date"],
#                         vd["period_end_date"],
#                         vd["document_tag"]
#                     )

#                     if latest and latest.file_hash == file_hash:
#                         results["failed"].append({
#                             "index": idx,
#                             "error": "File already uploaded"
#                         })
#                         continue

                   

#                     document = FinancialDocument(
#                         company_id=company_id,
            
#                         file_hash=file_hash,
#                         user_id_updated_by=request.user,
#                         **vd
#                     )

#                     document.file_name = file.name
#                     document.file_size = file.size
#                     document.mime_type = getattr(file, "content_type", "application/pdf")
#                     document.file_path.save(file.name, file, save=True)
                    


#                     if auto_verify:
#                         self._trigger_verification(document)

#                     results["success"].append({
#                         "index": idx,
#                         "document_id": document.document_id,
#                         "file_name": document.file_name
#                     })

#                 except Exception as e:
#                     logger.error(f"Bulk item {idx} failed: {e}", exc_info=True)
#                     results["failed"].append({"index": idx, "error": str(e)})
            
#             # after loop
#             FinancialDocumentService.update_onboarding_state(company_id)

#             return APIResponse.success(
               
#                 message=f"{len(results['success'])} succeeded, {len(results['failed'])} failed",
#                 data=results
#             )

#         except ValidationError as e:
#             return APIResponse.error(
               
#                 message="Validation failed",
#                 errors=e.detail,
#                 status_code=400
#             )

#         except Exception as e:
#             logger.error(f"Bulk upload failed: {e}", exc_info=True)
#             return APIResponse.error(message="Internal server error", status_code=500)

#     @action(detail=False, methods=["patch"])
#     @transaction.atomic
#     def bulk_update(self, request, company_id):
#         try:
            
#             bulk = BulkUpdateSerializer(data=request.data)
#             bulk.is_valid(raise_exception=True)

#             updates = bulk.validated_data["updates"]

#             if not updates:
#                 return APIResponse.error(message="No update payloads provided", status_code=400)
            

#             results = {"success": [], "failed": []}

#             needs_state_update = False
#             for idx, item in enumerate(updates):
#                 try:
#                     doc_id = item.get("document_id")
#                     metadata = item.get("metadata", {})

#                     file = request.FILES.get(f"file_{doc_id}")

#                     document = FinancialDocument.objects.filter(
#                         document_id=doc_id,
#                         company_id=company_id,
#                         del_flag=0
#                     ).first()

#                     if not document:
#                         results["failed"].append({
#                             "index": idx,
#                             "error": "Document not found"
#                         })
#                         continue

#                     # build payload for serializer
#                     payload = metadata.copy()
#                     if file:
#                         payload["file"] = file

#                     # validate metadata using FINANCIAL document serializer
#                     serializer = FinancialDocumentUploadSerializer(
#                         data=payload,
#                         partial=True,
#                         context={"company_id": company_id}
#                     )

#                     if not serializer.is_valid():
#                         results["failed"].append({
#                             "index": idx,
#                             "errors": serializer.errors
#                         })
#                         continue

#                     vd = serializer.validated_data
#                     vd.pop("period_month", None)
#                     vd.pop("period_quarter", None)
#                     vd.pop("auto_verify", None)

#                     # FILE UPDATE
#                     if file:
#                         new_hash = self._compute_file_hash(file)

#                         if new_hash != document.file_hash:
#                             document.file_hash = new_hash
#                             document.file_name = file.name
#                             document.file_size = file.size
#                             document.mime_type = getattr(file, "content_type", "application/pdf")
#                             document.file_path.save(file.name, file, save=True)

#                     # METADATA UPDATE
#                     for k, v in vd.items():
#                         setattr(document, k, v)

#                     document.save()
#                     if any(field in vd for field in [
#                         "financial_year",
#                         "period_type",
#                         "period_start_date",
#                         "period_end_date",
#                         "period_month",
#                         "period_quarter",
#                         "document_type",
#                     ]):
#                         needs_state_update = True

#                     results["success"].append({"index": idx, "document_id": doc_id})

#                 except Exception as e:
#                     logger.error(f"Bulk update item {idx} failed: {e}", exc_info=True)
#                     results["failed"].append({"index": idx, "error": str(e)})
            
#             if needs_state_update:
#                 FinancialDocumentService.update_onboarding_state(company_id)

#             return APIResponse.success(
                
#                 message=f"{len(results['success'])} succeeded, {len(results['failed'])} failed",
#                 data=results
#             )

#         except Exception as e:
#             logger.error(f"Bulk update failed: {e}", exc_info=True)
#             return APIResponse.error(message="Internal server error", status_code=500)


#     @action(detail=False, methods=["delete"])
#     @transaction.atomic
#     def bulk_delete(self, request, company_id):
#         try:
#             serializer = BulkDeleteSerializer(data=request.data)
#             serializer.is_valid(raise_exception=True)

#             doc_ids = serializer.validated_data["document_ids"]
#             results = {"success": [], "failed": []}

#             for idx, doc_id in enumerate(doc_ids):
#                 try:
#                     document = FinancialDocument.objects.get(
#                         document_id=doc_id,
#                         company_id=company_id,
#                         del_flag=0
#                     )

#                     document.del_flag = 1
#                     document.save()

#                     results["success"].append({"document_id": doc_id})

#                 except FinancialDocument.DoesNotExist:
#                     results["failed"].append({
#                         "document_id": doc_id,
#                         "error": "Document not found"
#                     })
#                 except Exception as e:
#                     results["failed"].append({
#                         "document_id": doc_id,
#                         "error": str(e)
#                     })
            
#             FinancialDocumentService.update_onboarding_state(company_id)
#             return APIResponse.success(
                
#                 message=f"{len(results['success'])} succeeded, {len(results['failed'])} failed",
#                 data=results
#             )

#         except Exception as e:
#             logger.error(f"Bulk delete failed: {e}", exc_info=True)
#             return APIResponse.error(message="Internal server error", status_code=500)
    
#     @action(detail=True, methods=['get'])
#     def download(self, request, company_id, pk=None):
#         if not company_id:
#             return APIResponse.error(
#                 message="Company not found for this",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         document = self.get_object()
#         if not document.file_path:
#             return APIResponse.error(
#                 message="File not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         return APIResponse.success(
#             message="File fetched successfully",
#             data={
#                 "download_url": document.file_path.url,   # works for local or S3
#                 "file_name": document.file_name,
#                 "file_size": document.file_size
#             },
#             status_code=status.HTTP_200_OK
#         )


#     @action(detail=False, methods=['get'])
#     def missing_documents(self, request, company_id):
#         if not company_id:
#             return APIResponse.error(
#                 message="Company not found for this",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         company = get_object_or_404(CompanyInformation, pk=company_id)
#         financial_year = request.query_params.get('financial_year')

#         if not company or not financial_year:
#             return APIResponse.error(
#                 message="company and financial_year are required",
#                 status_code=status.HTTP_400_BAD_REQUEST
#             )

#         # FY start year, e.g., "FY2023-24" -> 2023
#         fy_num = int(financial_year.replace('FY', '').replace(' ', '').split('-')[0])

#         # months in FY order: Apr..Dec (4..12) then Jan..Mar (1..3)
#         fy_months = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]

#         existing = FinancialDocument.objects.filter(
#             company_id=company,
#             financial_year=financial_year,
#             document_type=DocumentType.GSTR_3B,
#             period_type=PeriodType.MONTHLY,
#             del_flag=0
#         ).values_list('period_start_date', flat=True)

#         existing_months = set(d.month for d in existing)
#         missing_months = [m for m in fy_months if m not in existing_months]

#         # yearly docs
#         yearly_missing = {}
#         for dt in [DocumentType.GSTR_9, DocumentType.ITR, DocumentType.FINANCIAL_STATEMENT]:
#             exists = FinancialDocument.objects.filter(
#                 company_id=company,
#                 financial_year=financial_year,
#                 document_type=dt,
#                 period_type=PeriodType.YEARLY,
#                 del_flag=0
#             ).exists()
#             if not exists:
#                 yearly_missing[dt] = ["Required"]

#         return APIResponse.success(
#             message="Missing documents fetched successfully",
#             data={
#                 "GSTR_3B": [month_name[m] for m in missing_months],
#                 **yearly_missing
#             },
#             status_code=status.HTTP_200_OK
#         )

#     # @action(detail=True, methods=['get'])
#     # def download(self, request,company_id, pk=None):
#     #     if not company_id:
#     #         return Response({
#     #             "status": 
#     #             "message": "Company not found for this",
#     #         }, status=404)
#     #     document = self.get_object()
#     #     if not document.file_path:
#     #         return Response({'success': False, 'message': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

#     #     return Response({
#     #         'success': True,
#     #         'data': {
#     #             'download_url': document.file_path.url,   # works for local or S3
#     #             'file_name': document.file_name,
#     #             'file_size': document.file_size
#     #         }
#     #     }, status=status.HTTP_200_OK)

    
#     # @action(detail=False, methods=['get'])
#     # def missing_documents(self, request,company_id):
#     #     if not company_id:
#     #         return Response({
#     #             "status": 
#     #             "message": "Company not found for this",
#     #         }, status=404)
#     #     company = get_object_or_404(CompanyInformation,pk=company_id)
#     #     financial_year = request.query_params.get('financial_year')
#     #     if not company or not financial_year:
#     #         return Response({'success': False, 'message': 'company and financial_year are required'},
#     #                         status=status.HTTP_400_BAD_REQUEST)

#     #     # FY start year, e.g., "FY2023-24" -> 2023
#     #     fy_num = int(financial_year.replace('FY', '').replace(' ', '').split('-')[0])

#     #     # months in FY order: Apr..Dec (4..12) then Jan..Mar (1..3)
#     #     fy_months = [4,5,6,7,8,9,10,11,12,1,2,3]

#     #     existing = FinancialDocument.objects.filter(
#     #         company_id=company,
#     #         financial_year=financial_year,
#     #         document_type=DocumentType.GSTR_3B,
#     #         period_type=PeriodType.MONTHLY,
#     #         del_flag=0
#     #     ).values_list('period_start_date', flat=True)

#     #     existing_months = set(d.month for d in existing)
#     #     missing_months = [m for m in fy_months if m not in existing_months]

#     #     # yearly docs
#     #     yearly_missing = {}
#     #     for dt in [DocumentType.GSTR_9, DocumentType.ITR, DocumentType.FINANCIAL_STATEMENT]:
#     #         exists = FinancialDocument.objects.filter(
#     #             company_id=company,
#     #             financial_year=financial_year,
#     #             document_type=dt,
#     #             period_type=PeriodType.YEARLY,
#     #             del_flag=0
#     #         ).exists()
#     #         if not exists:
#     #             yearly_missing[dt] = ['Required']

#     #     return Response({
#     #         'success': True,
#     #         'data': {
#     #             'GSTR_3B': [month_name[m] for m in missing_months],
#     #             **yearly_missing
#     #         }
#     #     }, status=status.HTTP_200_OK)
    
    
#     #------------- Helper methods ----------------
#     def _upload_file_to_storage(self, file, company_id, doc_type, fy):
#         """Upload file to S3 or local storage"""
        
#         # Generate unique file path
#         file_path = f"financial_docs/{company_id}/{fy}/{doc_type}/{timezone.now().timestamp()}_{file.name}"
        
#         # Upload to storage
#         saved_path = default_storage.save(file_path, file)
        
#         return saved_path
    
#     def _trigger_verification(self, document):
#         """Trigger async verification (using Celery or similar)"""
        
#         # Import here to avoid circular imports
#         # from celery_task.financial_document_tasks import verify_document_async
        
#         # # Queue verification task
#         # verify_document_async.delay(document.document_id)
        
#         logger.info(f"Verification queued for document {document.document_id}")
    
#     def _generate_download_url(self, file_path):
#         """Generate presigned URL for S3 download"""
        
#         # If using S3, generate presigned URL
#         # return s3_client.generate_presigned_url(...)
        
#         # For local storage, return direct URL
#         return default_storage.url(file_path)
    
#     def _calculate_missing_documents(self, company_id, financial_year):
#         """Calculate missing documents for a company"""
        
#         missing = {
#             'GSTR_3B': [],
#             'GSTR_9': [],
#             'ITR': [],
#             'FINANCIAL_STATEMENT': []
#         }
        
#         # Check monthly GSTR-3B
#         existing_months = FinancialDocument.objects.filter(
#             company_id=company_id,
#             financial_year=financial_year,
#             document_type='GSTR_3B',
#             period_type='MONTHLY',
#             del_flag=0
#         ).values_list('period_month', flat=True)
        
#         all_months = set(range(1, 13))
#         missing_months = all_months - set(existing_months)
#         missing['GSTR_3B'] = sorted(list(missing_months))
        
#         # Check yearly documents
#         for doc_type in ['GSTR_9', 'ITR', 'FINANCIAL_STATEMENT']:
#             exists = FinancialDocument.objects.filter(
#                 company_id=company_id,
#                 financial_year=financial_year,
#                 document_type=doc_type,
#                 period_type='YEARLY',
#                 del_flag=0
#             ).exists()
            
#             if not exists:
#                 missing[doc_type] = ['Required']
        
#         return missing
    
#     def _compute_file_hash(self, file_obj):
#         sha = hashlib.sha256()
#         for chunk in file_obj.chunks():
#             sha.update(chunk)
#         return sha.hexdigest()
    
#     def _get_latest_version(self, company_id, document_type, start_date, end_date, tag):
#         """
#         Returns the most recent FinancialDocument for the same:
#         - company
#         - document_type
#         - period_start_date
#         - period_end_date
#         - document_tag
#         """
#         return (
#             FinancialDocument.objects
#             .filter(
#                 company_id=company_id,
#                 document_type=document_type,
#                 period_start_date=start_date,
#                 period_end_date=end_date,
#                 document_tag=tag,
#                 del_flag=0
#             )
#             .order_by("-version")
#             .first()
#         )
    
#     def _invalidate_verification(self, document):
#         document.is_verified = False
#         document.verification_source = 'PENDING'
#         document.verification_reference_id = None
#         document.verified_at = None




class FinancialDocumentViewSet(viewsets.ModelViewSet):
    queryset = FinancialDocument.objects.filter(del_flag=0)
    serializer_class = FinancialDocumentSerializer
    lookup_field = "document_id"
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        company = CompanyInformation.objects.filter(
            company_id=self.kwargs.get("company_id"),
            user=self.request.user
        ).first()
        if not company:
            return FinancialDocument.objects.none()
        qs = qs.filter(company_id=self.kwargs["company_id"], del_flag=0)

        fs = DocumentFilterSerializer(data=self.request.query_params)
        if fs.is_valid():
            f = fs.validated_data
            if "document_type" in f: qs = qs.filter(document_type=f["document_type"])
            if "document_tag" in f:  qs = qs.filter(document_tag=f["document_tag"])
            if "financial_year" in f:qs = qs.filter(financial_year=f["financial_year"])
            if "is_verified" in f:   qs = qs.filter(is_verified=f["is_verified"])
            if "period_type" in f:   qs = qs.filter(period_type=f["period_type"])
        return qs.order_by("-created_at")

    # ----------------- helpers (reuse your existing ones if present) -----------------
    def _load_file_from_temp_url(self, file_url):
        """
        Convert a temp MEDIA_URL path (e.g., /media/temp_uploads/xxx.pdf)
        into a Django File object ready to save into model FileField.
        """
        relative_path = file_url
        if relative_path.startswith(settings.MEDIA_URL):
            relative_path = relative_path.replace(settings.MEDIA_URL, "", 1)
        # ensure no leading slash
        relative_path = relative_path.lstrip("/")

        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        if not os.path.exists(full_path):
            return None
        return File(open(full_path, "rb"), name=os.path.basename(full_path))

    def _delete_temp_file(self, file_url):
        relative_path = file_url
        if relative_path.startswith(settings.MEDIA_URL):
            relative_path = relative_path.replace(settings.MEDIA_URL, "", 1)
        relative_path = relative_path.lstrip("/")
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {full_path}: {e}")

    def _compute_file_hash(self, file_obj):
        sha = hashlib.sha256()
        # file_obj may be an InMemoryUploadedFile or django File - ensure reading from start
        file_obj.seek(0)
        for chunk in file_obj.chunks():
            sha.update(chunk)
        file_obj.seek(0)
        return sha.hexdigest()

    def _get_latest_version(self, company_id, document_type, start_date, end_date, tag):
        return (
            FinancialDocument.objects
            .filter(
                company_id=company_id,
                document_type=document_type,
                period_start_date=start_date,
                period_end_date=end_date,
                document_tag=tag,
                del_flag=0
            )
            .order_by("-version")
            .first()
        )

    def _trigger_verification(self, document):
        # keep original implementation (celery etc.) — this is placeholder
        logger.info(f"Verification queued for document {document.document_id}")

    # ----------------- CRUD: create / update / partial_update -----------------
    @transaction.atomic
    def create(self, request, company_id, *args, **kwargs):
        try:
            serializer = FinancialDocumentUploadSerializer(
                data=request.data,
                context={"company_id": company_id}
            )
            serializer.is_valid(raise_exception=True)
            vd = serializer.validated_data

            file_url = vd.pop("file_url", None)
            auto_verify = vd.pop("auto_verify", True)
            vd.pop("period_month", None)
            vd.pop("period_quarter", None)

            file = self._load_file_from_temp_url(file_url)
            if not file:
                return APIResponse.error("Invalid or expired temporary file", status_code=400)

            file_hash = self._compute_file_hash(file)

            document = FinancialDocument(
                company_id=company_id,
                file_hash=file_hash,
                user_id_updated_by=request.user,
                **vd  # version already included by serializer
            )

            document.file_name = file.name
            document.file_size = file.size
            document.mime_type = getattr(file, "content_type", "application/pdf")
            document.file_path.save(file.name, file, save=True)

            self._delete_temp_file(file_url)

            FinancialDocumentService.update_onboarding_state(company_id)

            if auto_verify:
                self._trigger_verification(document)

            return APIResponse.success(
                message="Document uploaded successfully",
                data=FinancialDocumentSerializer(document).data,
                status_code=201
            )
        except ValidationError as e:
            return APIResponse.error(message="Validation failed", data=e.detail, status_code=400)
        except Exception as e:
            logger.error(f"CREATE document failed: {e}", exc_info=True)
            return APIResponse.error(message="Internal server error", status_code=500)

    def update(self, request, company_id, document_id=None, *args, **kwargs):
        try:
            document = self.get_object()
            serializer = FinancialDocumentUploadSerializer(
                data=request.data,
                partial=True,
                context={"company_id": company_id}
            )
            serializer.is_valid(raise_exception=True)
            vd = serializer.validated_data

            file_url = vd.pop("file_url", None)
            auto_verify = vd.pop("auto_verify", True)
            vd.pop("period_month", None)
            vd.pop("period_quarter", None)

            file = None
            if file_url:
                file = self._load_file_from_temp_url(file_url)
                if not file:
                    return APIResponse.error("Invalid or expired temporary file", status_code=400)

            # FILE UPDATE CASE
            if file:
                new_hash = self._compute_file_hash(file)
                if new_hash == document.file_hash:
                    return APIResponse.error(message="Uploaded file is identical to existing version", status_code=400)

                document.file_path.delete(save=False)
                document.file_path.save(file.name, file, save=True)

                document.file_hash = new_hash
                document.file_name = file.name
                document.file_size = file.size
                document.mime_type = getattr(file, "content_type", "application/pdf")

                document.is_verified = False
                document.verified_at = None

                # delete temp
                self._delete_temp_file(file_url)

            # METADATA UPDATE CASE
            for k, v in vd.items():
                setattr(document, k, v)

            document.user_id_updated_by = request.user
            document.save()

            return APIResponse.success(message="Document metadata updated", data=FinancialDocumentSerializer(document).data)

        except ValidationError as e:
            return APIResponse.error(message="Validation failed", data=e.detail, status_code=400)
        except Exception as e:
            logger.error(f"Update failed: {e}", exc_info=True)
            return APIResponse.error(message="Internal server error", status_code=500)

    def partial_update(self, request, company_id, document_id=None, *args, **kwargs):
        try:
            document = self.get_object()
            serializer = FinancialDocumentUploadSerializer(
                data=request.data,
                partial=True,
                context={"company_id": company_id}
            )
            serializer.is_valid(raise_exception=True)
            vd = serializer.validated_data

            file_url = vd.pop("file_url", None)
            auto_verify = vd.pop("auto_verify", True)
            vd.pop("period_month", None)
            vd.pop("period_quarter", None)

            file = None
            if file_url:
                file = self._load_file_from_temp_url(file_url)
                if not file:
                    return APIResponse.error("Invalid or expired temporary file", status_code=400)

            if file:
                new_hash = self._compute_file_hash(file)
                if new_hash == document.file_hash:
                    return APIResponse.error(message="Uploaded file is identical", status_code=400)

                document.file_path.delete(save=False)
                document.file_path.save(file.name, file, save=True)

                document.file_hash = new_hash
                document.file_name = file.name
                document.file_size = file.size
                document.mime_type = getattr(file, "content_type", "application/pdf")

                document.is_verified = False
                document.verified_at = None

                self._delete_temp_file(file_url)

            for k, v in vd.items():
                setattr(document, k, v)

            document.user_id_updated_by = request.user
            document.save()

            return APIResponse.success(message="Document partially updated", data=FinancialDocumentSerializer(document).data)

        except ValidationError as e:
            return APIResponse.error(message="Validation failed", data=e.detail, status_code=400)
        except Exception as e:
            logger.error(f"Partial update failed: {e}", exc_info=True)
            return APIResponse.error(message="Internal server error", status_code=500)

    def destroy(self, request, *args, **kwargs):
        try:
            document = self.get_object()
            document.del_flag = 1
            document.user_id_updated_by = request.user
            document.save()
            company_id = document.company_id
            FinancialDocumentService.update_onboarding_state(company_id)
            return APIResponse.success(message="Document deleted successfully")
        except Exception as e:
            logger.error(f"Delete failed: {e}", exc_info=True)
            return APIResponse.error(message="Internal server error", status_code=500)

    # ----------------- Bulk upload (only JSON, file_url required for each doc) -----------------
    @action(detail=False, methods=["post"])
    @transaction.atomic
    def bulk_upload(self, request, company_id):
        try:
            bulk = BulkUploadSerializer(data=request.data, context={"company_id": company_id})
            bulk.is_valid(raise_exception=True)
            documents = bulk.validated_data["documents"]

            results = {"success": [], "failed": []}

            for idx, doc_meta in enumerate(documents):
                try:
                    # Build payload for single-document serializer
                    payload = dict(doc_meta)  # shallow copy
                    serializer = FinancialDocumentUploadSerializer(data=payload, context={"company_id": company_id})
                    serializer.is_valid(raise_exception=True)
                    vd = serializer.validated_data

                    file_url = vd.pop("file_url", None)
                    auto_verify = vd.pop("auto_verify", True)
                    vd.pop("period_month", None)
                    vd.pop("period_quarter", None)

                    # load file from temp url
                    file = self._load_file_from_temp_url(file_url)
                    if not file:
                        results["failed"].append({"index": idx, "error": "Invalid or expired temp file"})
                        continue

                    file_hash = self._compute_file_hash(file)

                    latest = self._get_latest_version(
                        company_id,
                        vd["document_type"],
                        vd["period_start_date"],
                        vd["period_end_date"],
                        vd["document_tag"]
                    )

                    if latest and latest.file_hash == file_hash:
                        results["failed"].append({"index": idx, "error": "File already uploaded"})
                        continue

                    document = FinancialDocument(
                        company_id=company_id,
                        file_hash=file_hash,
                        user_id_updated_by=request.user,
                        **vd
                    )

                    document.file_name = file.name
                    document.file_size = file.size
                    document.mime_type = getattr(file, "content_type", "application/pdf")

                    document.file_path.save(file.name, file, save=True)

                    # remove temp
                    self._delete_temp_file(file_url)

                    if auto_verify:
                        self._trigger_verification(document)

                    results["success"].append({"index": idx, "document_id": document.document_id})

                except ValidationError as e:
                    results["failed"].append({"index": idx, "errors": e.detail})
                except Exception as e:
                    logger.error(f"Bulk upload item failed at index {idx}: {e}", exc_info=True)
                    results["failed"].append({"index": idx, "error": str(e)})

            FinancialDocumentService.update_onboarding_state(company_id)
            return APIResponse.success(message=f"{len(results['success'])} succeeded, {len(results['failed'])} failed", data=results)

        except ValidationError as e:
            return APIResponse.error(message="Validation failed", data=e.detail, status_code=400)
        except Exception as e:
            logger.error(f"Bulk upload failed: {e}", exc_info=True)
            return APIResponse.error(message="Internal server error", status_code=500)

    # ----------------- Bulk update (metadata or file via file_url) -----------------
    @action(detail=False, methods=["patch"])
    @transaction.atomic
    def bulk_update(self, request, company_id):
        try:
            bulk = BulkUpdateSerializer(data=request.data)
            bulk.is_valid(raise_exception=True)
            updates = bulk.validated_data["updates"]

            if not updates:
                return APIResponse.error(message="No update payloads provided", status_code=400)

            results = {"success": [], "failed": []}
            needs_state_update = False

            for idx, item in enumerate(updates):
                try:
                    doc_id = item.get("document_id")
                    metadata = item.get("metadata", {})

                    document = FinancialDocument.objects.filter(
                        document_id=doc_id,
                        company_id=company_id,
                        del_flag=0
                    ).first()

                    if not document:
                        results["failed"].append({"index": idx, "error": "Document not found"})
                        continue

                    payload = dict(metadata)  # copy
                    file_url = payload.get("file_url")

                    serializer = FinancialDocumentUploadSerializer(data=payload, partial=True, context={"company_id": company_id})
                    if not serializer.is_valid():
                        results["failed"].append({"index": idx, "errors": serializer.errors})
                        continue

                    vd = serializer.validated_data
                    vd.pop("period_month", None)
                    vd.pop("period_quarter", None)
                    vd.pop("auto_verify", None)

                    # If file_url present → load file
                    if file_url:
                        file = self._load_file_from_temp_url(file_url)
                        if not file:
                            results["failed"].append({"index": idx, "error": "Invalid or expired temporary file"})
                            continue

                        new_hash = self._compute_file_hash(file)
                        if new_hash != document.file_hash:
                            document.file_hash = new_hash
                            document.file_name = file.name
                            document.file_size = file.size
                            document.mime_type = getattr(file, "content_type", "application/pdf")
                            document.file_path.save(file.name, file, save=True)

                            # delete temp
                            self._delete_temp_file(file_url)

                            document.is_verified = False
                            document.verified_at = None

                    # metadata update
                    for k, v in vd.items():
                        setattr(document, k, v)

                    document.save()

                    if any(field in vd for field in [
                        "financial_year",
                        "period_type",
                        "period_start_date",
                        "period_end_date",
                        "period_month",
                        "period_quarter",
                        "document_type",
                    ]):
                        needs_state_update = True

                    results["success"].append({"index": idx, "document_id": doc_id})

                except ValidationError as e:
                    results["failed"].append({"index": idx, "errors": e.detail})
                except Exception as e:
                    logger.error(f"Bulk update item {idx} failed: {e}", exc_info=True)
                    results["failed"].append({"index": idx, "error": str(e)})

            if needs_state_update:
                FinancialDocumentService.update_onboarding_state(company_id)

            return APIResponse.success(message=f"{len(results['success'])} succeeded, {len(results['failed'])} failed", data=results)

        except ValidationError as e:
            return APIResponse.error(message="Validation failed", data=e.detail, status_code=400)
        except Exception as e:
            logger.error(f"Bulk update failed: {e}", exc_info=True)
            return APIResponse.error(message="Internal server error", status_code=500)

    @action(detail=True, methods=['get'])
    def download(self, request, company_id, pk=None):
        if not company_id:
            return APIResponse.error(
                message="Company not found for this",
                status_code=status.HTTP_404_NOT_FOUND
            )

        document = self.get_object()
        if not document.file_path:
            return APIResponse.error(
                message="File not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        return APIResponse.success(
            message="File fetched successfully",
            data={
                "download_url": document.file_path.url,   # works for local or S3
                "file_name": document.file_name,
                "file_size": document.file_size
            },
            status_code=status.HTTP_200_OK
        )


    @action(detail=False, methods=['get'])
    def missing_documents(self, request, company_id):
        if not company_id:
            return APIResponse.error(
                message="Company not found for this",
                status_code=status.HTTP_404_NOT_FOUND
            )

        company = get_object_or_404(CompanyInformation, pk=company_id)
        financial_year = request.query_params.get('financial_year')

        if not company or not financial_year:
            return APIResponse.error(
                message="company and financial_year are required",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # FY start year, e.g., "FY2023-24" -> 2023
        fy_num = int(financial_year.replace('FY', '').replace(' ', '').split('-')[0])

        # months in FY order: Apr..Dec (4..12) then Jan..Mar (1..3)
        fy_months = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]

        existing = FinancialDocument.objects.filter(
            company_id=company,
            financial_year=financial_year,
            document_type=DocumentType.GSTR_3B,
            period_type=PeriodType.MONTHLY,
            del_flag=0
        ).values_list('period_start_date', flat=True)

        existing_months = set(d.month for d in existing)
        missing_months = [m for m in fy_months if m not in existing_months]

        # yearly docs
        yearly_missing = {}
        for dt in [DocumentType.GSTR_9, DocumentType.ITR, DocumentType.FINANCIAL_STATEMENT]:
            exists = FinancialDocument.objects.filter(
                company_id=company,
                financial_year=financial_year,
                document_type=dt,
                period_type=PeriodType.YEARLY,
                del_flag=0
            ).exists()
            if not exists:
                yearly_missing[dt] = ["Required"]

        return APIResponse.success(
            message="Missing documents fetched successfully",
            data={
                "GSTR_3B": [month_name[m] for m in missing_months],
                **yearly_missing
            },
            status_code=status.HTTP_200_OK
        )
