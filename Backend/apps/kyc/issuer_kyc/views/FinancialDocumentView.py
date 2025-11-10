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
# from .services import DocumentVerificationService
import hashlib
import logging

logger = logging.getLogger(__name__)





    # @transaction.atomic
    # def create(self, request, company_id,*args, **kwargs):
    #     if not company_id:
    #         return Response({
    #             "status": "error",
    #             "message": "Company not found for this",
    #         }, status=404)
    #     upload = FinancialDocumentUploadSerializer(data=request.data,context={"company_id": company_id})
    #     upload.is_valid(raise_exception=True)
    #     vd = upload.validated_data
    #     file = vd.pop('file')
    #     auto_verify = vd.pop('auto_verify', True)

    #     # compute hash
    #     file_hash = self._compute_file_hash(file)

    #     # get latest version
    #     latest = self._get_latest_version(
    #         company_id,
    #         vd['document_type'],
    #         vd['period_start_date'],
    #         vd['period_end_date'],
    #         vd['document_tag']
    #     )

    #     if latest and latest.file_hash == file_hash:
    #         return Response({
    #             'success': False,
    #             'message': 'This exact file is already uploaded',
    #             'document_id': latest.document_id,
    #             'version': latest.version
    #         }, status=status.HTTP_400_BAD_REQUEST)

    #     version = latest.version + 1 if latest else 1

    #     document = FinancialDocument(
    #         company_id=company_id,
    #         document_type=vd['document_type'],
    #         document_tag=vd['document_tag'],
    #         financial_year=vd['financial_year'],
    #         period_type=vd['period_type'],
    #         period_start_date=vd['period_start_date'],
    #         period_end_date=vd['period_end_date'],
    #         period_code=vd.get('period_code'),
    #         version=version,

    #         file_hash=file_hash,

    #         auditor_name=vd.get('auditor_name'),
    #         audit_report_date=vd.get('audit_report_date'),
    #         audit_firm_name=vd.get('audit_firm_name'),
            

            
    #         # user_id_updated_by=request.user,
    #     )

    #     document.file_name = file.name
    #     document.file_size = file.size
    #     document.mime_type = getattr(file, 'content_type', 'application/pdf')

    #     document.file_path.save(file.name, file, save=True)

    #     if auto_verify:
    #         self._trigger_verification(document)

    #     return Response({
    #         'success': True,
    #         'message': 'Document uploaded successfully',
    #         'data': FinancialDocumentSerializer(document).data,
    #         'verification_triggered': auto_verify
    #     }, status=status.HTTP_201_CREATED)

    
    # @action(detail=False, methods=['post'])
    # @transaction.atomic
    # def bulk_upload(self, request,company_id):
    #     if not company_id:
    #         return Response({
    #             "status": "error",
    #             "message": "Company not found for this",
    #         }, status=404)
    #     bulk = BulkUploadSerializer(data=request.data,context={"company_id":company_id})
    #     bulk.is_valid(raise_exception=True)

    #     docs = bulk.validated_data['documents']

    #     results = {'success': [], 'failed': []}

    #     for idx, payload in enumerate(docs, start=1):
    #         item = dict(payload)
    #         item['company'] = company_id

    #         upload = FinancialDocumentUploadSerializer(data=item)
    #         if not upload.is_valid():
    #             results['failed'].append({'index': idx, 'errors': upload.errors})
    #             continue

    #         vd = upload.validated_data
    #         file = vd.pop('file')
    #         auto_verify = vd.pop('auto_verify', True)

    #         try:
    #             file_hash = self._compute_file_hash(file)

    #             latest = self._get_latest_version(
    #                 company_id,
    #                 vd['document_type'],
    #                 vd['period_start_date'],
    #                 vd['period_end_date'],
    #                 vd['document_tag']
    #             )

    #             if latest and latest.file_hash == file_hash:
    #                 results['failed'].append({
    #                     'index': idx,
    #                     'error': 'File already uploaded (duplicate)'
    #                 })
    #                 continue

    #             version = latest.version + 1 if latest else 1

    #             document = FinancialDocument(
    #                 company_id=company_id,
    #                 document_type=vd['document_type'],
    #                 document_tag=vd['document_tag'],
    #                 financial_year=vd['financial_year'],
    #                 period_type=vd['period_type'],
    #                 period_start_date=vd['period_start_date'],
    #                 period_end_date=vd['period_end_date'],
    #                 period_code=vd.get('period_code'),
    #                 version=version,
    #                 file_hash=file_hash,
    #                 auditor_name=vd.get('auditor_name'),
    #                 audit_report_date=vd.get('audit_report_date'),
    #                 audit_firm_name=vd.get('audit_firm_name'),
                  
                    
    #                 # user_id_updated_by=request.user,
    #             )

    #             document.file_name = file.name
    #             document.file_size = file.size
    #             document.mime_type = getattr(file, 'content_type', 'application/pdf')
    #             document.file_path.save(file.name, file, save=True)

    #             if auto_verify:
    #                 self._trigger_verification(document)

    #             results['success'].append({
    #                 'index': idx,
    #                 'document_id': document.document_id,
    #                 'file_name': document.file_name,
    #                 'version': document.version
    #             })
    #         except Exception as e:
    #             logger.exception("Bulk upload failed")
    #             results['failed'].append({'index': idx, 'error': str(e)})

    #     return Response({
    #         'success': True,
    #         'message': f"{len(results['success'])} succeeded, {len(results['failed'])} failed",
    #         'results': results
    #     }, status=status.HTTP_200_OK)
    
    # def update(self, request,company_id, *args, **kwargs):
    #     if not company_id:
    #         return Response({
    #             "status": "error",
    #             "message": "Company not found for this",
    #         }, status=404)
    #     document = self.get_object()

    #     upload = FinancialDocumentUploadSerializer(data=request.data, partial=True)
    #     upload.is_valid(raise_exception=True)
    #     vd = upload.validated_data

    #     file = vd.pop('file', None)
    #     auto_verify = vd.pop('auto_verify', True)

    #     if file:
    #         new_hash = self._compute_file_hash(file)

    #         if new_hash == document.file_hash:
    #             return Response({
    #                 'success': False,
    #                 'message': 'Uploaded file is identical to existing version'
    #             }, status=status.HTTP_400_BAD_REQUEST)

    #         new_version = document.version + 1

    #         new_doc = FinancialDocument.objects.create(
    #             company=document.company,
    #             document_type=document.document_type,
    #             document_tag=document.document_tag,
    #             financial_year=document.financial_year,
    #             period_type=document.period_type,
    #             period_start_date=document.period_start_date,
    #             period_end_date=document.period_end_date,
    #             period_code=document.period_code,
    #             version=new_version,
    #             file_hash=new_hash,
    #             auditor_name=vd.get('auditor_name', document.auditor_name),
    #             audit_report_date=vd.get('audit_report_date', document.audit_report_date),
    #             audit_firm_name=vd.get('audit_firm_name', document.audit_firm_name),
                
                
    #             # user_id_updated_by=request.user,
    #         )

    #         new_doc.file_name = file.name
    #         new_doc.file_size = file.size
    #         new_doc.mime_type = getattr(file, 'content_type', 'application/pdf')
    #         new_doc.file_path.save(file.name, file, save=True)

    #         self._invalidate_verification(new_doc)

    #         if auto_verify:
    #             self._trigger_verification(new_doc)

    #         return Response({
    #             'success': True,
    #             'message': 'New document version created',
    #             'data': FinancialDocumentSerializer(new_doc).data
    #         })

    #     for key, value in vd.items():
    #         setattr(document, key, value)

    #     document.user_id_updated_by = request.user
    #     document.save()

    #     return Response({
    #         'success': True,
    #         'message': 'Document metadata updated',
    #         'data': FinancialDocumentSerializer(document).data
    #     })

    # def destroy(self, request, *args, **kwargs):
    #     """Soft delete document"""
        
    #     document = self.get_object()
    #     document.del_flag = 1
    #     document.user_id_updated_by = request.user
    #     document.save()
        
    #     return Response({
    #         'success': True,
    #         'message': 'Document deleted successfully'
    #     }, status=status.HTTP_200_OK)
    
    # @action(detail=True, methods=['post'])
    # def verify(self, request, pk=None):
    #     """
    #     Manually trigger verification for a document
        
    #     POST /api/documents/{id}/verify/
    #     {
    #         "verification_provider": "GST_PORTAL"  # Optional
    #     }
    #     """
        
    #     document = self.get_object()
    #     verification_provider = request.data.get('verification_provider')
        
    #     try:
    #         result = DocumentVerificationService.verify_document(
    #             document,
    #             provider=verification_provider,
    #             user=request.user
    #         )
            
    #         return Response({
    #             'success': True,
    #             'message': 'Verification completed',
    #             'data': {
    #                 'is_verified': result['is_verified'],
    #                 'verification_source': result['verification_source'],
    #                 'verification_reference_id': result['verification_reference_id'],
    #                 'verified_at': result['verified_at']
    #             }
    #         }, status=status.HTTP_200_OK)
        
    #     except Exception as e:
    #         logger.error(f"Verification failed for document {pk}: {str(e)}")
    #         return Response({
    #             'success': False,
    #             'message': 'Verification failed',
    #             'error': str(e)
    #         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



