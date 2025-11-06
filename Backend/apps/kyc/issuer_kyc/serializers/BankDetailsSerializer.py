from rest_framework import serializers
from django.db import transaction
from apps.kyc.issuer_kyc.models.BankDetailsModel import BankDetails
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from apps.kyc.issuer_kyc.services.onboarding_service import update_step_4_status
import re
import logging
from django.utils import timezone


logger = logging.getLogger(__name__)



class BankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDetails
        fields = [
            "bank_detail_id",
            "bank_name",
            "branch_name",
            "account_number",
            "account_type",
            "ifsc_code",
            "is_verified",
            "verified_at",
        ]
        read_only_fields = ["is_verified", "verified_at"]

    def validate(self, data):
        # Account number
        if "account_number" in data:
            if not data["account_number"].isdigit():
                raise serializers.ValidationError({"account_number": "Must be numeric."})
            if not 9 <= len(data["account_number"]) <= 18:
                raise serializers.ValidationError({"account_number": "Invalid length for Indian bank account number."})

        # IFSC code
        if "ifsc_code" in data and not re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", data["ifsc_code"]):
            raise serializers.ValidationError({"ifsc_code": "Invalid IFSC code."})

        # Account type
        if "account_type" in data and data["account_type"] not in dict(BankDetails.ACCOUNT_TYPES):
            raise serializers.ValidationError({"account_type": "Invalid account type."})

        # Bank & branch names
        if "bank_name" in data and not data["bank_name"].strip():
            raise serializers.ValidationError({"bank_name": "Bank name cannot be empty."})
        if "branch_name" in data and not data["branch_name"].strip():
            raise serializers.ValidationError({"branch_name": "Branch name cannot be empty."})

        return data


    def save(self, company_id):
        company = CompanyInformation.objects.get(pk=company_id)
        with transaction.atomic():
            bank, _ = BankDetails.objects.get_or_create(company=company)

            # Update all provided fields
            for field, value in self.validated_data.items():
                setattr(bank, field, value)

            # Only verify if not already verified
            if not bank.is_verified:
                from apps.kyc.issuer_kyc.services.bank_details.verify_bank_details import verify_bank_details
                result = verify_bank_details(bank)

                if result.get("success"):
                    bank.is_verified = True
                    bank.verified_at = timezone.now()

            bank.save()

            # -------------------------
            # Update onboarding step 4
            # -------------------------
            try:
                if hasattr(company, "application") and company.application:
                    application = company.application
                    print("ffffffffffffffffffffffffffff")
                    update_step_4_status(application, bank_ids=bank.bank_detail_id)
            except Exception as e:
                raise serializers.ValidationError(
                    f"Failed to update onboarding step: {str(e)}"
                )

            return bank