from rest_framework import serializers
from django.db import transaction
import logging

from ..models.CompanyDocumentModel import CompanyDocument

logger = logging.getLogger(__name__)


# =====================================================================
# 🔵 BULK UPLOAD SERIALIZER (token-based)
# =====================================================================

class CompanyDocumentBulkUploadSerializer(serializers.Serializer):

    certificate_of_incorporation = serializers.FileField(required=False)

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
        company = self.context["company"]
        company_id = str(company.company_id)
        errors = {}

        # ------------ Certificate Validation ------------
        certificate_name = "CERTIFICATE_OF_INCORPORATION"
        cert_exists = CompanyDocument.objects.filter(
            company_id=company_id,
            document_name=certificate_name,
            del_flag=0
        ).exists()

        if not cert_exists and not data.get("certificate_of_incorporation"):
            errors["certificate_of_incorporation"] = "Certificate of Incorporation is required on first upload."

        if cert_exists and data.get("certificate_of_incorporation"):
            errors["certificate_of_incorporation"] = "Certificate already exists. Delete before re-upload."

        # ------------ Other document duplicate rules ------------
        upload_map = {
            "moa_aoa_file": data.get("moa_aoa_type"),
            "msme_udyam_file": data.get("msme_udyam_type"),
            "import_export_certificate": "IEC",
        }

        for field_name, name in upload_map.items():
            file = data.get(field_name)
            if not file or not name:
                continue

            exists = CompanyDocument.objects.filter(
                company_id=company_id,
                document_name=name,
                del_flag=0
            ).exists()

            if exists:
                errors[field_name] = f"{name} already exists. Delete before uploading again."

        # Pairing rules
        if data.get("moa_aoa_type") and not data.get("moa_aoa_file"):
            errors["moa_aoa_file"] = "File required for selected MOA/AOA."

        if data.get("moa_aoa_file") and not data.get("moa_aoa_type"):
            errors["moa_aoa_type"] = "Select MOA or AOA."

        if data.get("msme_udyam_type") and not data.get("msme_udyam_file"):
            errors["msme_udyam_file"] = "File required for selected MSME/UDYAM."

        if data.get("msme_udyam_file") and not data.get("msme_udyam_type"):
            errors["msme_udyam_type"] = "Select MSME or UDYAM."

        # ------------ File validation ------------
        allowed_ext = ["pdf", "jpeg", "jpg", "png"]
        max_size = 5 * 1024 * 1024

        for field, file in {
            "certificate_of_incorporation": data.get("certificate_of_incorporation"),
            "moa_aoa_file": data.get("moa_aoa_file"),
            "msme_udyam_file": data.get("msme_udyam_file"),
            "import_export_certificate": data.get("import_export_certificate"),
        }.items():

            if not file:
                continue

            if file.size > max_size:
                errors[field] = "File must be under 5MB."

            ext = file.name.split(".")[-1].lower()
            if ext not in allowed_ext:
                errors[field] = "Allowed types: pdf, jpeg, jpg, png."

        if errors:
            raise serializers.ValidationError(errors)

        return data

    # SAVE ------------------------------------------------------
    def create(self, validated_data):
        company = self.context["company"]
        company_id = str(company.company_id)

        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None

        created_docs = []

        with transaction.atomic():

            # Certificate
            cert_file = validated_data.get("certificate_of_incorporation")
            if cert_file:
                created_docs.append(
                    self._create_doc(company_id, "CERTIFICATE_OF_INCORPORATION", cert_file, user)
                )

            # MOA/AOA
            moa_type = validated_data.get("moa_aoa_type")
            moa_file = validated_data.get("moa_aoa_file")
            if moa_type and moa_file:
                created_docs.append(
                    self._create_doc(company_id, moa_type, moa_file, user)
                )

            # MSME / UDYAM
            msme_type = validated_data.get("msme_udyam_type")
            msme_file = validated_data.get("msme_udyam_file")
            if msme_type and msme_file:
                created_docs.append(
                    self._create_doc(company_id, msme_type, msme_file, user)
                )

            # IEC
            iec_file = validated_data.get("import_export_certificate")
            if iec_file:
                created_docs.append(
                    self._create_doc(company_id, "IEC", iec_file, user)
                )

        return created_docs

    def _create_doc(self, company_id, doc_name, file, user):
        doc_type = CompanyDocument.detect_file_type(file.name)

        return CompanyDocument.objects.create(
            company_id=company_id,
            document_name=doc_name,
            document_type=doc_type,
            document_file=file,
            file_size=file.size,
            user_id_updated_by=user
        )


