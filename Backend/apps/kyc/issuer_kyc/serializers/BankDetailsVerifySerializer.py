# serializers/bank_details_verify_serializer.py
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from apps.kyc.issuer_kyc.models.BankDetailsModel import BankDetails
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
import re
import logging

logger = logging.getLogger(__name__)


class BankDetailsVerifySerializer(serializers.Serializer):
    """Used to verify data from frontend"""
    bank_name = serializers.CharField()
    branch_name = serializers.CharField()
    account_number = serializers.CharField()
    account_type = serializers.ChoiceField(choices=["SAVINGS", "CURRENT"])
    ifsc_code = serializers.CharField()

    def validate_account_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Account number must be numeric.")
        return value

    def validate_ifsc_code(self, value):
        if not re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", value):
            raise serializers.ValidationError("Invalid IFSC code format.")
        return value