from rest_framework import serializers
from decimal import Decimal
from ..models.borrowing_details import BorrowingDetails, BorrowingType, RepaymentTerms


# =====================================================================
# Main Serializer (Retrieve / Update)
# =====================================================================
class BorrowingDetailsSerializer(serializers.ModelSerializer):
    borrowing_id = serializers.UUIDField(read_only=True)


    created_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')

    borrowing_type = serializers.ChoiceField(choices=BorrowingType.choices)
    repayment_terms = serializers.ChoiceField(choices=RepaymentTerms.choices)

    borrowing_type_display = serializers.CharField(source='get_borrowing_type_display', read_only=True)
    repayment_terms_display = serializers.CharField(source='get_repayment_terms_display', read_only=True)

    class Meta:
        model = BorrowingDetails
        fields = [
            "borrowing_id",
           
            "lender_name",
            "lender_amount",
            "borrowing_type",
            "borrowing_type_display",
            "repayment_terms",
            "repayment_terms_display",
            "monthly_principal_payment",
            "interest_payment_percentage",
            "monthly_interest_payment",
            "is_del",
            "created_at",
            "updated_at",
            "user_id_updated_by",
        ]
        read_only_fields = ["borrowing_id", "created_at", "updated_at", "is_del"]

    # ================================================================
    # VALIDATIONS
    # ================================================================
    def validate_lender_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Lender amount must be greater than 0")
        return value

    def validate_monthly_principal_payment(self, value):
        if value < 0:
            raise serializers.ValidationError("Monthly principal payment cannot be negative")
        return value

    def validate_monthly_interest_payment(self, value):
        if value < 0:
            raise serializers.ValidationError("Monthly interest payment cannot be negative")
        return value

    def validate_interest_payment_percentage(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Interest percentage must be between 0 and 100")
        return value

    def validate(self, attrs):
        lender_amount = attrs.get("lender_amount")
        interest_rate = attrs.get("interest_payment_percentage")

        if lender_amount and interest_rate:
            calculated = (lender_amount * interest_rate / Decimal("100")) / 12
            provided = attrs.get("monthly_interest_payment")

            if provided is None:
                attrs["monthly_interest_payment"] = calculated
            else:
                # Allow 1% tolerance
                tolerance = calculated * Decimal("0.01")
                if abs(calculated - provided) > tolerance:
                    attrs["monthly_interest_payment"] = calculated

        return attrs


# =====================================================================
# List Serializer
# =====================================================================
class BorrowingDetailsListSerializer(serializers.ModelSerializer):
    borrowing_type_display = serializers.CharField(source='get_borrowing_type_display', read_only=True)
    repayment_terms_display = serializers.CharField(source='get_repayment_terms_display', read_only=True)

    class Meta:
        model = BorrowingDetails
        fields = [
            "borrowing_id",
            "lender_name",
            "lender_amount",
            "borrowing_type",
            "borrowing_type_display",
            "repayment_terms",
            "repayment_terms_display",
            "monthly_principal_payment",
            "interest_payment_percentage",
            "monthly_interest_payment",
            "created_at",
        ]


# =====================================================================
# Create Serializer (POST)
# =====================================================================
class BorrowingDetailsCreateSerializer(serializers.ModelSerializer):

    borrowing_type = serializers.ChoiceField(choices=BorrowingType.choices)
    repayment_terms = serializers.ChoiceField(choices=RepaymentTerms.choices)

    class Meta:
        model = BorrowingDetails
        fields = [
            "lender_name",
            "lender_amount",
            "borrowing_type",
            "repayment_terms",
            "monthly_principal_payment",
            "interest_payment_percentage",
            "monthly_interest_payment",
        ]

    def validate(self, attrs):

        lender_amount = attrs.get("lender_amount")
        interest_rate = attrs.get("interest_payment_percentage")

        # Auto-calc monthly interest if missing
        if lender_amount and interest_rate:
            if not attrs.get("monthly_interest_payment"):
                attrs["monthly_interest_payment"] = (lender_amount * interest_rate / Decimal("100")) / 12
        
        return attrs


# =====================================================================
# Summary Serializer
# =====================================================================
class BorrowingSummarySerializer(serializers.Serializer):
    total_borrowings = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_monthly_principal = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_monthly_interest = serializers.DecimalField(max_digits=18, decimal_places=2)
    average_interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    by_type = serializers.DictField()


# =====================================================================
# CHOICES SERIALIZERS
# =====================================================================
class BorrowingTypeChoiceSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()


class RepaymentTermsChoiceSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()
