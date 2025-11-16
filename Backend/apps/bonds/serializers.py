from rest_framework import serializers
from .models import ISINBasicInfo,KeyFactor,RatioAnalysis,FinancialMetric,CompanyInfo,ISINCompanyMap,RTAInfo,ISINRTAMap,ContactMessage
from dateutil.relativedelta import relativedelta
from datetime import date
from decimal import Decimal, InvalidOperation
from django.db import models

# class SafeDecimalField(serializers.DecimalField):
#     def to_representation(self, value):
#         if value in ["", " ", None, "NA", "-", "NaN", "nan", "Infinity"]:
#             print(f"SafeDecimalField: Invalid value encountered: {value}")
#             return None
#         try:
#             return str(Decimal(str(value)))
#         except InvalidOperation:
#             return None


# class ISINBasicInfoSerializer(serializers.ModelSerializer):
#     price = SafeDecimalField(
#         source="face_value_rs", max_digits=18, decimal_places=2,
#         allow_null=True, required=False, read_only=True
#     )
#     tenure = serializers.SerializerMethodField()
#     ratings = serializers.SerializerMethodField()
#     coupon_type = serializers.SerializerMethodField()
  
    

#     class Meta:
#         model = ISINBasicInfo
#         exclude = [
#             "former_name",
#             "interest_payment_frequency_raw",
#             "percentage_sold",
#             "data_hash",
#             "record_created_date",
#             "last_updated",
#         ]

#     def get_tenure(self, obj):
#         # tenure_days is None if maturity_date is null
    
#         if obj.maturity_date is None:
#             return {"years": 0, "months": 0, "days": 0}

#         today = date.today()
#         rd = relativedelta(obj.maturity_date, today)

#         return {"years": rd.years, "months": rd.months, "days": rd.days}


#     def get_ratings(self, obj):
#         """
#         Returns ratings in the format [{"agency": <>, "rating": <>}].
#         Supports both:
#         1. Annotated latest_rating/latest_agency (single latest rating)
#         2. Prefetched full ratings (latest_ratings attribute)
#         """
#         # 1 Use annotated latest rating if available
#         if getattr(obj, "latest_rating", None) and getattr(obj, "latest_agency", None):
#             return [{"agency": obj.latest_agency, "rating": obj.latest_rating}]
        
#         # 2 Use prefetched ratings if available
#         latest_ratings = getattr(obj, "latest_ratings", None)
#         if latest_ratings:
#             return [
#                 {"agency": r.rating_agency, "rating": r.credit_rating, "rating_date": r.rating_date}
#                 for r in latest_ratings
#             ]

#         # 3 Fallback: empty list
#         return []
    
#     def get_coupon_type(self, obj):
#         detail = getattr(obj, "detailed_info", None)
#         return detail.coupon_type if detail else None



from datetime import date
from dateutil.relativedelta import relativedelta



class SafeDecimalField(serializers.DecimalField):
    """
    Enhanced DecimalField that handles all edge cases.
    Automatically respects each field's decimal_places setting.
    """
    
    def to_representation(self, value):
        # Handle None, empty strings, and special string values
        if value in [None, "", " ", "NA", "-"]:
            return None
        
        try:
            # Convert to Decimal
            decimal_value = Decimal(str(value))
            
            # Check for infinity and NaN
            if decimal_value.is_infinite() or decimal_value.is_nan():
                return None
            
            # ✅ KEY FIX: Use the field's own decimal_places setting
            # Build the quantize pattern dynamically based on decimal_places
            if self.decimal_places is not None:
                # Create pattern: 2 decimals → '0.01', 4 decimals → '0.0001'
                quantize_pattern = Decimal('0.1') ** self.decimal_places
            else:
                # Fallback if decimal_places not set (shouldn't happen)
                quantize_pattern = Decimal('0.01')
            
            # Quantize using the correct precision
            quantized = decimal_value.quantize(
                quantize_pattern,
                rounding=self.rounding
            )
            
            # Return as string
            return str(quantized)
            
        except (InvalidOperation, ValueError, TypeError) as e:
            # Log the error for debugging
            print(f"SafeDecimalField: Invalid value encountered: {value} (type: {type(value)}), Error: {e}")
            return None