# =====================================================================
# 🔵 LIST SERIALIZER
# =====================================================================

class CompanyDocumentListSerializer(serializers.ModelSerializer):
    document_name_display = serializers.CharField(source="get_document_name_display", read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    file_path = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = CompanyDocument
        fields = [
            "document_id",
            "document_name",
            "document_name_display",
            "document_type",
            "file_size",
            "file_size_mb",
            "file_path",
            "uploaded_at",
            "is_mandatory",
            "is_verified",
            "status",
        ]

    def get_file_size_mb(self, obj):
        return round(obj.file_size / (1024 * 1024), 2)

    def get_file_path(self, obj):
        return obj.document_file.name if obj.document_file else None

    def get_status(self, obj):
        return "Verified" if obj.is_verified else "Uploaded"


# =====================================================================
# 🔵 DETAIL SERIALIZER
# =====================================================================

class CompanyDocumentDetailSerializer(serializers.ModelSerializer):
    document_name_display = serializers.CharField(source="get_document_name_display", read_only=True)
    file_path = serializers.SerializerMethodField()

    class Meta:
        model = CompanyDocument
        fields = [
            "document_id",
            "document_name",
            "document_name_display",
            "document_type",
            "file_size",
            "uploaded_at",
            "is_mandatory",
            "is_verified",
            "file_path",
        ]

    def get_file_path(self, obj):
        return obj.document_file.name if obj.document_file else None


# =====================================================================
# 🔵 STATUS SERIALIZER
# =====================================================================

class CompanyDocumentStatusSerializer(serializers.Serializer):
    total_documents = serializers.IntegerField()
    mandatory_documents = serializers.IntegerField()
    optional_documents = serializers.IntegerField()
    uploaded_mandatory = serializers.IntegerField()
    uploaded_optional = serializers.IntegerField()
    all_mandatory_uploaded = serializers.BooleanField()
    missing_mandatory_documents = serializers.ListField(child=serializers.DictField())
    uploaded_documents = serializers.ListField(child=serializers.DictField())
    document_groups = serializers.DictField()


# =====================================================================
# 🔵 SINGLE DOCUMENT UPLOAD SERIALIZER
# =====================================================================

class CompanySingleDocumentUploadSerializer(serializers.Serializer):
    document_name = serializers.ChoiceField(
        choices=CompanyDocument.DOCUMENT_NAMES,
        required=True
    )
    file = serializers.FileField(required=True)

    # -------------------------------
    # FILE VALIDATION
    # -------------------------------
    def validate_file(self, file):
        if file.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("File cannot exceed 5MB.")

        ext = file.name.split(".")[-1].lower()
        if ext not in ["pdf", "jpeg", "jpg", "png"]:
            raise serializers.ValidationError("Allowed: PDF, JPEG, JPG, PNG.")

        return file

    # -------------------------------
    # DUPLICATE CHECK FIXED HERE
    # -------------------------------
    def validate(self, data):
        """
        Prevent duplicate documents for the same company,
        but ALLOW updating the same document (PUT).
        """
        company = self.context["company"]
        company_id = str(company.company_id)
        name = data["document_name"]

        # Base duplicate check
        qs = CompanyDocument.objects.filter(
            company_id=company_id,
            document_name=name,
            del_flag=0
        )

        # FIX: If updating, exclude current instance
        if getattr(self, "instance", None):
            qs = qs.exclude(document_id=self.instance.document_id)

        if qs.exists():
            raise serializers.ValidationError({
                "document_name": f"{name} already exists. Delete first."
            })

        return data

    # -------------------------------
    # CREATE DOCUMENT
    # -------------------------------
    def create(self, validated):
        company = self.context["company"]
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None

        doc_type = CompanyDocument.detect_file_type(validated["file"].name)

        return CompanyDocument.objects.create(
            company=company,
            document_name=validated["document_name"],
            document_type=doc_type,
            document_file=validated["file"],
            file_size=validated["file"].size,
            user_id_updated_by=user
        )

    # -------------------------------
    # UPDATE (PUT)
    # -------------------------------
    def update(self, instance, validated):
        file = validated.get("file")
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None

        if file:
            instance.document_file = file
            instance.file_size = file.size
            instance.document_type = CompanyDocument.detect_file_type(file.name)

        instance.user_id_updated_by = user
        instance.save()
        return instance

    # -------------------------------
    # SOFT DELETE
    # -------------------------------
    def soft_delete(self, instance):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None

        instance.del_flag = 1
        instance.user_id_updated_by = user
        instance.save()
        return True
