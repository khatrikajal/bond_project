from rest_framework import serializers
from django.db import transaction
from apps.kyc.issuer_kyc.models.BankDetailsModel import BankDetails
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from apps.kyc.issuer_kyc.services.onboarding_service import update_step_4_status
from apps.kyc.issuer_kyc.services.bank_details.constants import BankDetailsConfig
import re
import logging



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

    def create(self, validated_data):
        """Handle POST - Create new bank details"""
        company = self.context.get("company")

        
        with transaction.atomic():
            # Get or create
            bank, created = BankDetails.objects.get_or_create(
                company=company,
                defaults=validated_data
            )
            
            # If already exists, update it
            if not created:
                for field, value in validated_data.items():
                    setattr(bank, field, value)
                
                # New record is always unverified
                bank.is_verified = False
                bank.verified_at = None
                bank.verified_data_hash = None
                bank.save()
            
            # Update onboarding step 4
            self._update_onboarding_step(company, bank)
            
            return bank

    def update(self, instance, validated_data):
        """Handle PUT/PATCH - Update existing bank details"""
        company = self.context["company"]

        
        with transaction.atomic():
            # ✅ CHECK: If verified, check for critical field changes
            should_invalidate = False
            if instance.is_verified:
                should_invalidate = self._critical_fields_changed(instance, validated_data)
            
            # Update all provided fields
            for field, value in validated_data.items():
                setattr(instance, field, value)
            
            # ✅ INVALIDATE verification if critical fields changed
            if should_invalidate:
                instance.is_verified = False
                instance.verified_at = None
                instance.verified_data_hash = None
                logger.info(
                    f"Invalidated verification for bank_detail_id={instance.bank_detail_id} "
                    f"due to critical field changes"
                )
            
            instance.save()
            
            # Update onboarding step 4
            if company:
               
                self._update_onboarding_step(company, instance)
            
            return instance

    def _critical_fields_changed(self, instance, new_data):
        """Check if any critical field changed"""
        for field in BankDetailsConfig.CRITICAL_FIELDS:
            # Only check fields that are being updated
            if field not in new_data:
                continue
            
            old_value = str(getattr(instance, field, '')).strip().lower()
            new_value = str(new_data.get(field, '')).strip().lower()
            
            if old_value != new_value:
                logger.info(f"Critical field '{field}' changed for bank_detail_id={instance.bank_detail_id}")
                return True
        
        return False
    
    def _update_onboarding_step(self, company, bank):
        """Update onboarding step 4 status"""
        try:
            if hasattr(company, "application") and company.application:
                update_step_4_status(company.application, bank_ids=bank.bank_detail_id)
        except Exception as e:
            logger.exception(f"Failed to update onboarding step for company {company.pk}")
            raise serializers.ValidationError(
                f"Failed to update onboarding step: {str(e)}"
            )
        




