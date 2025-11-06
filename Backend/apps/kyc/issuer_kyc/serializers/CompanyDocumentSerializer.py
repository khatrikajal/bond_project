from rest_framework import serializers
from django.db import transaction
from django.core.files.uploadedfile import InMemoryUploadedFile
from ..models.CompanyDocumentModel import CompanyDocument
from ..models.CompanyInformationModel import CompanyInformation
import logging

logger = logging.getLogger(__name__)


from rest_framework import serializers
from django.db import transaction
from django.core.files.uploadedfile import InMemoryUploadedFile
from ..models.CompanyDocumentModel import CompanyDocument
from ..models.CompanyInformationModel import CompanyInformation
import logging

logger = logging.getLogger(__name__)


class CompanyDocumentBulkUploadSerializer(serializers.Serializer):
    """
    Serializer for bulk document upload.
    """

    # Mandatory on FIRST upload only
    certificate_of_incorporation = serializers.FileField(required=False)

    # Optional fields
    moa_aoa_type = serializers.ChoiceField(
        choices=[('MOA', 'MOA'), ('AOA', 'AOA')],
        required=False,
        allow_blank=True
    )
    moa_aoa_file = serializers.FileField(required=False)

    msme_udyam_type = serializers.ChoiceField(
        choices=[('MSME', 'MSME'), ('UDYAM', 'UDYAM')],
        required=False,
        allow_blank=True
    )
    msme_udyam_file = serializers.FileField(required=False)

    import_export_certificate = serializers.FileField(required=False)

    def validate(self, data):
        """Validate files, types, and ensure no duplicate uploads."""
        logger.debug(f"Validating bulk document upload: {list(data.keys())}")
        errors = {}
        company_id = self.context["company_id"]

        # ✅ Import here to avoid circular import
        from ..models.CompanyDocumentModel import CompanyDocument

        # ✅ 1. Certificate mandatory on FIRST upload
        cert_exists = CompanyDocument.objects.filter(
            company_id=company_id,
            document_name="CERTIFICATE_INC",
            del_flag=0
        ).exists()

        if not cert_exists and not data.get("certificate_of_incorporation"):
            errors["certificate_of_incorporation"] = (
                "Certificate of Incorporation is mandatory for first upload."
            )

        # ✅ 2. Mapping to detect duplicate uploads
        upload_map = {
            "certificate_of_incorporation": "CERTIFICATE_INC",
            "moa_aoa_file": data.get("moa_aoa_type"),
            "msme_udyam_file": data.get("msme_udyam_type"),
            "import_export_certificate": "IEC",
        }

        # ✅ 3. Check duplicates — if exists, user must delete first
        for field_name, document_name in upload_map.items():
            file = data.get(field_name)
            if not file or not document_name:
                continue

            exists = CompanyDocument.objects.filter(
                company_id=company_id,
                document_name=document_name,
                del_flag=0
            ).exists()

            if exists:
                errors[field_name] = (
                    f"{document_name} already exists. Delete it before uploading again."
                )

        if errors:
            raise serializers.ValidationError(errors)

        # ✅ 4. Validate MOA/AOA dropdown logic
        if data.get('moa_aoa_type') and not data.get('moa_aoa_file'):
            errors['moa_aoa_file'] = "File required for selected MOA/AOA"

        if data.get('moa_aoa_file') and not data.get('moa_aoa_type'):
            errors['moa_aoa_type'] = "Please select MOA or AOA"

        # ✅ 5. Validate MSME/Udyam dropdown logic
        if data.get('msme_udyam_type') and not data.get('msme_udyam_file'):
            errors['msme_udyam_file'] = "File required for selected MSME/Udyam"

        if data.get('msme_udyam_file') and not data.get('msme_udyam_type'):
            errors['msme_udyam_type'] = "Please select MSME or Udyam"

        # ✅ 6. File validation (size + extension)
        allowed_extensions = ['pdf', 'jpeg', 'jpg', 'png']
        max_size = 5 * 1024 * 1024  # 5MB

        files_to_validate = {
            'certificate_of_incorporation': data.get('certificate_of_incorporation'),
            'moa_aoa_file': data.get('moa_aoa_file'),
            'msme_udyam_file': data.get('msme_udyam_file'),
            'import_export_certificate': data.get('import_export_certificate'),
        }

        for field_name, file in files_to_validate.items():
            if not file:
                continue

            if file.size > max_size:
                errors[field_name] = "File size must be less than 5MB"

            ext = file.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                errors[field_name] = "Allowed file types: pdf, jpeg, jpg, png"

        if errors:
            logger.error(f"Bulk upload validation failed: {errors}")
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        """Create all documents (new row for each upload attempt)."""
        company_id = self.context['company_id']
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None

        from ..models.CompanyDocumentModel import CompanyDocument

        created_documents = []
        document_ids = []

        with transaction.atomic():

            # ✅ Certificate
            cert_file = validated_data.get('certificate_of_incorporation')
            if cert_file:
                doc = self._create_document(company_id, "CERTIFICATE_INC", cert_file, user)
                created_documents.append(doc)
                document_ids.append(str(doc.document_id))

            # ✅ MOA/AOA
            moa_type = validated_data.get('moa_aoa_type')
            moa_file = validated_data.get('moa_aoa_file')
            if moa_type and moa_file:
                doc = self._create_document(company_id, moa_type, moa_file, user)
                created_documents.append(doc)
                document_ids.append(str(doc.document_id))

            # ✅ MSME/Udyam
            msme_type = validated_data.get('msme_udyam_type')
            msme_file = validated_data.get('msme_udyam_file')
            if msme_type and msme_file:
                doc = self._create_document(company_id, msme_type, msme_file, user)
                created_documents.append(doc)
                document_ids.append(str(doc.document_id))

            # ✅ IEC
            iec_file = validated_data.get('import_export_certificate')
            if iec_file:
                doc = self._create_document(company_id, 'IEC', iec_file, user)
                created_documents.append(doc)
                document_ids.append(str(doc.document_id))

        return created_documents

    def _create_document(self, company_id, document_name, file, user):
        """Create a single document row (new entry always)."""
        document_type = CompanyDocument.detect_file_type(file.name)

        doc = CompanyDocument.objects.create(
            company_id=company_id,
            document_name=document_name,
            document_type=document_type,
            document_file=file,
            file_size=file.size,
            user_id_updated_by=user
        )
        return doc

