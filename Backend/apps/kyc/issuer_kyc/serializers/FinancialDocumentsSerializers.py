from rest_framework import serializers
from datetime import date
from dateutil.relativedelta import relativedelta
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from apps.kyc.issuer_kyc.models.FinancialDocumentModel import (
    FinancialDocument,
    DocumentType,
    DocumentTag,
    PeriodType,
    VerificationSource
)
import os
import json


# class FinancialDocumentUploadSerializer(serializers.Serializer):
#     # ---------- Meta fields ----------
#     document_type = serializers.ChoiceField(choices=DocumentType.values)
#     document_tag = serializers.ChoiceField(choices=DocumentTag.values)

#     financial_year = serializers.CharField(max_length=9)
#     period_type = serializers.ChoiceField(choices=PeriodType.values)

#     period_month = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=12)
#     period_quarter = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=4)

#     # file required ONLY for create
#     file = serializers.FileField(required=False)

#     auditor_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
#     audit_report_date = serializers.DateField(required=False, allow_null=True)
#     audit_firm_name = serializers.CharField(max_length=255, required=False, allow_blank=True)

#     auto_verify = serializers.BooleanField(default=True)
   
#     file_url = serializers.URLField(required=False)

#     # -----------------------------------------------------------

#     def validate(self, data):
#         company_id = self.context.get("company_id")
#         if not company_id:
#             raise serializers.ValidationError("company_id missing from context")

#         company = CompanyInformation.objects.filter(pk=company_id, del_flag=0).first()
#         if not company:
#             raise serializers.ValidationError("Invalid company ID")

#         # If partial update → redirect to partial validator
#         if self.partial:
#             return self.validate_partial(data)

#         # If full update or create → file REQUIRED
#         if not data.get("file") and not data.get("file_url"):
#             raise serializers.ValidationError("Either file or file_url required")
 
#         return self._common_validation(data, company)


#     # -----------------------------------------------------------

#     def validate_partial(self, data):
#         """
#         Used for partial_update().
#         Only validate fields that are present.
#         """
#         company_id = self.context.get("company_id")
#         company = CompanyInformation.objects.filter(pk=company_id, del_flag=0).first()
#         if not company:
#             raise serializers.ValidationError("Invalid company ID")

#         return self._common_validation(data, company, is_partial=True)

#     # -----------------------------------------------------------

#     def _common_validation(self, data, company, is_partial=False):
#         """
#         Shared validation logic for create, update, and partial_update.
#         """
#         doc_type = data.get("document_type")
#         doc_tag = data.get("document_tag")
#         fy = data.get("financial_year")
#         period_type = data.get("period_type")

#         month = data.get("period_month")
#         quarter = data.get("period_quarter")

#         # ----- Period rules -----

#         if not is_partial:
#             self._validate_period_rules(period_type, month, quarter)

#         # ----- Business rules -----

#         if not is_partial or ("period_type" in data or "document_type" in data):
#             self._validate_business_rules(company, doc_type, period_type)

#         # ----- Audited document rules -----

#         if doc_tag == DocumentTag.AUDITED:
#             self._validate_audited_rules(data, is_partial)

#         # ----- File validation -----

#         if "file" in data:
#             file = data["file"]
#             ext = os.path.splitext(file.name)[1].lower()

#             ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}

#             if ext not in ALLOWED_EXTENSIONS:
#                 raise serializers.ValidationError({
#                     "file": f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
#                 })
#             if file.size > 10 * 1024 * 1024:
#                 raise serializers.ValidationError({"file": "Max size is 10MB"})

#         # ---------- Generate period dates only if all data present ----------
#         if fy and period_type:
#             start_date, end_date = self.calculate_period_dates(fy, period_type, month, quarter)

#             data["period_start_date"] = start_date
#             data["period_end_date"] = end_date

#             # period code
#             if period_type == PeriodType.MONTHLY:
#                 data["period_code"] = f"{start_date.year}-{start_date.month:02d}"
#             elif period_type == PeriodType.QUARTERLY:
#                 data["period_code"] = f"Q{quarter}-{start_date.year}"
#             else:
#                 data["period_code"] = None

