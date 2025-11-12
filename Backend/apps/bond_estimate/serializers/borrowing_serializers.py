from rest_framework import serializers
from decimal import Decimal
from ..model.borrowing_details import BorrowingDetails, BorrowingType, RepaymentTerms


class BorrowingDetailsSerializer(serializers.ModelSerializer):
    """Main serializer for Borrowing Details"""
    
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
            'borrowing_id',
            'company_id',
            'lender_name',
            'lender_amount',
            'borrowing_type',
            'borrowing_type_display',
            'repayment_terms',
            'repayment_terms_display',
            'monthly_principal_payment',
            'interest_payment_percentage',
            'monthly_interest_payment',
            'is_del',
            'created_at',
            'updated_at',
            'user_id_updated_by'
        ]
        read_only_fields = ['borrowing_id', 'created_at', 'updated_at']

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
        if attrs.get('interest_payment_percentage') and attrs.get('lender_amount'):
            lender_amount = attrs['lender_amount']
            interest_rate = attrs['interest_payment_percentage']
            calculated_interest = (lender_amount * interest_rate / 100) / 12
            if 'monthly_interest_payment' in attrs:
                provided_interest = attrs['monthly_interest_payment']
                tolerance = calculated_interest * Decimal('0.01')
                if abs(calculated_interest - provided_interest) > tolerance:
                    attrs['monthly_interest_payment'] = calculated_interest
        return attrs


class BorrowingDetailsListSerializer(serializers.ModelSerializer):
    borrowing_type_display = serializers.CharField(source='get_borrowing_type_display', read_only=True)
    repayment_terms_display = serializers.CharField(source='get_repayment_terms_display', read_only=True)

    class Meta:
        model = BorrowingDetails
        fields = [
            'borrowing_id',
            'lender_name',
            'lender_amount',
            'borrowing_type',
            'borrowing_type_display',
            'repayment_terms',
            'repayment_terms_display',
            'monthly_principal_payment',
            'interest_payment_percentage',
            'monthly_interest_payment',
            'created_at',
        ]


class BorrowingDetailsCreateSerializer(serializers.ModelSerializer):
    borrowing_type = serializers.ChoiceField(choices=BorrowingType.choices)
    repayment_terms = serializers.ChoiceField(choices=RepaymentTerms.choices)

    class Meta:
        model = BorrowingDetails
        fields = [
            'company_id',
            'lender_name',
            'lender_amount',
            'borrowing_type',
            'repayment_terms',
            'monthly_principal_payment',
            'interest_payment_percentage',
            'monthly_interest_payment',
        ]

    def validate(self, attrs):
        if attrs.get('interest_payment_percentage') and attrs.get('lender_amount'):
            if not attrs.get('monthly_interest_payment'):
                lender_amount = attrs['lender_amount']
                interest_rate = attrs['interest_payment_percentage']
                attrs['monthly_interest_payment'] = (lender_amount * interest_rate / 100) / 12
        return attrs


class BorrowingSummarySerializer(serializers.Serializer):
    total_borrowings = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_monthly_principal = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_monthly_interest = serializers.DecimalField(max_digits=18, decimal_places=2)
    average_interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    by_type = serializers.DictField()


class BorrowingTypeChoiceSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()


class RepaymentTermsChoiceSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()