class CompanyDocumentListSerializer(serializers.ModelSerializer):
    """Serializer for listing documents without file data"""
    document_name_display = serializers.CharField(
        source='get_document_name_display',
        read_only=True
    )
    file_size_mb = serializers.SerializerMethodField()
    file_path = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    uploaded_by = serializers.SerializerMethodField()

    class Meta:
        model = CompanyDocument
        fields = [
            'document_id', 'document_name', 'document_name_display',
            'document_type', 'file_size', 'file_size_mb', 'file_path',
            'uploaded_at', 'is_mandatory', 'is_verified',
            'status', 'uploaded_by'
        ]

    def get_file_size_mb(self, obj):
        return round(obj.file_size / (1024 * 1024), 2)
    
    def get_file_path(self, obj):
        """Return the file storage path"""
        return obj.document_file.name if obj.document_file else None

    def get_status(self, obj):
        return "Verified" if obj.is_verified else "Uploaded"

    def get_uploaded_by(self, obj):
        if obj.user_id_updated_by:
            return {
                'user_id': str(obj.user_id_updated_by.user_id),
                'uploaded_at': obj.uploaded_at.isoformat()
            }
        return None


class CompanyDocumentDetailSerializer(serializers.ModelSerializer):
    """Serializer for retrieving document with file URL"""
    document_name_display = serializers.CharField(
        source='get_document_name_display',
        read_only=True
    )
    file_url = serializers.SerializerMethodField()
    file_path = serializers.SerializerMethodField()
    uploaded_by = serializers.SerializerMethodField()

    class Meta:
        model = CompanyDocument
        fields = [
            'document_id', 'document_name', 'document_name_display',
            'document_type', 'file_size', 'uploaded_at',
            'is_mandatory', 'is_verified', 'file_url', 'file_path', 'uploaded_by'
        ]

    def get_file_url(self, obj):
        """Return the file URL if available"""
        try:
            if obj.document_file:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.document_file.url)
                return obj.document_file.url
        except Exception as e:
            logger.error(
                f"Error generating file URL for document_id={obj.document_id}: {str(e)}",
                exc_info=True
            )
        return None
    
    def get_file_path(self, obj):
        """Return the file storage path"""
        return obj.document_file.name if obj.document_file else None

    def get_uploaded_by(self, obj):
        if obj.user_id_updated_by:
            return {
                'user_id': str(obj.user_id_updated_by.user_id),
                'uploaded_at': obj.uploaded_at.isoformat()
            }
        return None