#         # ---------- Version logic (create/update only) ----------
#         if not is_partial:
#             latest = FinancialDocument.objects.filter(
#                 company_id=company.company_id,
#                 document_type=doc_type,
#                 period_start_date=data["period_start_date"],
#                 period_end_date=data["period_end_date"],
#                 document_tag=doc_tag,
#                 del_flag=0
#             ).order_by("-version").first()

#             data["version"] = (latest.version + 1) if latest else 1

#         return data

#     # -----------------------------------------------------------

#     def _validate_period_rules(self, period_type, month, quarter):
#         if period_type == PeriodType.MONTHLY and not month:
#             raise serializers.ValidationError({"period_month": "Required for monthly documents"})

#         if period_type == PeriodType.QUARTERLY and not quarter:
#             raise serializers.ValidationError({"period_quarter": "Required for quarterly documents"})

#         if period_type == PeriodType.YEARLY and (month or quarter):
#             raise serializers.ValidationError("Monthly/quarterly values not allowed for yearly documents")

#     # -----------------------------------------------------------

#     def _validate_business_rules(self, company, doc_type, period_type):
#         if doc_type == DocumentType.GSTR_3B and period_type != PeriodType.MONTHLY:
#             raise serializers.ValidationError({"period_type": "GSTR-3B must be monthly"})

#         if doc_type == DocumentType.GSTR_9 and period_type != PeriodType.YEARLY:
#             raise serializers.ValidationError({"period_type": "GSTR-9 must be yearly"})

#         if doc_type == DocumentType.FINANCIAL_STATEMENT and period_type != PeriodType.YEARLY:
#             raise serializers.ValidationError({"period_type": "Financial statements must be yearly"})

#     # -----------------------------------------------------------
#     def _validate_audited_rules(self, data, is_partial):
#         if not is_partial:
#             # create/update
#             if not data.get("auditor_name"):
#                 raise serializers.ValidationError({"auditor_name": "Required for audited documents"})
#             if not data.get("audit_report_date"):
#                 raise serializers.ValidationError({"audit_report_date": "Required for audited documents"})
#         else:
#             # partial update → only validate if field present
#             if "auditor_name" in data and not data.get("auditor_name"):
#                 raise serializers.ValidationError({"auditor_name": "Required for audited documents"})
#             if "audit_report_date" in data and not data.get("audit_report_date"):
#                 raise serializers.ValidationError({"audit_report_date": "Required for audited documents"})

#     # -----------------------------------------------------------

#     def calculate_period_dates(self, fy, period_type, month, quarter):

#         fy = fy.replace("FY", "").replace(" ", "")
#         start_year = int(fy.split('-')[0])

#         if period_type == PeriodType.YEARLY:
#             return date(start_year, 4, 1), date(start_year + 1, 3, 31)

#         if period_type == PeriodType.MONTHLY:
#             year = start_year if month >= 4 else start_year + 1
#             start_date = date(year, month, 1)
#             end_date = start_date + relativedelta(months=1, days=-1)
#             return start_date, end_date

#         if period_type == PeriodType.QUARTERLY:
#             mapping = {
#                 1: (4, 6),
#                 2: (7, 9),
#                 3: (10, 12),
#                 4: (1, 3),
#             }
#             sm, em = mapping[quarter]
#             year = start_year if quarter in (1, 2, 3) else start_year + 1

#             start_date = date(year, sm, 1)
#             end_date = date(year, em, 1) + relativedelta(months=1, days=-1)
#             return start_date, end_date

#         raise serializers.ValidationError('Invalid period configuration')


# #------------ Model serializer ----------
# class FinancialDocumentCreateSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = FinancialDocument
#         fields = [
#             'company',
#             'document_type',
#             'document_tag',
#             'financial_year',
#             'period_type',
#             'period_start_date',
#             'period_end_date',
#             'period_code',
#             'version',
#             'file_name',
#             'file_path',
#             'file_size',
#             'mime_type',
#             'auditor_name',
#             'audit_report_date',
#             'audit_firm_name',
           
