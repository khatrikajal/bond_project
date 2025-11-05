from rest_framework import serializers
from django.db import transaction
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from apps.kyc.issuer_kyc.models.CompanyAdressModel import CompanyAddress
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
import phonenumbers
import re
import os
import uuid


class CompanyAddressSerializer(serializers.ModelSerializer):
    # Add file field for uploads
    address_proof_file = serializers.FileField(
        required=False,
        allow_null=True,
        help_text="Upload address proof (PDF, JPG, JPEG, PNG, max 5MB)"
    )

    class Meta:
        model = CompanyAddress
        fields = [
            'address_id',
            'company',
            'registered_office_address',
            'city',
            'state_ut',
            'pin_code',
            'country',
            'company_contact_email',
            'company_contact_phone',
            'address_type',
            'address_proof_file',
            'created_at',
            'user_id_updated_by_id'
        ]
        read_only_fields = ['address_id', 'created_at', 'user_id_updated_by_id']

    # -----------------------------
    # FIELD-LEVEL VALIDATIONS
    # -----------------------------
    def validate_pin_code(self, value):
        if not re.match(r'^\d{6}$', str(value)):
            raise serializers.ValidationError("PIN code must be exactly 6 digits.")
        return value

    def validate_company_contact_email(self, value):
        if value and not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
            raise serializers.ValidationError("Invalid company email address format.")
        return value

    def validate_company_contact_phone(self, value):
        try:
            phone = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(phone):
                raise serializers.ValidationError("Invalid or non-existent phone number.")
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError(
                "Invalid phone number format. Use E.164 format like +14155552671."
            )
        return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)

    def validate_country(self, value):
        if not value.strip():
            raise serializers.ValidationError("Country cannot be blank.")
        return value

    # -----------------------------
    # FILE VALIDATION
    # -----------------------------
    def validate_address_proof_file(self, file):
        if not file:
            return file

        allowed_ext = ['.jpg', '.jpeg', '.png', '.pdf']
        max_size_mb = 5
        ext = os.path.splitext(file.name)[1].lower()

        if ext not in allowed_ext:
            raise serializers.ValidationError("Unsupported file type. Allowed: JPG, JPEG, PNG, PDF.")
        if file.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError("File too large (max 5MB allowed).")

        return file

    # -----------------------------
    # OBJECT-LEVEL VALIDATION
    # -----------------------------
    def validate(self, attrs):
        company = attrs.get("company") or getattr(self.instance, "company", None)
        address_type = attrs.get("address_type") or getattr(self.instance, "address_type", None)

        if company and address_type is not None:
            existing_qs = CompanyAddress.objects.filter(company=company, del_flag=0)
            if self.instance:
                existing_qs = existing_qs.exclude(pk=self.instance.pk)

            if address_type == 0:  # Registered
                if existing_qs.filter(address_type__in=[0, 2]).exists():
                    raise serializers.ValidationError(
                        "A registered address already exists for this company."
                    )
            elif address_type == 1:  # Correspondence
                if existing_qs.filter(address_type__in=[1, 2]).exists():
                    raise serializers.ValidationError(
                        "A correspondence address already exists for this company."
                    )
            elif address_type == 2:  # Both
                if existing_qs.filter(address_type__in=[0, 1, 2]).exists():
                    raise serializers.ValidationError(
                        "An address already exists for this company. Cannot add 'BOTH' type."
                    )

        city = attrs.get("city")
        state_ut = attrs.get("state_ut")
        if address_type == 2 and (not city or not state_ut):
            raise serializers.ValidationError("City and State/UT are required when address type is BOTH.")

        return attrs

    # -----------------------------
    # FILE SAVE HELPER
    # -----------------------------
    def _save_file(self, file):
        """Save uploaded file to /uploads/company_address/ and return stored path."""
        folder = "uploads/company_address"
        filename = f"{uuid.uuid4()}_{file.name}"
        saved_path = default_storage.save(os.path.join(folder, filename), ContentFile(file.read()))
        return saved_path

    # -----------------------------
    # CREATE WITH TRANSACTION + USER TRACKING + FILE HANDLING
    # -----------------------------
    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        file = validated_data.pop("address_proof_file", None)

        with transaction.atomic():
            if user and user.is_authenticated:
                validated_data["user_id_updated_by"] = user

            # Handle file saving
            if file:
                saved_path = self._save_file(file)
                validated_data["address_proof_file"] = saved_path

            address = super().create(validated_data)
            company = validated_data.get("company")

            # Optional: update onboarding step
            try:
                if hasattr(company, "application") and company.application:
                    application = company.application
                    if hasattr(application, "update_state"):
                        application.update_state(
                            step_number=2,
                            completed=True,
                            record_ids=[address.address_id]
                        )
            except Exception as e:
                raise serializers.ValidationError(f"Failed to update application state: {str(e)}")

        return address

    # -----------------------------
    # UPDATE WITH TRANSACTION + USER TRACKING + FILE HANDLING
    # -----------------------------
    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        file = validated_data.pop("address_proof_file", None)

        with transaction.atomic():
            if user and user.is_authenticated:
                instance.user_id_updated_by = user
                instance.save(update_fields=["user_id_updated_by"])

            # Handle file replacement
            if file:
                if instance.address_proof_file and default_storage.exists(instance.address_proof_file.name):
                    default_storage.delete(instance.address_proof_file.name)
                saved_path = self._save_file(file)
                validated_data["address_proof_file"] = saved_path

            updated_instance = super().update(instance, validated_data)
            company = updated_instance.company

            # Optional: update onboarding step
            try:
                if hasattr(company, "application") and company.application:
                    application = company.application
                    if hasattr(application, "update_state"):
                        application.update_state(
                            step_number=2,
                            completed=True,
                            record_ids=[updated_instance.address_id]
                        )
            except Exception as e:
                raise serializers.ValidationError(f"Failed to update application state: {str(e)}")

        return updated_instance

    # -----------------------------
    # UNIVERSAL SOFT DELETE (no is_same_address)
    # -----------------------------
    def soft_delete_all(self, company):
        """
        Soft delete all active address records for the given company
        (sets del_flag=1 for all where del_flag=0)
        """
        from django.utils import timezone
        deleted_records = []

        with transaction.atomic():
            qs = CompanyAddress.objects.filter(company=company, del_flag=0)
            if not qs.exists():
                raise serializers.ValidationError("No active addresses found for this company.")

            # Track which address types are being deleted
            deleted_records = list(qs.values_list("address_type", flat=True))
            qs.update(del_flag=1, updated_at=timezone.now())

        # Map address_type integers to human-readable names
        type_map = {0: "REGISTERED", 1: "CORRESPONDENCE", 2: "BOTH"}
        deleted_labels = [f"{type_map.get(t, 'UNKNOWN')} (address_type={t})" for t in deleted_records]

        return deleted_labels
    
    # -----------------------------
    # GET ALL ACTIVE ADDRESSES (moved transaction logic here)
    # -----------------------------
    def get_all_active_addresses(self):
        """
        Fetch all active (del_flag=0) addresses grouped by company.
        Each company has 'registered' and 'correspondence' sections.
        If address_type=2 (BOTH), the same data fills both sections.
        """
        with transaction.atomic():
            companies = CompanyInformation.objects.all()
            if not companies.exists():
                raise serializers.ValidationError("No companies found.")

            grouped_data = []

            for company in companies:
                addresses = CompanyAddress.objects.filter(company=company, del_flag=0)
                if not addresses.exists():
                    continue

                both_address = addresses.filter(address_type=2).first()
                registered = addresses.filter(address_type=0).first()
                correspondence = addresses.filter(address_type=1).first()

                company_data = {
                    "company_id": company.company_id,
                    "company_name": getattr(company, "company_name", None),
                    "addresses": {
                        "registered": None,
                        "correspondence": None
                    }
                }

                if both_address:
                    # Both registered + correspondence same
                    company_data["addresses"]["registered"] = {
                        "address_id": both_address.address_id,
                        "registered_office": both_address.registered_office_address,
                        "city": both_address.city,
                        "state_ut": both_address.state_ut,
                        "pin_code": both_address.pin_code,
                        "country": both_address.country,
                        "contact_email": both_address.company_contact_email,
                        "contact_phone": both_address.company_contact_phone,
                    }
                    company_data["addresses"]["correspondence"] = company_data["addresses"]["registered"]

                else:
                    if registered:
                        company_data["addresses"]["registered"] = {
                            "address_id": registered.address_id,
                            "registered_office": registered.registered_office_address,
                            "city": registered.city,
                            "state_ut": registered.state_ut,
                            "pin_code": registered.pin_code,
                            "country": registered.country,
                            "contact_email": registered.company_contact_email,
                            "contact_phone": registered.company_contact_phone,
                        }
                    if correspondence:
                        company_data["addresses"]["correspondence"] = {
                            "address_id": correspondence.address_id,
                            "registered_office": correspondence.registered_office_address,
                            "city": correspondence.city,
                            "state_ut": correspondence.state_ut,
                            "pin_code": correspondence.pin_code,
                            "country": correspondence.country,
                            "contact_email": correspondence.company_contact_email,
                            "contact_phone": correspondence.company_contact_phone,
                        }

                grouped_data.append(company_data)

        return grouped_data
    
        # -----------------------------
    # FILE VALIDATION & SAVING HELPERS (for OCR upload API)
    # -----------------------------
    def validate_file(self, file):
        allowed_ext = ['.jpg', '.jpeg', '.png', '.pdf']
        max_size_mb = 5
        ext = os.path.splitext(file.name)[1].lower()

        if ext not in allowed_ext:
            raise serializers.ValidationError("Unsupported file type. Allowed: JPG, PNG, PDF.")
        if file.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError("File too large (max 5MB allowed).")

        return file

    def save_uploaded_file(self, file):
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        import uuid

        folder = "company_docs"
        file_name = f"{folder}/{uuid.uuid4()}_{file.name}"
        saved_path = default_storage.save(file_name, ContentFile(file.read()))
        file_url = default_storage.url(saved_path)

        return {"file_path": default_storage.path(saved_path), "file_url": file_url}

    