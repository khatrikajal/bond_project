

# from django.db import models
# from django.core.exceptions import ValidationError
# from .BaseModel import BaseModel
# from .CompanyInformationModel import CompanyInformation
# import mimetypes
# import uuid


# class CompanyDocument(BaseModel):
#     """
#     Stores company KYC documents with automatic document type detection.
#     Handles MoA, AoA, GST, MSME, and Import/Export certificates.
#     """

#     DOCUMENT_NAMES = [
#         ('CERTIFICATE_INC', 'Certificate of Incorporation'),
#         ('MOA', 'Memorandum of Association (MoA) / Articles of Association (AoA)'),
#         ('MSME', 'MSME / Udyam Certificate'),
#         ('IEC', 'Import Export Certificate (IEC)'),
#     ]

#     FILE_TYPES = [
#         ('PDF', 'PDF'),
#         ('JPEG', 'JPEG'),
#         ('JPG', 'JPG'),
#         ('PNG', 'PNG'),
#     ]

#     MANDATORY_DOCUMENTS = ['CERTIFICATE_INC', 'MOA', 'MSME', 'IEC']

#     document_id = models.UUIDField(
#         primary_key=True,
#         default=uuid.uuid4,
#         editable=False,
#         db_index=True
#     )

#     company = models.ForeignKey(
#         CompanyInformation,
#         on_delete=models.CASCADE,
#         related_name='documents',
#         db_index=True
#     )

#     document_name = models.CharField(
#         max_length=100,
#         choices=DOCUMENT_NAMES,
#         help_text="Auto-detected based on upload context"
#     )

#     document_type = models.CharField(
#         max_length=10,
#         choices=FILE_TYPES,
#         help_text="Auto-detected from file extension"
#     )

#     document_file = models.BinaryField(
#         help_text="Encrypted binary document data"
#     )

#     file_size = models.IntegerField(
#         help_text="File size in bytes for validation"
#     )

#     uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)

#     is_mandatory = models.BooleanField(
#         default=False,
#         help_text="Auto-set based on document_name"
#     )

#     is_verified = models.BooleanField(
#         default=False,
#         help_text="Admin verification status"
#     )

#     class Meta:
#         db_table = "company_documents"
#         ordering = ['-uploaded_at']
#         indexes = [
#             models.Index(fields=['company', 'document_name']),
#             models.Index(fields=['company', 'is_mandatory']),
#             models.Index(fields=['uploaded_at']),
#             models.Index(fields=['del_flag', 'company']),
#         ]
#         unique_together = [['company', 'document_name', 'del_flag']]

#     def __str__(self):
#         return f"{self.get_document_name_display()} - {self.company.company_name}"

#     def save(self, *args, **kwargs):
#         if self.document_name in self.MANDATORY_DOCUMENTS:
#             self.is_mandatory = True
#         super().save(*args, **kwargs)

#     def clean(self):
#         max_size = 5 * 1024 * 1024  # 5MB
#         if self.file_size > max_size:
#             raise ValidationError(f"File size exceeds 5MB limit")

#         allowed_types = [choice[0] for choice in self.FILE_TYPES]
#         if self.document_type not in allowed_types:
#             raise ValidationError(f"Invalid file type: {self.document_type}")

#     @classmethod
#     def get_mandatory_documents(cls):
#         return cls.MANDATORY_DOCUMENTS

#     @classmethod
#     def check_company_documents_complete(cls, company_id):
#         uploaded_docs = cls.objects.filter(
#             company_id=company_id,
#             del_flag=0,
#             is_mandatory=True
#         ).values_list('document_name', flat=True)

#         return all(doc in uploaded_docs for doc in cls.MANDATORY_DOCUMENTS)

#     @staticmethod
#     def detect_file_type(filename):
#         mime_type, _ = mimetypes.guess_type(filename)
#         extension = filename.rsplit('.', 1)[-1].upper()
#         valid_extensions = ['PDF', 'JPEG', 'JPG', 'PNG']
#         return extension if extension in valid_extensions else 'PDF'


from django.db import models
from django.core.exceptions import ValidationError
from .BaseModel import BaseModel
from .CompanyInformationModel import CompanyInformation
import mimetypes
import uuid
import logging
import os

logger = logging.getLogger(__name__)