#         ]



# #------------ Response serializer ----------
# class FinancialDocumentSerializer(serializers.ModelSerializer):


#     class Meta:
#         model = FinancialDocument
#         fields = [
#             'document_id',
#             'document_type',
#             'document_tag',
#             'financial_year',
#             'period_type',
#             'period_start_date',
#             'period_end_date',
#             'period_code',
#             'version',
#             'file_name',
#             'file_path',
#             'file_size',
#             'mime_type',
#             'is_verified',
#             'verified_at',
#             'auditor_name',
#             'audit_report_date',
#             'audit_firm_name',
#             'created_at',
#             'updated_at',
#         ]
#         read_only_fields = [
#             'document_id',
#             'is_verified',
#             'verified_at',
#             'created_at',
#             'updated_at',
#         ]



# class BulkUploadSerializer(serializers.Serializer):
#     documents = serializers.JSONField()
#     files = serializers.ListField(
#         child=serializers.FileField(),
#         min_length=1,
#         max_length=50
#     )

#     def validate(self, data):
#         if len(data["documents"]) != len(data["files"]):
#             raise serializers.ValidationError(
#                 {"files": "Number of files must match number of documents"}
#         )
#         return data



# class BulkUpdateSerializer(serializers.Serializer):
#     updates = serializers.JSONField()

#     def validate(self, data):
#         for item in data["updates"]:
#             if "document_id" not in item:
#                 raise serializers.ValidationError({
#                     "updates": "document_id is required for each update item"
#                 })

#             if "metadata" not in item:
#                 raise serializers.ValidationError({
#                     "updates": "metadata is required for each update item"
#                 })

#             if not isinstance(item["metadata"], dict):
#                 raise serializers.ValidationError({
#                     "metadata": "metadata must be a dictionary"
#                 })

#         return data


# class BulkDeleteSerializer(serializers.Serializer):
#     document_ids = serializers.ListField(
#         child=serializers.IntegerField(),
#         min_length=1
#     )



# class DocumentFilterSerializer(serializers.Serializer):
#     company = serializers.IntegerField(required=False)
#     document_type = serializers.ChoiceField(choices=DocumentType.values, required=False)
#     document_tag = serializers.ChoiceField(choices=DocumentTag.values, required=False)
#     financial_year = serializers.CharField(required=False)
#     is_verified = serializers.BooleanField(required=False)
#     period_type = serializers.ChoiceField(choices=PeriodType.values, required=False)




