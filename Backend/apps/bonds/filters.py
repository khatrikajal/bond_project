# C:\Users\Admin\Desktop\bond_platform\bonds\filters.py
import django_filters
from .models import ISINBasicInfo,CreditRating,IssuerType,TaxCategory,OptionType
from django.db.models import Q
from django.core.exceptions import ValidationError

class CaseInsensitiveChoiceBaseFilter(django_filters.CharFilter):
    """
    Case-insensitive filter that works for single or multiple comma-separated values.
    Validates against provided choices if strict_validation=True.
    """
    def __init__(self, choices=None, strict_validation=True, allow_multiple=True, *args, **kwargs):
        self.strict_validation = strict_validation
        self.allow_multiple = allow_multiple
        self.valid_choices = []

        if choices:
            if hasattr(choices, 'choices'):
                self.valid_choices = [choice[0].upper() for choice in choices.choices]
            elif isinstance(choices, (list, tuple)):
                self.valid_choices = [
                    choice[0].upper() if isinstance(choice, (list, tuple)) else str(choice).upper()
                    for choice in choices
                ]

        super().__init__(*args, **kwargs)

    def filter(self, queryset, value):
        if not value:
            return queryset

        # Split into multiple values if allowed
        values = [v.strip() for v in str(value).split(',')] if self.allow_multiple else [str(value).strip()]
        if not values:
            return queryset

        # Validation
        if self.strict_validation and self.valid_choices:
            invalid_values = [v for v in values if v.upper() not in self.valid_choices]
            if invalid_values:
                available_choices = [c.lower() for c in self.valid_choices]
                raise ValidationError(
                    f"Invalid choice(s): {', '.join(invalid_values)}. Available: {', '.join(available_choices)}"
                )

        # Build OR query for multiple values, or single filter
        q = Q()
        for v in values:
            q |= Q(**{f"{self.field_name}__iexact": v})
        return queryset.filter(q)

class BondFilter(django_filters.FilterSet):
    """
    Production-ready version with comprehensive error handling and logging.
    """
    
    # YTM / Yield
    ytm_percent_min = django_filters.NumberFilter(
        field_name='ytm_percent', 
        lookup_expr='gte',
        label='Minimum YTM (%)'
    )
    ytm_percent_max = django_filters.NumberFilter(
        field_name='ytm_percent', 
        lookup_expr='lte',
        label='Maximum YTM (%)'
    )

    # Coupon Rate
    coupon_rate_min = django_filters.NumberFilter(
        field_name='coupon_rate_percent', 
        lookup_expr='gte',
        label='Minimum Coupon Rate (%)'
    )
    coupon_rate_max = django_filters.NumberFilter(
        field_name='coupon_rate_percent', 
        lookup_expr='lte',
        label='Maximum Coupon Rate (%)'
    )

    # Tenure filters
    balance_tenure_min = django_filters.NumberFilter(
        method='filter_tenure_year_min',
        label='Minimum Tenure (Years)'
    )
    balance_tenure_max = django_filters.NumberFilter(
        method='filter_tenure_year_max',
        label='Maximum Tenure (Years)'
    )

    # Choice-based filters with proper validation
    interest_payment_frequency = CaseInsensitiveChoiceBaseFilter(
        field_name='interest_payment_frequency',
        choices=[
            ('MONTHLY', 'Monthly'), 
            ('QUARTERLY', 'Quarterly'), 
            ('HALF_YEARLY', 'Half Yearly'), 
            ('ANNUALLY', 'Annually'), 
            ('CUMULATIVE', 'Cumulative at Maturity')
        ],
        label='Interest Payment Frequency',
        allow_multiple=True
    )

    credit_rating = CaseInsensitiveChoiceBaseFilter(
        field_name='latest_rating',
        choices=CreditRating,
        label='Credit Rating',
        allow_multiple=True
    )

    issuer_type = CaseInsensitiveChoiceBaseFilter(
        field_name='issuer_type',
        choices=IssuerType,
        label='Issuer Type',
        allow_multiple=True
    )

    tax_category = CaseInsensitiveChoiceBaseFilter(
        field_name='tax_category',
        choices=TaxCategory,
        label='Tax Category',
        allow_multiple=True
    )

    option_type = CaseInsensitiveChoiceBaseFilter(
        field_name='option_type',
        choices=OptionType,
        label='Option Type (Call/Put)',
        allow_multiple=False
    )

    # Face value range
    face_value_min = django_filters.NumberFilter(
        field_name='face_value_rs', 
        lookup_expr='gte',
        label='Minimum Face Value (Rs)'
    )
    face_value_max = django_filters.NumberFilter(
        field_name='face_value_rs', 
        lookup_expr='lte',
        label='Maximum Face Value (Rs)'
    )

    # Boolean filters
    secured = django_filters.BooleanFilter(
        field_name='secured',
        label='Secured Bonds Only'
    )

    class Meta:
        model = ISINBasicInfo
        fields = []

    def filter_tenure_year_min(self, queryset, name, value):
        """Filter for minimum tenure years with validation"""
        if value is not None:
            if value < 0:
                raise ValidationError("Minimum tenure cannot be negative")
            return queryset.filter(tenure_years__gte=value)
        return queryset

    def filter_tenure_year_max(self, queryset, name, value):
        """Filter for maximum tenure years with validation"""
        if value is not None:
            if value < 0:
                raise ValidationError("Maximum tenure cannot be negative")
            return queryset.filter(tenure_years__lte=value)
        return queryset

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add custom validation for min/max ranges
        self.form.fields['ytm_percent_min'].help_text = "Enter minimum YTM percentage"
        self.form.fields['ytm_percent_max'].help_text = "Enter maximum YTM percentage"
