# C:\Users\Admin\Desktop\bond_platform\bonds\filters.py
import django_filters
from .models import ISINBasicInfo,CreditRating,IssuerType,TaxCategory,OptionType
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.db.models import Case, When, IntegerField
from django.core.cache import cache
from typing import Dict
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



# ============================================
# RATING HIERARCHY - Synced with CreditRating Model
# ============================================
RATING_ORDER: Dict[str, int] = {
    "AAA": 1,
    "AA+": 2,
    "AA": 3,
    "AA-": 4,
    "A+": 5,
    "A": 6,
    "A-": 7,
    "BBB+": 8,
    "BBB": 9,
    "BBB-": 10,   # Investment grade cutoff
    "BB+": 11,
    "BB": 12,
    "BB-": 13,
    "B+": 14,
    "B": 15,
    "B-": 16,
    "C": 17,
    "D": 18,
    "UNRATED": 999,  # Lowest priority
}

# Investment grade threshold
INVESTMENT_GRADE_THRESHOLD = 10  # BBB- and above


def get_rating_annotation():
    """
    Returns Case/When annotation for rating rank.
    Cached to avoid recreating on every request.
    """
    cache_key = 'rating_case_annotation_v1'
    annotation = cache.get(cache_key)
    
    if annotation is None:
        annotation = Case(
            *[When(latest_rating__iexact=rating, then=rank) 
              for rating, rank in RATING_ORDER.items()],
            default=999,  # Fallback for any edge cases
            output_field=IntegerField()
        )
        cache.set(cache_key, annotation, timeout=3600)
    
    return annotation


def validate_rating(value: str) -> str:
    """Validate and normalize rating value"""
    value_upper = value.upper().strip()
    
    if value_upper not in RATING_ORDER:
        valid_ratings = ", ".join(RATING_ORDER.keys())
        raise ValidationError(
            f"Invalid rating '{value}'. Valid options: {valid_ratings}"
        )
    
    return value_upper




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
        
        # ✅ NEW: Handle UNRATED specially
        has_unrated = any(v.upper() == 'UNRATED' for v in values)

        # Build OR query for multiple values, or single filter
        q = Q()
        for v in values:
            q |= Q(**{f"{self.field_name}__iexact": v})
        
        # ✅ Add UNRATED filter (NULL or empty or 'UNRATED')
        if has_unrated:
            q |= Q(**{f"{self.field_name}__isnull": True}) | Q(**{f"{self.field_name}__iexact": ''}) | Q(**{f"{self.field_name}__iexact": 'UNRATED'})
            
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

    
    # ===== NEW: RATING HIERARCHY FILTERS =====
    
    rating_min = django_filters.CharFilter(
        method='filter_rating_min',
        label='Minimum Rating Quality (e.g., BBB+ and better)',
        help_text='Returns bonds with this rating or HIGHER quality. Example: BBB+ returns AAA to BBB+'
    )
    
    rating_max = django_filters.CharFilter(
        method='filter_rating_max',
        label='Maximum Rating Quality (e.g., BBB+ and lower)',
        help_text='Returns bonds with this rating or LOWER quality. Example: BBB+ returns BBB+ to UNRATED'
    )
    
    investment_grade_only = django_filters.BooleanFilter(
        method='filter_investment_grade',
        label='Investment Grade Only',
        help_text='Returns only BBB- rated bonds and above'
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
    

    # ===== RATING FILTER IMPLEMENTATIONS =====
    def filter_rating_min(self, queryset, name, value):
        """
        Filter for MINIMUM rating quality (X and BETTER).
        
        Example: rating_min=BBB+ returns all bonds from AAA down to BBB+
        Works with UNRATED too: rating_min=UNRATED returns only UNRATED bonds
        
        URL: ?rating_min=BBB+
        """
        try:
            validated_rating = validate_rating(value)
            threshold = RATING_ORDER[validated_rating]
            
            # Annotate if not already done
            if 'rating_rank' not in queryset.query.annotations:
                queryset = queryset.annotate(rating_rank=get_rating_annotation())
            
            # Lower rank number = better quality
            return queryset.filter(rating_rank__lte=threshold)
            
        except ValidationError as e:
            logger.warning(f"Invalid rating_min value: {value}")
            raise
    
    def filter_rating_max(self, queryset, name, value):
        """
        Filter for MAXIMUM rating quality (X and WORSE).
        
        Example: rating_max=BBB+ returns bonds from BBB+ down to UNRATED
        
        URL: ?rating_max=BBB+
        """
        try:
            validated_rating = validate_rating(value)
            threshold = RATING_ORDER[validated_rating]
            
            # Annotate if not already done
            if 'rating_rank' not in queryset.query.annotations:
                queryset = queryset.annotate(rating_rank=get_rating_annotation())
            
            # Higher rank number = worse quality
            return queryset.filter(rating_rank__gte=threshold)
            
        except ValidationError as e:
            logger.warning(f"Invalid rating_max value: {value}")
            raise
    
    def filter_investment_grade(self, queryset, name, value):
        """
        Filter for investment grade bonds only (BBB- and above).
        Excludes speculative grade (BB+ and below) and UNRATED.
        
        URL: ?investment_grade_only=true
        """
        if not value:
            return queryset
        
        # Annotate if not already done
        if 'rating_rank' not in queryset.query.annotations:
            queryset = queryset.annotate(rating_rank=get_rating_annotation())
        
        return queryset.filter(rating_rank__lte=INVESTMENT_GRADE_THRESHOLD)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add custom validation for min/max ranges
        self.form.fields['ytm_percent_min'].help_text = "Enter minimum YTM percentage"
        self.form.fields['ytm_percent_max'].help_text = "Enter maximum YTM percentage"
