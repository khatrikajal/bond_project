# from rest_framework import serializers
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
#         """Ensure PIN code is 6 digits."""
#         if not re.match(r'^\d{6}$', str(value)):
#             raise serializers.ValidationError("PIN code must be exactly 6 digits.")
#         return value

#     def validate_company_contact_email(self, value):
#         """Ensure valid company email format."""
#         if value and not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
#             raise serializers.ValidationError("Invalid company email address format.")
#         return value

#     def validate_company_contact_phone(self, value):
#         """Validate phone number globally using phonenumbers."""
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
#         """Ensure country is not empty."""
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

#             # Exclude current instance if updating
#             if self.instance:
#                 existing_qs = existing_qs.exclude(pk=self.instance.pk)

#             # Logic for each address type
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

#         # Example cross-field check
#         city = attrs.get("city")
#         state_ut = attrs.get("state_ut")
#         if address_type == 2 and (not city or not state_ut):
#             raise serializers.ValidationError("City and State/UT are required when address type is BOTH.")

#         return attrs

#     # -----------------------------
#     # CREATE WITH STATE UPDATE
#     # -----------------------------
#     def create(self, validated_data):
#         company = validated_data.get("company")
#         address = super().create(validated_data)

#         # ✅ Automatically update step state if company has application
#         if hasattr(company, "application") and company.application:
#             application = company.application
#             if hasattr(application, "update_state"):
#                 application.update_state(
#                     step_number=2,
#                     completed=True,
#                     record_ids=[address.address_id]  # convert to list
#                 )

#         return address

#     def update(self, instance, validated_data):
#         return super().update(instance, validated_data)


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
            'created_at'
        ]
        read_only_fields = ['address_id', 'created_at']

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
    # OBJECT-LEVEL VALIDATION
    # -----------------------------
    def validate(self, attrs):
        company = attrs.get("company")
        address_type = attrs.get("address_type")

        if company and address_type is not None:
            existing_qs = CompanyAddress.objects.filter(
                company=company,
                del_flag=0  
            )
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
    # CREATE WITH TRANSACTION ATOMIC
    # -----------------------------
    def create(self, validated_data):
        company = validated_data.get("company")

        # ✅ Wrap both DB operations in a transaction
        with transaction.atomic():
            address = super().create(validated_data)

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
                # ❌ If anything fails in update_state, rollback entire transaction
                raise serializers.ValidationError(
                    f"Failed to update application state: {str(e)}"
                )

        return address

    # -----------------------------
    # UPDATE (optional transaction)
    # -----------------------------
    def update(self, instance, validated_data):
        with transaction.atomic():
            updated_instance = super().update(instance, validated_data)
            # Optionally handle update_state here as well if needed
            return updated_instance