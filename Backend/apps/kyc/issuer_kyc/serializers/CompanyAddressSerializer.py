# from rest_framework import serializers
# from django.db import transaction
# from apps.kyc.issuer_kyc.models.CompanyAdressModel import CompanyAddress
# from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
# import re
# import phonenumbers
# class CompanyAddressSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CompanyAddress
#         fields = [
#             'address_id',
#             'company',
#             'registered_office_address',
#             'city',
#             'state_ut',
#             'pin_code',
#             'country',
#             'company_contact_email',
#             'company_contact_phone',
#             'address_type',
#             'created_at'
#         ]
#         read_only_fields = ['address_id', 'created_at']

#     # -----------------------------
#     # FIELD-LEVEL VALIDATIONS
#     # -----------------------------
#     def validate_pin_code(self, value):
#         if not re.match(r'^\d{6}$', str(value)):
#             raise serializers.ValidationError("PIN code must be exactly 6 digits.")
#         return value

#     def validate_company_contact_email(self, value):
#         if value and not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
#             raise serializers.ValidationError("Invalid company email address format.")
#         return value

#     def validate_company_contact_phone(self, value):
#         try:
#             phone = phonenumbers.parse(value, None)
#             if not phonenumbers.is_valid_number(phone):
#                 raise serializers.ValidationError("Invalid or non-existent phone number.")
#         except phonenumbers.NumberParseException:
#             raise serializers.ValidationError(
#                 "Invalid phone number format. Use E.164 format like +14155552671."
#             )
#         return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)

#     def validate_country(self, value):
#         if not value.strip():
#             raise serializers.ValidationError("Country cannot be blank.")
#         return value

#     # -----------------------------
#     # OBJECT-LEVEL VALIDATION
#     # -----------------------------
#     def validate(self, attrs):
#         company = attrs.get("company")
#         address_type = attrs.get("address_type")

#         if company and address_type is not None:
#             existing_qs = CompanyAddress.objects.filter(
#                 company=company,
#                 del_flag=0  
#             )
#             if self.instance:
#                 existing_qs = existing_qs.exclude(pk=self.instance.pk)

#             if address_type == 0:  # Registered
#                 if existing_qs.filter(address_type__in=[0, 2]).exists():
#                     raise serializers.ValidationError(
#                         "A registered address already exists for this company."
#                     )
#             elif address_type == 1:  # Correspondence
#                 if existing_qs.filter(address_type__in=[1, 2]).exists():
#                     raise serializers.ValidationError(
#                         "A correspondence address already exists for this company."
#                     )
#             elif address_type == 2:  # Both
#                 if existing_qs.filter(address_type__in=[0, 1, 2]).exists():
#                     raise serializers.ValidationError(
#                         "An address already exists for this company. Cannot add 'BOTH' type."
#                     )

#         city = attrs.get("city")
#         state_ut = attrs.get("state_ut")
#         if address_type == 2 and (not city or not state_ut):
#             raise serializers.ValidationError("City and State/UT are required when address type is BOTH.")
#         return attrs

#     # -----------------------------
#     # CREATE WITH TRANSACTION ATOMIC
#     # -----------------------------
#     def create(self, validated_data):
#         company = validated_data.get("company")

#         # ✅ Wrap both DB operations in a transaction
#         with transaction.atomic():
#             address = super().create(validated_data)

#             try:
#                 if hasattr(company, "application") and company.application:
#                     application = company.application
#                     if hasattr(application, "update_state"):
#                         application.update_state(
#                             step_number=2,
#                             completed=True,
#                             record_ids=[address.address_id]
#                         )
#             except Exception as e:
#                 # ❌ If anything fails in update_state, rollback entire transaction
#                 raise serializers.ValidationError(
#                     f"Failed to update application state: {str(e)}"
#                 )

#         return address

#     # -----------------------------
#     # UPDATE (optional transaction)
#     # -----------------------------
#     def update(self, instance, validated_data):
#         with transaction.atomic():
#             updated_instance = super().update(instance, validated_data)
#             # Optionally handle update_state here as well if needed
#             return updated_instance



from rest_framework import serializers
from django.db import transaction
from apps.kyc.issuer_kyc.models.CompanyAdressModel import CompanyAddress
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation

import re
import phonenumbers


class CompanyAddressSerializer(serializers.ModelSerializer):
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
            'created_at',
            'user_id_updated_by_id'
        ]
        read_only_fields = ['address_id', 'created_at', 'user_id_updated_by_id']

    # -----------------------------
    # FIELD VALIDATIONS
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
    # OBJECT LEVEL VALIDATION
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

    # # -----------------------------
    # # CREATE WITH TRANSACTION
    # # -----------------------------
    # def create(self, validated_data):
    #     company = validated_data.get("company")
    #     with transaction.atomic():
    #         address = super().create(validated_data)
    #         try:
    #             if hasattr(company, "application") and company.application:
    #                 application = company.application
    #                 if hasattr(application, "update_state"):
    #                     application.update_state(
    #                         step_number=2,
    #                         completed=True,
    #                         record_ids=[address.address_id]
    #                     )
    #         except Exception as e:
    #             raise serializers.ValidationError(f"Failed to update application state: {str(e)}")
    #     return address

    # # -----------------------------
    # # UPDATE WITH TRANSACTION
    # # -----------------------------
    # def update(self, instance, validated_data):
    #     with transaction.atomic():
    #         updated_instance = super().update(instance, validated_data)
    #         company = updated_instance.company
    #         try:
    #             if hasattr(company, "application") and company.application:
    #                 application = company.application
    #                 if hasattr(application, "update_state"):
    #                     application.update_state(
    #                         step_number=2,
    #                         completed=True,
    #                         record_ids=[updated_instance.address_id]
    #                     )
    #         except Exception as e:
    #             raise serializers.ValidationError(f"Failed to update application state: {str(e)}")
    #         return updated_instance

    # -----------------------------
    # CREATE WITH TRANSACTION + USER TRACKING
    # -----------------------------
    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        with transaction.atomic():
            # Attach user to BaseModel tracking field
            if user and user.is_authenticated:
                validated_data["user_id_updated_by"] = user

            address = super().create(validated_data)

            company = validated_data.get("company")
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
        # UPDATE WITH TRANSACTION + USER TRACKING
        # -----------------------------
    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        with transaction.atomic():
            if user and user.is_authenticated:
                instance.user_id_updated_by = user
                instance.save(update_fields=["user_id_updated_by"])

            updated_instance = super().update(instance, validated_data)

            company = updated_instance.company
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