class CompanyDocumentStatusSerializer(serializers.Serializer):
    """Serializer for checking document upload status"""
    total_documents = serializers.IntegerField()
    mandatory_documents = serializers.IntegerField()
    optional_documents = serializers.IntegerField()
    uploaded_mandatory = serializers.IntegerField()
    uploaded_optional = serializers.IntegerField()
    all_mandatory_uploaded = serializers.BooleanField()
    missing_mandatory_documents = serializers.ListField(child=serializers.DictField())
    uploaded_documents = serializers.ListField(child=serializers.DictField())
    document_groups = serializers.DictField()


class CompanySingleDocumentUploadSerializer(serializers.Serializer):
    """
    Serializer for single document upload/update.
    (Used during onboarding BEFORE login)
    """
    document_name = serializers.ChoiceField(
        choices=CompanyDocument.DOCUMENT_NAMES,
        required=True
    )
    file = serializers.FileField(required=True)

    # ✅ Validate file: size + extension
    def validate_file(self, value):
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 5MB")

        allowed_extensions = ['pdf', 'jpeg', 'jpg', 'png']
        ext = value.name.split('.')[-1].lower()

        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                "File type not allowed. Use PDF/JPG/JPEG/PNG."
            )

        return value

    # ✅ Validate MOA/AOA & MSME/Udyam exclusivity
    def validate(self, data):
        company_id = self.context['company_id']
        document_name = data['document_name']

        # ✅ MOA/AOA validation
        if document_name in CompanyDocument.MOA_AOA_GROUP:
            other = CompanyDocument.MOA_AOA_GROUP.copy()
            other.remove(document_name)

            exists = CompanyDocument.objects.filter(
                company_id=company_id,
                document_name__in=other,
                del_flag=0
            ).exists()

            if exists:
                raise serializers.ValidationError({
                    "document_name": f"Another MOA/AOA already exists. Delete it first."
                })

        # ✅ MSME/Udyam validation
        if document_name in CompanyDocument.MSME_UDYAM_GROUP:
            other = CompanyDocument.MSME_UDYAM_GROUP.copy()
            other.remove(document_name)

            exists = CompanyDocument.objects.filter(
                company_id=company_id,
                document_name__in=other,
                del_flag=0
            ).exists()

            if exists:
                raise serializers.ValidationError({
                    "document_name": f"Another MSME/Udyam document already exists. Delete it first."
                })

        return data

    # ✅ CREATE document (safe for AnonymousUser)
    def create(self, validated_data):
        file = validated_data["file"]
        document_name = validated_data["document_name"]
        company_id = self.context['company_id']
        request = self.context.get("request")

        # ✅ SAFE USER HANDLING (never crash)
        user = getattr(request, "user", None)
        safe_user = user if getattr(user, "is_authenticated", False) else None

        try:
            with transaction.atomic():

                doc_type = CompanyDocument.detect_file_type(file.name)

                document = CompanyDocument.objects.create(
                    company_id=company_id,
                    document_name=document_name,
                    document_type=doc_type,
                    document_file=file,
                    file_size=file.size,
                    user_id_updated_by=safe_user   # ✅ SAFE
                )

                return document

        except Exception as e:
            logger.error(f"[SINGLE_UPLOAD] Error creating document: {e}", exc_info=True)
            raise

    # ✅ UPDATE existing document
    def update(self, instance, validated_data):
        file = validated_data.get("file")
        request = self.context.get("request")

        user = getattr(request, "user", None)
        safe_user = user if getattr(user, "is_authenticated", False) else None

        try:
            with transaction.atomic():

                if file:
                    if instance.document_file:
                        instance.document_file.delete(save=False)

                    instance.document_file = file
                    instance.file_size = file.size
                    instance.document_type = CompanyDocument.detect_file_type(file.name)

                instance.user_id_updated_by = safe_user
                instance.save()

                return instance

        except Exception as e:
            logger.error(f"[SINGLE_UPDATE] Error updating document: {e}", exc_info=True)
            raise

    # ✅ SOFT DELETE
    def soft_delete(self, instance):
        request = self.context.get("request")

        user = getattr(request, "user", None)
        safe_user = user if getattr(user, "is_authenticated", False) else None

        try:
            with transaction.atomic():
                instance.del_flag = 1
                instance.user_id_updated_by = safe_user
                instance.save()

                return True
        except Exception as e:
            logger.error(f"[SINGLE_DELETE] Error soft deleting: {e}", exc_info=True)
            raise