# --------------------- Upload/metadata serializer ---------------------
class FinancialDocumentUploadSerializer(serializers.Serializer):
    # ---------- Meta fields ----------
    document_type = serializers.ChoiceField(choices=DocumentType.values)
    document_tag = serializers.ChoiceField(choices=DocumentTag.values)

    financial_year = serializers.CharField(max_length=9)
    period_type = serializers.ChoiceField(choices=PeriodType.values)

    period_month = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=12)
    period_quarter = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=4)

    # NOTE: file field removed. Only file_url is allowed.
    auditor_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    audit_report_date = serializers.DateField(required=False, allow_null=True)
    audit_firm_name = serializers.CharField(max_length=255, required=False, allow_blank=True)

    auto_verify = serializers.BooleanField(default=True)
    file_url = serializers.CharField(required=False, allow_blank=True)  # accept raw string URL (relative ok)

    def validate(self, data):
        company_id = self.context.get("company_id")
        if not company_id:
            raise serializers.ValidationError("company_id missing from context")

        company = CompanyInformation.objects.filter(pk=company_id, del_flag=0).first()
        if not company:
            raise serializers.ValidationError("Invalid company ID")

        # If partial update → redirect to partial validator
        if self.partial:
            return self.validate_partial(data)

        # For create (not partial) file_url is required (we removed file uploads)
        file_url = data.get("file_url")
        if not file_url:
            raise serializers.ValidationError({"file_url": "file_url is required for create (temp file URL)"})

        return self._common_validation(data, company)

    def validate_partial(self, data):
        company_id = self.context.get("company_id")
        company = CompanyInformation.objects.filter(pk=company_id, del_flag=0).first()
        if not company:
            raise serializers.ValidationError("Invalid company ID")
        return self._common_validation(data, company, is_partial=True)

    def _common_validation(self, data, company, is_partial=False):
        doc_type = data.get("document_type")
        doc_tag = data.get("document_tag")
        fy = data.get("financial_year")
        period_type = data.get("period_type")

        month = data.get("period_month")
        quarter = data.get("period_quarter")

        # Period rules (strict for non-partial)
        if not is_partial:
            self._validate_period_rules(period_type, month, quarter)

        # business rules
        if not is_partial or ("period_type" in data or "document_type" in data):
            self._validate_business_rules(company, doc_type, period_type)

        # audited rules
        if doc_tag == DocumentTag.AUDITED:
            self._validate_audited_rules(data, is_partial)

        # ---------- Generate period dates only if all data present ----------
        if fy and period_type:
            start_date, end_date = self.calculate_period_dates(fy, period_type, month, quarter)
            data["period_start_date"] = start_date
            data["period_end_date"] = end_date

            if period_type == PeriodType.MONTHLY:
                data["period_code"] = f"{start_date.year}-{start_date.month:02d}"
            elif period_type == PeriodType.QUARTERLY:
                data["period_code"] = f"Q{quarter}-{start_date.year}"
            else:
                data["period_code"] = None

        # version logic (for create/update full)
        if not is_partial:
            latest = FinancialDocument.objects.filter(
                company_id=company.company_id,
                document_type=doc_type,
                period_start_date=data["period_start_date"],
                period_end_date=data["period_end_date"],
                document_tag=doc_tag,
                del_flag=0
            ).order_by("-version").first()
            data["version"] = (latest.version + 1) if latest else 1

        return data

    def _validate_period_rules(self, period_type, month, quarter):
        if period_type == PeriodType.MONTHLY and not month:
            raise serializers.ValidationError({"period_month": "Required for monthly documents"})
        if period_type == PeriodType.QUARTERLY and not quarter:
            raise serializers.ValidationError({"period_quarter": "Required for quarterly documents"})
        if period_type == PeriodType.YEARLY and (month or quarter):
            raise serializers.ValidationError("Monthly/quarterly values not allowed for yearly documents")

    def _validate_business_rules(self, company, doc_type, period_type):
        if doc_type == DocumentType.GSTR_3B and period_type != PeriodType.MONTHLY:
            raise serializers.ValidationError({"period_type": "GSTR-3B must be monthly"})
        if doc_type == DocumentType.GSTR_9 and period_type != PeriodType.YEARLY:
            raise serializers.ValidationError({"period_type": "GSTR-9 must be yearly"})
        if doc_type == DocumentType.FINANCIAL_STATEMENT and period_type != PeriodType.YEARLY:
            raise serializers.ValidationError({"period_type": "Financial statements must be yearly"})

    def _validate_audited_rules(self, data, is_partial):
        if not is_partial:
            if not data.get("auditor_name"):
                raise serializers.ValidationError({"auditor_name": "Required for audited documents"})
            if not data.get("audit_report_date"):
                raise serializers.ValidationError({"audit_report_date": "Required for audited documents"})
        else:
            if "auditor_name" in data and not data.get("auditor_name"):
                raise serializers.ValidationError({"auditor_name": "Required for audited documents"})
            if "audit_report_date" in data and not data.get("audit_report_date"):
                raise serializers.ValidationError({"audit_report_date": "Required for audited documents"})

    def calculate_period_dates(self, fy, period_type, month, quarter):
        fy = fy.replace("FY", "").replace(" ", "")
        start_year = int(fy.split('-')[0])

        if period_type == PeriodType.YEARLY:
            return date(start_year, 4, 1), date(start_year + 1, 3, 31)

        if period_type == PeriodType.MONTHLY:
            year = start_year if month >= 4 else start_year + 1
            start_date = date(year, month, 1)
            end_date = start_date + relativedelta(months=1, days=-1)
            return start_date, end_date

        if period_type == PeriodType.QUARTERLY:
            mapping = {1: (4, 6), 2: (7, 9), 3: (10, 12), 4: (1, 3)}
            sm, em = mapping[quarter]
            year = start_year if quarter in (1, 2, 3) else start_year + 1
            start_date = date(year, sm, 1)
            end_date = date(year, em, 1) + relativedelta(months=1, days=-1)
            return start_date, end_date

        raise serializers.ValidationError('Invalid period configuration')


