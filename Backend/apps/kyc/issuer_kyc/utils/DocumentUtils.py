# import mimetypes
# from typing import Tuple, Dict, List
# from ..models.CompanyDocumentModel import CompanyDocument


# class DocumentTypeDetector:
#     """Utility class for detecting document types from files"""
    
#     EXTENSION_MAP = {
#         'pdf': 'PDF',
#         'jpeg': 'JPEG',
#         'jpg': 'JPG',
#         'png': 'PNG',
#     }
    
#     MIME_TYPE_MAP = {
#         'application/pdf': 'PDF',
#         'image/jpeg': 'JPEG',
#         'image/jpg': 'JPG',
#         'image/png': 'PNG',
#     }
    
#     @classmethod
#     def detect_from_filename(cls, filename: str) -> str:
#         """Detect document type from filename extension"""
#         ext = filename.rsplit('.', 1)[-1].lower()
#         return cls.EXTENSION_MAP.get(ext, 'PDF')
    
#     @classmethod
#     def detect_from_mime(cls, mime_type: str) -> str:
#         """Detect document type from MIME type"""
#         return cls.MIME_TYPE_MAP.get(mime_type, 'PDF')
    
#     @classmethod
#     def get_allowed_extensions(cls) -> List[str]:
#         """Get list of allowed file extensions"""
#         return list(cls.EXTENSION_MAP.keys())


# class DocumentStatusChecker:
#     """Utility class for checking document upload status"""
    
#     @staticmethod
#     def get_company_document_status(company_id: int) -> Dict:
#         """
#         Get comprehensive document status for a company.
#         Returns dict with upload status and missing documents.
#         """
#         mandatory_docs = set(CompanyDocument.MANDATORY_DOCUMENTS)
        
#         # Get uploaded documents (avoid N+1)
#         uploaded = CompanyDocument.objects.filter(
#             company_id=company_id,
#             del_flag=0
#         ).values('document_name', 'document_id', 'uploaded_at', 'is_verified')
        
#         uploaded_names = {doc['document_name'] for doc in uploaded}
#         uploaded_mandatory = uploaded_names & mandatory_docs
        
#         missing = list(mandatory_docs - uploaded_names)
#         all_mandatory_complete = len(missing) == 0
        
#         return {
#             'total_documents': len(uploaded),
#             'mandatory_documents': len(mandatory_docs),
#             'uploaded_mandatory': len(uploaded_mandatory),
#             'all_mandatory_uploaded': all_mandatory_complete,
#             'missing_documents': missing,
#             'uploaded_documents': list(uploaded)
#         }
    
#     @staticmethod
#     def get_document_name_display(doc_name: str) -> str:
#         """Get display name for document code"""
#         doc_map = dict(CompanyDocument.DOCUMENT_NAMES)
#         return doc_map.get(doc_name, doc_name)


# class DocumentValidator:
#     """Utility class for document validation"""
    
#     MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
#     ALLOWED_MIME_TYPES = ['application/pdf', 'image/jpeg', 'image/png']
    
#     @classmethod
#     def validate_file(cls, file) -> Tuple[bool, str]:
#         """
#         Validate uploaded file.
#         Returns (is_valid, error_message)
#         """
#         # Check file size
#         if file.size > cls.MAX_FILE_SIZE:
#             return False, f"File size exceeds 5MB limit"
        
#         # Check MIME type
#         if hasattr(file, 'content_type'):
#             if file.content_type not in cls.ALLOWED_MIME_TYPES:
#                 return False, "Invalid file type. Allowed: PDF, JPEG, PNG"
        
#         # Check extension
#         ext = file.name.split('.')[-1].lower()
#         if ext not in DocumentTypeDetector.get_allowed_extensions():
#             return False, f"Invalid file extension: .{ext}"
        
#         return True, None
    
#     @classmethod
#     def validate_document_uniqueness(cls, company_id: int, document_name: str) -> Tuple[bool, str]:
#         """
#         Check if document already exists for company.
#         Returns (is_valid, error_message)
#         """
#         exists = CompanyDocument.objects.filter(
#             company_id=company_id,
#             document_name=document_name,
#             del_flag=0
#         ).exists()
        
#         if exists:
#             doc_display = DocumentStatusChecker.get_document_name_display(document_name)
#             return False, f"{doc_display} already uploaded. Delete existing to re-upload."
        
#         return True, None


# class DocumentResponseFormatter:
#     """Utility class for formatting API responses"""
    
#     @staticmethod
#     def format_success_response(document, message="Document uploaded successfully"):
#         """Format success response for document upload"""
#         return {
#             'success': True,
#             'message': message,
#             'data': {
#                 'document_id': document.document_id,
#                 'document_name': document.document_name,
#                 'document_name_display': document.get_document_name_display(),
#                 'document_type': document.document_type,
#                 'file_size': document.file_size,
#                 'uploaded_at': document.uploaded_at.isoformat(),
#                 'is_mandatory': document.is_mandatory,
#             }
#         }
    
