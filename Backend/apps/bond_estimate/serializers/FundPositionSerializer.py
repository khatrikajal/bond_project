from rest_framework import serializers
from apps.bond_estimate.models.FundPositionModel import FundPosition


class FundPositionSerializer(serializers.ModelSerializer):
    fund_position_id = serializers.UUIDField(read_only=True)
    company_name = serializers.CharField(source="company.company_name", read_only=True)

    class Meta:
        model = FundPosition
        fields = [
            "fund_position_id",
            "company_name",
            "cash_balance_date",
            "bank_balance_date",
            "cash_balance_amount",
            "bank_balance_amount",
            "remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["fund_position_id", "created_at", "updated_at"]

    def validate(self, attrs):
        if attrs.get("cash_balance_amount") is not None and attrs["cash_balance_amount"] < 0:
            raise serializers.ValidationError({"cash_balance_amount": "Cannot be negative"})
        if attrs.get("bank_balance_amount") is not None and attrs["bank_balance_amount"] < 0:
            raise serializers.ValidationError({"bank_balance_amount": "Cannot be negative"})
        return attrs


class FundPositionListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.company_name", read_only=True)

    class Meta:
        model = FundPosition
        fields = [
            "fund_position_id",
            "company_name",
            "cash_balance_date",
            "cash_balance_amount",
            "bank_balance_amount",
            "created_at",
        ]