class ISINBasicInfoSerializer(serializers.ModelSerializer):
    serializer_field_mapping = {
        **serializers.ModelSerializer.serializer_field_mapping,
        models.DecimalField: SafeDecimalField,  # Override default
    }
    tenure = serializers.SerializerMethodField()
    ratings = serializers.SerializerMethodField()
    coupon_type = serializers.SerializerMethodField()

    class Meta:
        model = ISINBasicInfo
        exclude = [
            "former_name",
            "interest_payment_frequency_raw",
            "percentage_sold",
            "data_hash",
            "record_created_date",
            "last_updated",
        ]

    def get_tenure(self, obj):
        """Calculate tenure with proper error handling"""
        if obj.maturity_date is None:
            return {"years": 0, "months": 0, "days": 0}
        
        try:
            today = date.today()
            rd = relativedelta(obj.maturity_date, today)
            return {"years": rd.years, "months": rd.months, "days": rd.days}
        except (ValueError, OverflowError):
            return {"years": 0, "months": 0, "days": 0}

    def get_ratings(self, obj):
        """Returns ratings with proper fallback"""
        # Use annotated latest rating if available
        if getattr(obj, "latest_rating", None) and getattr(obj, "latest_agency", None):
            return [{"agency": obj.latest_agency, "rating": obj.latest_rating}]
        
        # Use prefetched ratings if available
        latest_ratings = getattr(obj, "latest_ratings", None)
        if latest_ratings:
            return [
                {
                    "agency": r.rating_agency, 
                    "rating": r.credit_rating, 
                    "rating_date": r.rating_date
                }
                for r in latest_ratings
            ]

        return []
    
    def get_coupon_type(self, obj):
        """Get coupon type from detailed info"""
        detail = getattr(obj, "detailed_info", None)
        return detail.coupon_type if detail else None

    




class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyInfo
        fields = [
            "company_id", "issuer_name", "issuer_logo", "issuer_address",
            "issuer_type", "issuer_state", "issuer_website","issuer_description","sector"
        ]

class ISINCompanyMapSerializer(serializers.ModelSerializer):
    company = CompanySerializer()  # nested company serializer

    class Meta:
        model = ISINCompanyMap
        fields = ["company"]


class RtaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RTAInfo
        fields = ["rta_id", "rta_name", "rta_email", "rta_phone"]    

class ISINRTAMapSerializer(serializers.ModelSerializer):
    rta = RtaSerializer()  

    class Meta:
        model = ISINRTAMap
        fields = ["rta"]



class FinancialMetricSerializer(serializers.ModelSerializer):
    charts = serializers.SerializerMethodField()

    class Meta:
        model = FinancialMetric
        fields = ['name', 'charts']

    def get_charts(self, obj):
        limit = 3
        data_qs = obj.values.order_by("-year")[:limit] 
        return {str(d.year): d.value if d.value is not None else "" for d in data_qs}




class RatioAnalysisSerializer(serializers.ModelSerializer):
    charts = serializers.SerializerMethodField()  

    class Meta:
        model = RatioAnalysis
        fields = ['title', 'benchmark', 'assessment', 'description', 'charts']

    def get_charts(self, obj):
        limit = 3
        data_qs = obj.values.order_by("-year")[:limit]  
        return {str(d.year): d.value if d.value is not None else "" for d in data_qs}




class KeyFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyFactor
        fields = ['company', 'key_factors', 'strengths', 'weaknesses']



class SnapshotItemSerializer(serializers.Serializer):
    metric = serializers.CharField()
    value = serializers.CharField()



# class ContactMessageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ContactMessage
#         fields = ['id', 'name', 'email', 'phone_number', 'message', 'created_at']
#         read_only_fields = ['id', 'created_at']

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone_number', 'message']
        
    def validate_phone_number(self, value):
        """Optional: Add phone validation if needed"""
        if value and len(value) > 20:
            raise serializers.ValidationError("Phone number too long")
        return value   
        