#     @staticmethod
#     def format_error_response(message, errors=None):
#         """Format error response"""
#         response = {
#             'success': False,
#             'message': message
#         }
#         if errors:
#             response['errors'] = errors
#         return response
    
#     @staticmethod
#     def format_list_response(documents, status_info=None):
#         """Format list response with document status"""
#         response = {
#             'success': True,
#             'count': len(documents),
#             'documents': documents
#         }
#         if status_info:
#             response['status'] = status_info
#         return response


"""
Utility classes for document operations.
Handles document status checking and response formatting with dropdown groups.
"""
import logging

logger = logging.getLogger(__name__)


class DocumentStatusChecker:
    """Utility class for checking document upload status"""
    
    @staticmethod
    def get_company_document_status(company_id):
        """
        Get comprehensive document upload status for a company.
        
        Returns:
        - total_documents: Total documents uploaded
        - mandatory_documents: Total mandatory documents required
        - optional_documents: Total optional documents available
        - uploaded_mandatory: Count of uploaded mandatory documents
        - uploaded_optional: Count of uploaded optional documents
        - all_mandatory_uploaded: Boolean indicating if all mandatory docs are uploaded
        - missing_mandatory_documents: List of missing mandatory document names
        - uploaded_documents: List of all uploaded documents with details
        - document_groups: Status of MOA/AOA and MSME/Udyam dropdown groups
        """
        from ..models.CompanyDocumentModel import CompanyDocument
        
        logger.debug(f"Checking document status for company_id={company_id}")
        
        try:
            # Get all uploaded documents
            uploaded_docs = CompanyDocument.objects.filter(
                company_id=company_id,
                del_flag=0
            ).select_related('user_id_updated_by')
            
            # Get mandatory and optional document lists
            mandatory_docs = CompanyDocument.get_mandatory_documents()
            optional_docs = CompanyDocument.get_optional_documents()
            
            # Separate uploaded documents by type
            uploaded_mandatory = []
            uploaded_optional = []
            
            for doc in uploaded_docs:
                doc_info = {
                    'document_id': str(doc.document_id),
                    'document_name': doc.document_name,
                    'document_name_display': doc.get_document_name_display(),
                    'document_type': doc.document_type,
                    'file_size': doc.file_size,
                    'file_path': doc.document_file.name if doc.document_file else None,
                    'uploaded_at': doc.uploaded_at.isoformat(),
                    'is_mandatory': doc.is_mandatory,
                    'is_verified': doc.is_verified,
                }
                
                if doc.is_mandatory:
                    uploaded_mandatory.append(doc_info)
                else:
                    uploaded_optional.append(doc_info)
            
            # Find missing mandatory documents
            uploaded_mandatory_names = [
                doc['document_name'] for doc in uploaded_mandatory
            ]
            missing_mandatory = [
                doc_name for doc_name in mandatory_docs 
                if doc_name not in uploaded_mandatory_names
            ]
            
            # Get display names for missing documents
            missing_mandatory_display = []
            for doc_name in missing_mandatory:
                for choice in CompanyDocument.DOCUMENT_NAMES:
                    if choice[0] == doc_name:
                        missing_mandatory_display.append({
                            'document_name': doc_name,
                            'document_name_display': choice[1]
                        })
                        break
            
            # Check if all mandatory documents are uploaded
            all_mandatory_uploaded = len(missing_mandatory) == 0
            
            # Check document groups (MOA/AOA and MSME/Udyam)
            document_groups = {
                'moa_aoa_group': {
                    'options': [
                        {'value': 'MOA', 'label': 'Memorandum of Association (MoA)'},
                        {'value': 'AOA', 'label': 'Articles of Association (AoA)'}
                    ],
                    'uploaded': None,
                    'is_optional': True
                },
                'msme_udyam_group': {
                    'options': [
                        {'value': 'MSME', 'label': 'MSME Certificate'},
                        {'value': 'UDYAM', 'label': 'Udyam Certificate'}
                    ],
                    'uploaded': None,
                    'is_optional': True
                }
            }
            
            # Check which document from MOA/AOA group is uploaded
            for doc_info in uploaded_optional:
                if doc_info['document_name'] in CompanyDocument.MOA_AOA_GROUP:
                    document_groups['moa_aoa_group']['uploaded'] = {
                        'document_id': doc_info['document_id'],
                        'document_name': doc_info['document_name'],
                        'document_name_display': doc_info['document_name_display'],
                        'file_path': doc_info['file_path'],
                        'uploaded_at': doc_info['uploaded_at']
                    }
                
                if doc_info['document_name'] in CompanyDocument.MSME_UDYAM_GROUP:
                    document_groups['msme_udyam_group']['uploaded'] = {
                        'document_id': doc_info['document_id'],
                        'document_name': doc_info['document_name'],
                        'document_name_display': doc_info['document_name_display'],
                        'file_path': doc_info['file_path'],
                        'uploaded_at': doc_info['uploaded_at']
                    }
            
            status_data = {
                'total_documents': len(uploaded_docs),
                'mandatory_documents': len(mandatory_docs),
                'optional_documents': len(optional_docs),
                'uploaded_mandatory': len(uploaded_mandatory),
                'uploaded_optional': len(uploaded_optional),
                'all_mandatory_uploaded': all_mandatory_uploaded,
                'missing_mandatory_documents': missing_mandatory_display,
                'uploaded_documents': uploaded_mandatory + uploaded_optional,
                'document_groups': document_groups
            }
            
            logger.info(
                f"Document status for company_id={company_id}: "
                f"mandatory={len(uploaded_mandatory)}/{len(mandatory_docs)}, "
                f"optional={len(uploaded_optional)}/{len(optional_docs)}, "
                f"all_mandatory_uploaded={all_mandatory_uploaded}, "
                f"moa_aoa={document_groups['moa_aoa_group']['uploaded'] is not None}, "
                f"msme_udyam={document_groups['msme_udyam_group']['uploaded'] is not None}"
            )
            
            return status_data
            
        except Exception as e:
            logger.error(
                f"Error checking document status for company_id={company_id}: {str(e)}",
                exc_info=True
            )
            # Return empty status on error
            return {
                'total_documents': 0,
                'mandatory_documents': len(CompanyDocument.get_mandatory_documents()),
                'optional_documents': len(CompanyDocument.get_optional_documents()),
                'uploaded_mandatory': 0,
                'uploaded_optional': 0,
                'all_mandatory_uploaded': False,
                'missing_mandatory_documents': [],
                'uploaded_documents': [],
                'document_groups': {
                    'moa_aoa_group': {
                        'options': [
                            {'value': 'MOA', 'label': 'Memorandum of Association (MoA)'},
                            {'value': 'AOA', 'label': 'Articles of Association (AoA)'}
                        ],
                        'uploaded': None,
                        'is_optional': True
                    },
                    'msme_udyam_group': {
                        'options': [
                            {'value': 'MSME', 'label': 'MSME Certificate'},
                            {'value': 'UDYAM', 'label': 'Udyam Certificate'}
                        ],
                        'uploaded': None,
                        'is_optional': True
                    }
                }
            }