def api_response(status: str, message: str, data=None, http_status=200):
    resp = {
        "status": status,
        "message": message
    }

    # attach payload correctly
    if data is not None:
        if status == "error":
            resp["errors"] = data       # errors go here
        else:
            resp["data"] = data         # success payload goes here

    return Response(resp, status=http_status)

class FinancialDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing financial documents
    
    Endpoints:
    - POST /api/documents/ - Upload single document
    - POST /api/documents/bulk_upload/ - Upload multiple documents
    - GET /api/documents/ - List all documents (with filters)
    - GET /api/documents/{id}/ - Get specific document
    - PUT /api/documents/{id}/ - Update document
    - DELETE /api/documents/{id}/ - Soft delete document
    - POST /api/documents/{id}/verify/ - Trigger verification
    - GET /api/documents/{id}/download/ - Download document
    - GET /api/documents/missing_documents/ - Get missing documents report
    """
    
    queryset = FinancialDocument.objects.filter(del_flag=0)
    serializer_class = FinancialDocumentSerializer
    lookup_field = "document_id"
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        qs = super().get_queryset()
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


       
    def retrieve(self, request, company_id, document_id=None, *args, **kwargs):
        try:
            document = self.get_object()
            serializer = FinancialDocumentSerializer(document)

            return api_response(
                status="success",
                message="Document fetched successfully",
                data=serializer.data
            )
        
        except Http404:
            return api_response("error", f"Document not found", http_status=404)
        
        except Exception as e:
            logger.error(f"Retrieve document failed: {e}", exc_info=True)
            return api_response("error", "Internal server error", http_status=500)

    def list(self, request, company_id, *args, **kwargs):
        try:
            qs = self.filter_queryset(self.get_queryset())

            serializer = FinancialDocumentSerializer(qs, many=True)
            return api_response(
                status="success",
                message="Documents fetched successfully",
                data=serializer.data
            )
        except Exception as e:
            logger.error(f"List documents failed: {e}", exc_info=True)
            return api_response("error", "Internal server error", http_status=500)


    @transaction.atomic
    def create(self, request, company_id, *args, **kwargs):
        try:
            if not company_id:
                return api_response("error", "company_id missing", http_status=400)

            serializer = FinancialDocumentUploadSerializer(
                data=request.data,
                context={"company_id": company_id}
            )
            serializer.is_valid(raise_exception=True)
            vd = serializer.validated_data

            file = vd.pop("file")
            auto_verify = vd.pop("auto_verify", True)

            file_hash = self._compute_file_hash(file)

            latest = self._get_latest_version(
                company_id,
                vd["document_type"],
                vd["period_start_date"],
                vd["period_end_date"],
                vd["document_tag"],
            )

            if latest and latest.file_hash == file_hash:
                return api_response(
                    "error",
                    "This exact file is already uploaded",
                    data={
                        "document_id": latest.document_id,
                        "version": latest.version
                    },
                    http_status=400
                )

            version = latest.version + 1 if latest else 1

            document = FinancialDocument(
                company_id=company_id,
                version=version,
                file_hash=file_hash,
                user_id_updated_by=request.user,
                **vd,
            )

            document.file_name = file.name
            document.file_size = file.size
            document.mime_type = getattr(file, "content_type", "application/pdf")
            document.file_path.save(file.name, file, save=True)

            if auto_verify:
                logger.info(f"Triggering verification for document {document.document_id}")
                self._trigger_verification(document)

            return api_response(
                "success",
                "Document uploaded successfully",
                data={
                    "verification_triggered": auto_verify,
                    **FinancialDocumentSerializer(document).data
                },
                http_status=201
            )
        except ValidationError as e:
            # return proper serializer errors
            return api_response(
                "error",
                "Validation failed",
                data=e.detail,               # serializer error dict
                http_status=400
            )
        except Exception as e:
            logger.error(f"CREATE document failed: {e}", exc_info=True)
            return api_response("error", "Internal server error", http_status=500)
        
   
    def update(self, request, company_id,document_id=None, *args, **kwargs):
        try:
            document = self.get_object()

            serializer = FinancialDocumentUploadSerializer(
                data=request.data, partial=True,
                context={"company_id": company_id}
            )
            serializer.is_valid(raise_exception=True)
            vd = serializer.validated_data

            file = vd.pop("file", None)
            auto_verify = vd.pop("auto_verify", True)

            # CASE 1 — new version due to file change
            if file:
                new_hash = self._compute_file_hash(file)

                if new_hash == document.file_hash:
                    return api_response(
                        "error",
                        "Uploaded file is identical to existing version",
                        http_status=400
                    )

                # replace PDF file
                document.file_path.delete(save=False)
                document.file_path.save(file.name, file, save=True)

                # update meta
                document.file_hash = new_hash
                document.file_name = file.name
                document.file_size = file.size
                document.mime_type = getattr(file, "content_type", "application/pdf")

                # reset verification (because file changed)
                document.is_verified = False
                document.verified_at = None

            # CASE 2 — metadata update only
            for k, v in vd.items():
                setattr(document, k, v)

            document.user_id_updated_by = request.user
            document.save()


            return api_response(
                "success",
                "Document metadata updated",
                data=FinancialDocumentSerializer(document).data
            )
        except ValidationError as e:
            # return proper serializer errors
            return api_response(
                "error",
                "Validation failed",
                data=e.detail,               # serializer error dict
                http_status=400
            )
        
        except Exception as e:
            logger.error(f"Update failed: {e}", exc_info=True)
            return api_response("error", "Internal server error", http_status=500)


    def partial_update(self, request, company_id, document_id=None, *args, **kwargs):
        try:
            document = self.get_object()

            serializer = FinancialDocumentUploadSerializer(
                data=request.data,
                partial=True,                       # partial update
                context={"company_id": company_id}
            )
            serializer.is_valid(raise_exception=True)
            vd = serializer.validated_data

            file = vd.pop("file", None)
            auto_verify = vd.pop("auto_verify", True)

            # FILE update (optional)
            if file:
                new_hash = self._compute_file_hash(file)

                if new_hash == document.file_hash:
                    return api_response(
                        "error",
                        "Uploaded file is identical to existing version",
                        http_status=400
                    )

                # replace file
                document.file_path.delete(save=False)
                document.file_path.save(file.name, file, save=True)

                document.file_hash = new_hash
                document.file_name = file.name
                document.file_size = file.size
                document.mime_type = getattr(file, "content_type", "application/pdf")

                document.is_verified = False
                document.verified_at = None

            # METADATA update (only fields provided)
            for k, v in vd.items():
                setattr(document, k, v)

            document.user_id_updated_by = request.user
            document.save()

            return api_response(
                "success",
                "Document partially updated",
                data=FinancialDocumentSerializer(document).data
            )

        except ValidationError as e:
            return api_response(
                "error",
                "Validation failed",
                data=e.detail,
                http_status=400
            )

        except Exception as e:
            logger.error(f"Partial update failed: {e}", exc_info=True)
            return api_response("error", "Internal server error", http_status=500)
   
    def destroy(self, request, *args, **kwargs):
        try:
            document = self.get_object()
            document.del_flag = 1
            document.user_id_updated_by = request.user
            document.save()

            return api_response("success", "Document deleted successfully")
        
        except Exception as e:
            logger.error(f"Delete failed: {e}", exc_info=True)
            return api_response("error", "Internal server error", http_status=500)
    

    #--------------- Bulk Operations ------------
    
    @action(detail=False, methods=["post"])
    @transaction.atomic
    def bulk_upload(self, request, company_id):
        try:
            if not company_id:
                return api_response("error", "company_id missing", http_status=400)

            bulk = BulkUploadSerializer(
                data=request.data,
                context={"company_id": company_id}
            )
            bulk.is_valid(raise_exception=True)

            documents = bulk.validated_data["documents"]
            files = bulk.validated_data["files"]

            results = {"success": [], "failed": []}

            for idx, doc_meta in enumerate(documents):
                try:
                    file = files[idx]

                    payload = {
                        **doc_meta,
                        "file": file,
                        "auto_verify": doc_meta.get("auto_verify", True)
                    }

                    serializer = FinancialDocumentUploadSerializer(
                        data=payload,
                        context={"company_id": company_id}
                    )

                    if not serializer.is_valid():
                        results["failed"].append({
                            "index": idx,
                            "errors": serializer.errors
                        })
                        continue

                    vd = serializer.validated_data
                    vd.pop("period_month", None)
                    vd.pop("period_quarter", None)
                    auto_verify = vd.pop("auto_verify", True)
                    file = vd.pop("file")

                    file_hash = self._compute_file_hash(file)

                    latest = self._get_latest_version(
                        company_id,
                        vd["document_type"],
                        vd["period_start_date"],
                        vd["period_end_date"],
                        vd["document_tag"]
                    )

                    if latest and latest.file_hash == file_hash:
                        results["failed"].append({
                            "index": idx,
                            "error": "File already uploaded"
                        })
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

                    if auto_verify:
                        self._trigger_verification(document)

                    results["success"].append({
                        "index": idx,
                        "document_id": document.document_id,
                        "file_name": document.file_name
                    })

                except Exception as e:
                    logger.error(f"Bulk item {idx} failed: {e}", exc_info=True)
                    results["failed"].append({"index": idx, "error": str(e)})

            return api_response(
                "success",
                f"{len(results['success'])} succeeded, {len(results['failed'])} failed",
                data=results
            )

        except ValidationError as e:
            return api_response(
                "error",
                "Validation failed",
                errors=e.detail,
                http_status=400
            )

        except Exception as e:
            logger.error(f"Bulk upload failed: {e}", exc_info=True)
            return api_response("error", "Internal server error", http_status=500)

    @action(detail=False, methods=["patch"])
    @transaction.atomic
    def bulk_update(self, request, company_id):
        try:
            
            bulk = BulkUpdateSerializer(data=request.data)
            bulk.is_valid(raise_exception=True)

            updates = bulk.validated_data["updates"]

            if not updates:
                return api_response("error", "No update payloads provided", http_status=400)
            

            results = {"success": [], "failed": []}

            
            for idx, item in enumerate(updates):
                try:
                    doc_id = item.get("document_id")
                    metadata = item.get("metadata", {})

                    file = request.FILES.get(f"file_{doc_id}")

                    document = FinancialDocument.objects.filter(
                        document_id=doc_id,
                        company_id=company_id,
                        del_flag=0
                    ).first()

                    if not document:
                        results["failed"].append({
                            "index": idx,
                            "error": "Document not found"
                        })
                        continue

                    # build payload for serializer
                    payload = metadata.copy()
                    if file:
                        payload["file"] = file

                    # validate metadata using FINANCIAL document serializer
                    serializer = FinancialDocumentUploadSerializer(
                        data=payload,
                        partial=True,
                        context={"company_id": company_id}
                    )

                    if not serializer.is_valid():
                        results["failed"].append({
                            "index": idx,
                            "errors": serializer.errors
                        })
                        continue

                    vd = serializer.validated_data
                    vd.pop("period_month", None)
                    vd.pop("period_quarter", None)
                    vd.pop("auto_verify", None)

                    # FILE UPDATE
                    if file:
                        new_hash = self._compute_file_hash(file)

                        if new_hash != document.file_hash:
                            document.file_hash = new_hash
                            document.file_name = file.name
                            document.file_size = file.size
                            document.mime_type = getattr(file, "content_type", "application/pdf")
                            document.file_path.save(file.name, file, save=True)

                    # METADATA UPDATE
                    for k, v in vd.items():
                        setattr(document, k, v)

                    document.save()

                    results["success"].append({"index": idx, "document_id": doc_id})

                except Exception as e:
                    logger.error(f"Bulk update item {idx} failed: {e}", exc_info=True)
                    results["failed"].append({"index": idx, "error": str(e)})

            return api_response(
                "success",
                f"{len(results['success'])} succeeded, {len(results['failed'])} failed",
                data=results
            )

        except Exception as e:
            logger.error(f"Bulk update failed: {e}", exc_info=True)
            return api_response("error", "Internal server error", http_status=500)


    @action(detail=False, methods=["delete"])
    @transaction.atomic
    def bulk_delete(self, request, company_id):
        try:
            serializer = BulkDeleteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            doc_ids = serializer.validated_data["document_ids"]
            results = {"success": [], "failed": []}

            for idx, doc_id in enumerate(doc_ids):
                try:
                    document = FinancialDocument.objects.get(
                        document_id=doc_id,
                        company_id=company_id,
                        del_flag=0
                    )

                    document.del_flag = 1
                    document.save()

                    results["success"].append({"document_id": doc_id})

                except FinancialDocument.DoesNotExist:
                    results["failed"].append({
                        "document_id": doc_id,
                        "error": "Document not found"
                    })
                except Exception as e:
                    results["failed"].append({
                        "document_id": doc_id,
                        "error": str(e)
                    })

            return api_response(
                "success",
                f"{len(results['success'])} succeeded, {len(results['failed'])} failed",
                data=results
            )

        except Exception as e:
            logger.error(f"Bulk delete failed: {e}", exc_info=True)
            return api_response("error", "Internal server error", http_status=500)


    @action(detail=True, methods=['get'])
    def download(self, request,company_id, pk=None):
        if not company_id:
            return Response({
                "status": "error",
                "message": "Company not found for this",
            }, status=404)
        document = self.get_object()
        if not document.file_path:
            return Response({'success': False, 'message': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'success': True,
            'data': {
                'download_url': document.file_path.url,   # works for local or S3
                'file_name': document.file_name,
                'file_size': document.file_size
            }
        }, status=status.HTTP_200_OK)

    
    @action(detail=False, methods=['get'])
    def missing_documents(self, request,company_id):
        if not company_id:
            return Response({
                "status": "error",
                "message": "Company not found for this",
            }, status=404)
        company = get_object_or_404(CompanyInformation,pk=company_id)
        financial_year = request.query_params.get('financial_year')
        if not company or not financial_year:
            return Response({'success': False, 'message': 'company and financial_year are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        # FY start year, e.g., "FY2023-24" -> 2023
        fy_num = int(financial_year.replace('FY', '').replace(' ', '').split('-')[0])

        # months in FY order: Apr..Dec (4..12) then Jan..Mar (1..3)
        fy_months = [4,5,6,7,8,9,10,11,12,1,2,3]

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
                yearly_missing[dt] = ['Required']

        return Response({
            'success': True,
            'data': {
                'GSTR_3B': [month_name[m] for m in missing_months],
                **yearly_missing
            }
        }, status=status.HTTP_200_OK)
    
    
    #------------- Helper methods ----------------
    def _upload_file_to_storage(self, file, company_id, doc_type, fy):
        """Upload file to S3 or local storage"""
        
        # Generate unique file path
        file_path = f"financial_docs/{company_id}/{fy}/{doc_type}/{timezone.now().timestamp()}_{file.name}"
        
        # Upload to storage
        saved_path = default_storage.save(file_path, file)
        
        return saved_path
    
    def _trigger_verification(self, document):
        """Trigger async verification (using Celery or similar)"""
        
        # Import here to avoid circular imports
        # from celery_task.financial_document_tasks import verify_document_async
        
        # # Queue verification task
        # verify_document_async.delay(document.document_id)
        
        logger.info(f"Verification queued for document {document.document_id}")
    
    def _generate_download_url(self, file_path):
        """Generate presigned URL for S3 download"""
        
        # If using S3, generate presigned URL
        # return s3_client.generate_presigned_url(...)
        
        # For local storage, return direct URL
        return default_storage.url(file_path)
    
    def _calculate_missing_documents(self, company_id, financial_year):
        """Calculate missing documents for a company"""
        
        missing = {
            'GSTR_3B': [],
            'GSTR_9': [],
            'ITR': [],
            'FINANCIAL_STATEMENT': []
        }
        
        # Check monthly GSTR-3B
        existing_months = FinancialDocument.objects.filter(
            company_id=company_id,
            financial_year=financial_year,
            document_type='GSTR_3B',
            period_type='MONTHLY',
            del_flag=0
        ).values_list('period_month', flat=True)
        
        all_months = set(range(1, 13))
        missing_months = all_months - set(existing_months)
        missing['GSTR_3B'] = sorted(list(missing_months))
        
        # Check yearly documents
        for doc_type in ['GSTR_9', 'ITR', 'FINANCIAL_STATEMENT']:
            exists = FinancialDocument.objects.filter(
                company_id=company_id,
                financial_year=financial_year,
                document_type=doc_type,
                period_type='YEARLY',
                del_flag=0
            ).exists()
            
            if not exists:
                missing[doc_type] = ['Required']
        
        return missing
    
    def _compute_file_hash(self, file_obj):
        sha = hashlib.sha256()
        for chunk in file_obj.chunks():
            sha.update(chunk)
        return sha.hexdigest()
    
    def _get_latest_version(self, company_id, document_type, start_date, end_date, tag):
        """
        Returns the most recent FinancialDocument for the same:
        - company
        - document_type
        - period_start_date
        - period_end_date
        - document_tag
        """
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
    
    def _invalidate_verification(self, document):
        document.is_verified = False
        document.verification_source = 'PENDING'
        document.verification_reference_id = None
        document.verified_at = None