def company_document_upload_path(instance, filename):
    """
    Generate upload path: company_documents/<company_name>/certificates/<document_display_name>.<ext>
    """
    try:
        company = instance.company
        company_name = company.company_name.replace(' ', '_').replace('/', '_')
        
        # Get document display name from choices
        doc_display_name = None
        for choice in CompanyDocument.DOCUMENT_NAMES:
            if choice[0] == instance.document_name:
                doc_display_name = choice[1].replace(' ', '_').replace('/', '_')
                break
        
        if not doc_display_name:
            doc_display_name = instance.document_name
        
        # Get file extension
        ext = filename.split('.')[-1].lower()
        
        # Build path: company_documents/<company_name>/certificates/<doc_name>.<ext>
        path = f"company_documents/{company_name}/certificates/{doc_display_name}.{ext}"
        
        logger.debug(f"Generated upload path: {path}")
        return path
        
    except Exception as e:
        logger.error(f"Error generating upload path: {str(e)}", exc_info=True)
        # Fallback path
        return f"company_documents/default/certificates/{filename}"


class CompanyDocument(BaseModel):
    """
    Stores company KYC documents.
    
    Rules:
    1. Certificate of Incorporation - MANDATORY
    2. MOA/AOA - OPTIONAL (user selects one from dropdown OR skips)
    3. MSME/Udyam - OPTIONAL (user selects from dropdown OR skips)
    4. IEC - OPTIONAL (no dropdown, simple upload OR skip)
    """

    DOCUMENT_NAMES = [
        ('CERTIFICATE_INC', 'Certificate of Incorporation'),
        ('MOA', 'Memorandum of Association (MoA)'),
        ('AOA', 'Articles of Association (AoA)'),
        ('MSME', 'MSME Certificate'),
        ('UDYAM', 'Udyam Certificate'),
        ('IEC', 'Import Export Certificate (IEC)'),
    ]

    FILE_TYPES = [
        ('PDF', 'PDF'),
        ('JPEG', 'JPEG'),
        ('JPG', 'JPG'),
        ('PNG', 'PNG'),
    ]

    # Only Certificate of Incorporation is mandatory
    MANDATORY_DOCUMENTS = ['CERTIFICATE_INC']
    
    # Documents that are mutually exclusive (user uploads one from dropdown)
    MOA_AOA_GROUP = ['MOA', 'AOA']
    MSME_UDYAM_GROUP = ['MSME', 'UDYAM']

    document_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True
    )

    company = models.ForeignKey(
        CompanyInformation,
        on_delete=models.CASCADE,
        related_name='documents',
        db_index=True
    )

    document_name = models.CharField(
        max_length=100,
        choices=DOCUMENT_NAMES,
        help_text="Select document type from dropdown"
    )

    document_type = models.CharField(
        max_length=10,
        choices=FILE_TYPES,
        help_text="Auto-detected from file extension"
    )

    document_file = models.FileField(
        upload_to=company_document_upload_path,
        help_text="Document stored with company name folder structure"
    )

    file_size = models.IntegerField(
        help_text="File size in bytes for validation"
    )

    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    is_mandatory = models.BooleanField(
        default=False,
        help_text="Auto-set based on document_name"
    )

    is_verified = models.BooleanField(
        default=False,
        help_text="Admin verification status"
    )

    class Meta:
        db_table = "company_documents"
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['company', 'document_name']),
            models.Index(fields=['company', 'is_mandatory']),
            models.Index(fields=['uploaded_at']),
            models.Index(fields=['del_flag', 'company']),
        ]
        # Remove unique_together to allow MOA or AOA (not both at same time via logic)

    def __str__(self):
        return f"{self.get_document_name_display()} - {self.company.company_name}"

    def save(self, *args, **kwargs):
        """Auto-set is_mandatory flag based on document name"""
        if self.document_name in self.MANDATORY_DOCUMENTS:
            self.is_mandatory = True
            logger.debug(
                f"Document {self.document_name} marked as mandatory for "
                f"company_id={self.company_id}"
            )
        else:
            self.is_mandatory = False
            logger.debug(
                f"Document {self.document_name} marked as optional for "
                f"company_id={self.company_id}"
            )
        
        super().save(*args, **kwargs)
        logger.info(
            f"Document saved: document_id={self.document_id}, "
            f"company={self.company.company_name}, document_name={self.document_name}, "
            f"is_mandatory={self.is_mandatory}, file_path={self.document_file.name if self.document_file else 'None'}"
        )

    def clean(self):
        """Validate file size, type, and MOA/AOA exclusivity"""
        max_size = 5 * 1024 * 1024  # 5MB
        if self.file_size > max_size:
            logger.warning(
                f"File size validation failed for company_id={self.company_id}: "
                f"{self.file_size} bytes exceeds 5MB limit"
            )
            raise ValidationError(f"File size exceeds 5MB limit")

        allowed_types = [choice[0] for choice in self.FILE_TYPES]
        if self.document_type not in allowed_types:
            logger.warning(
                f"Invalid file type for company_id={self.company_id}: "
                f"{self.document_type}"
            )
            raise ValidationError(f"Invalid file type: {self.document_type}")
        
        # Check MOA/AOA exclusivity (user can upload either MOA OR AOA, not both)
        if self.document_name in self.MOA_AOA_GROUP:
            other_docs = self.MOA_AOA_GROUP.copy()
            other_docs.remove(self.document_name)
            
            existing = CompanyDocument.objects.filter(
                company=self.company,
                document_name__in=other_docs,
                del_flag=0
            ).exclude(document_id=self.document_id)
            
            if existing.exists():
                existing_doc = existing.first()
                logger.warning(
                    f"MOA/AOA conflict: company_id={self.company_id} already has "
                    f"{existing_doc.document_name}"
                )
                raise ValidationError(
                    f"Company already has {existing_doc.get_document_name_display()}. "
                    f"You can only upload one document from MOA/AOA group."
                )
        
        # Check MSME/Udyam exclusivity (user can upload either MSME OR Udyam, not both)
        if self.document_name in self.MSME_UDYAM_GROUP:
            other_docs = self.MSME_UDYAM_GROUP.copy()
            other_docs.remove(self.document_name)
            
            existing = CompanyDocument.objects.filter(
                company=self.company,
                document_name__in=other_docs,
                del_flag=0
            ).exclude(document_id=self.document_id)
            
            if existing.exists():
                existing_doc = existing.first()
                logger.warning(
                    f"MSME/Udyam conflict: company_id={self.company_id} already has "
                    f"{existing_doc.document_name}"
                )
                raise ValidationError(
                    f"Company already has {existing_doc.get_document_name_display()}. "
                    f"You can only upload one document from MSME/Udyam group."
                )

    @classmethod
    def get_mandatory_documents(cls):
        """Return list of mandatory document types"""
        logger.debug(f"Fetching mandatory documents: {cls.MANDATORY_DOCUMENTS}")
        return cls.MANDATORY_DOCUMENTS

    @classmethod
    def get_optional_documents(cls):
        """Return list of optional document types"""
        optional_docs = [
            doc[0] for doc in cls.DOCUMENT_NAMES 
            if doc[0] not in cls.MANDATORY_DOCUMENTS
        ]
        logger.debug(f"Fetching optional documents: {optional_docs}")
        return optional_docs
    
    @classmethod
    def get_moa_aoa_group(cls):
        """Return MOA/AOA group (user selects one from dropdown)"""
        return cls.MOA_AOA_GROUP
    
    @classmethod
    def get_msme_udyam_group(cls):
        """Return MSME/Udyam group (user selects one from dropdown)"""
        return cls.MSME_UDYAM_GROUP

    @classmethod
    def check_company_documents_complete(cls, company_id):
        """
        Check if all mandatory documents are uploaded for a company.
        Returns True only if Certificate of Incorporation exists.
        """
        try:
            uploaded_mandatory_docs = cls.objects.filter(
                company_id=company_id,
                del_flag=0,
                is_mandatory=True
            ).values_list('document_name', flat=True)

            uploaded_set = set(uploaded_mandatory_docs)
            required_set = set(cls.MANDATORY_DOCUMENTS)
            
            missing_docs = required_set - uploaded_set
            is_complete = len(missing_docs) == 0

            if is_complete:
                logger.info(
                    f"All mandatory documents uploaded for company_id={company_id}"
                )
            else:
                logger.warning(
                    f"Missing mandatory documents for company_id={company_id}: "
                    f"{list(missing_docs)}"
                )

            return is_complete
        except Exception as e:
            logger.error(
                f"Error checking document completion for company_id={company_id}: "
                f"{str(e)}",
                exc_info=True
            )
            return False

    @staticmethod
    def detect_file_type(filename):
        """Detect file type from filename extension"""
        try:
            mime_type, _ = mimetypes.guess_type(filename)
            extension = filename.rsplit('.', 1)[-1].upper()
            valid_extensions = ['PDF', 'JPEG', 'JPG', 'PNG']
            
            detected_type = extension if extension in valid_extensions else 'PDF'
            logger.debug(
                f"File type detected for '{filename}': {detected_type} "
                f"(mime_type: {mime_type})"
            )
            return detected_type
        except Exception as e:
            logger.error(
                f"Error detecting file type for '{filename}': {str(e)}",
                exc_info=True
            )
            return 'PDF'  # Default fallback