class DocumentResponseFormatter:
    """Utility class for formatting API responses"""
    
    @staticmethod
    def format_success_response(document, message="Document uploaded successfully"):
        """
        Format successful document operation response.
        
        Args:
            document: CompanyDocument instance
            message: Success message
            
        Returns:
            Formatted response dictionary
        """
        try:
            response = {
                'success': True,
                'message': message,
                'data': {
                    'document_id': str(document.document_id),
                    'document_name': document.document_name,
                    'document_name_display': document.get_document_name_display(),
                    'document_type': document.document_type,
                    'file_size': document.file_size,
                    'file_path': document.document_file.name if document.document_file else None,
                    'uploaded_at': document.uploaded_at.isoformat(),
                    'is_mandatory': document.is_mandatory,
                    'is_verified': document.is_verified,
                }
            }
            
            logger.debug(f"Formatted success response for document_id={document.document_id}")
            return response
            
        except Exception as e:
            logger.error(
                f"Error formatting success response: {str(e)}",
                exc_info=True
            )
            return {
                'success': True,
                'message': message,
                'data': {}
            }
    
    @staticmethod
    def format_error_response(message, errors=None):
        """
        Format error response.
        
        Args:
            message: Error message
            errors: Optional validation errors dictionary
            
        Returns:
            Formatted error response dictionary
        """
        response = {
            'success': False,
            'message': message
        }
        
        if errors:
            response['errors'] = errors
            logger.warning(f"Error response: {message}, errors={errors}")
        else:
            logger.warning(f"Error response: {message}")
        
        return response
    
    @staticmethod
    def format_list_response(documents_data, status_data):
        """
        Format document list response with status information.
        
        Args:
            documents_data: Serialized documents list
            status_data: Document status dictionary
            
        Returns:
            Formatted response dictionary
        """
        try:
            response = {
                'success': True,
                'data': {
                    'documents': documents_data,
                    'status': {
                        'total_documents': status_data.get('total_documents', 0),
                        'mandatory': {
                            'total': status_data.get('mandatory_documents', 0),
                            'uploaded': status_data.get('uploaded_mandatory', 0),
                            'missing': status_data.get('missing_mandatory_documents', []),
                            'all_uploaded': status_data.get('all_mandatory_uploaded', False)
                        },
                        'optional': {
                            'total': status_data.get('optional_documents', 0),
                            'uploaded': status_data.get('uploaded_optional', 0)
                        },
                        'document_groups': status_data.get('document_groups', {})
                    }
                }
            }
            
            logger.debug(
                f"Formatted list response: {len(documents_data)} documents, "
                f"mandatory_complete={status_data.get('all_mandatory_uploaded', False)}"
            )
            
            return response
            
        except Exception as e:
            logger.error(
                f"Error formatting list response: {str(e)}",
                exc_info=True
            )
            return {
                'success': True,
                'data': {
                    'documents': documents_data,
                    'status': {}
                }
            }