# ---------- Response & Model serializers remain unchanged ----------
class FinancialDocumentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialDocument
        fields = [
            'company',
            'document_type',
            'document_tag',
            'financial_year',
            'period_type',
            'period_start_date',
            'period_end_date',
            'period_code',
            'version',
            'file_name',
            'file_path',
            'file_size',
            'mime_type',
            'auditor_name',
            'audit_report_date',
            'audit_firm_name',
        ]


class FinancialDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialDocument
        fields = [
            'document_id',
            'document_type',
            'document_tag',
            'financial_year',
            'period_type',
            'period_start_date',
            'period_end_date',
            'period_code',
            'version',
            'file_name',
            'file_path',
            'file_size',
            'mime_type',
            'is_verified',
            'verified_at',
            'auditor_name',
            'audit_report_date',
            'audit_firm_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['document_id', 'is_verified', 'verified_at', 'created_at', 'updated_at']


# --------------------- Bulk serializers (raw JSON only) ---------------------
class BulkUploadSerializer(serializers.Serializer):
    documents = serializers.JSONField()  # raw JSON array expected in request body

    def validate(self, data):
        raw_docs = data.get("documents")

        # If request was application/json the JSON will already be parsed.
        # If somehow it's a string (shouldn't be with application/json), try to parse.
        if isinstance(raw_docs, str):
            try:
                raw_docs = json.loads(raw_docs)
            except Exception:
                raise serializers.ValidationError({"documents": "Invalid JSON format"})
        if not isinstance(raw_docs, list):
            raise serializers.ValidationError({"documents": "Must be a list of document objects"})
        data["documents"] = raw_docs

        # Validate each doc must contain file_url (since files are removed)
        for idx, doc in enumerate(raw_docs):
            if not isinstance(doc, dict):
                raise serializers.ValidationError({"documents": f"Document at index {idx} must be an object"})
            if not doc.get("file_url"):
                raise serializers.ValidationError({"documents": f"Document at index {idx} requires file_url"})
        return data


class BulkUpdateSerializer(serializers.Serializer):
    updates = serializers.JSONField()

    def validate(self, data):
        updates = data.get("updates")
        if isinstance(updates, str):
            try:
                updates = json.loads(updates)
            except Exception:
                raise serializers.ValidationError({"updates": "Invalid JSON format"})
        if not isinstance(updates, list):
            raise serializers.ValidationError({"updates": "Must be a list"})
        data["updates"] = updates

        for item in updates:
            if "document_id" not in item:
                raise serializers.ValidationError({"updates": "document_id is required for each update item"})
            if "metadata" not in item:
                raise serializers.ValidationError({"updates": "metadata is required for each update item"})
            if not isinstance(item["metadata"], dict):
                raise serializers.ValidationError({"metadata": "metadata must be a dictionary"})
        return data


class BulkDeleteSerializer(serializers.Serializer):
    document_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)


class DocumentFilterSerializer(serializers.Serializer):
    company = serializers.IntegerField(required=False)
    document_type = serializers.ChoiceField(choices=DocumentType.values, required=False)
    document_tag = serializers.ChoiceField(choices=DocumentTag.values, required=False)
    financial_year = serializers.CharField(required=False)
    is_verified = serializers.BooleanField(required=False)
    period_type = serializers.ChoiceField(choices=PeriodType.values, required=False)
