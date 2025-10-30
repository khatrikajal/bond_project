# Backend/apps/authentication/serializers.py
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from phonenumber_field.phonenumber import PhoneNumber
from .models import OTPRequest
import re


class SendOTPSerializer(serializers.Serializer):
    """Serializer for sending OTP"""
    
    phone_number = PhoneNumberField(
        help_text="Phone number with country code (e.g., +1234567890)"
    )
    purpose = serializers.ChoiceField(
        choices=OTPRequest.PurposeChoices.choices,
        default=OTPRequest.PurposeChoices.REGISTRATION,
        help_text="Purpose of OTP request"
    )
    
    def validate_phone_number(self, value):
        """Validate phone number format and check if it's valid"""
        if not value.is_valid():
            raise serializers.ValidationError(
                "Invalid phone number format. Please include country code."
            )
        return value
    
    def validate(self, attrs):
        """Additional validation"""
        phone_number = attrs.get('phone_number')
        purpose = attrs.get('purpose')
        
        # Additional business logic validation can be added here
        # For example, checking if phone number is already registered
        
        return attrs


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP"""
    
    phone_number = PhoneNumberField(
        help_text="Phone number with country code"
    )
    otp_code = serializers.CharField(
        max_length=10,
        min_length=4,
        help_text="OTP code received via SMS"
    )
    purpose = serializers.ChoiceField(
        choices=OTPRequest.PurposeChoices.choices,
        default=OTPRequest.PurposeChoices.REGISTRATION,
        help_text="Purpose of OTP verification"
    )
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        if not value.is_valid():
            raise serializers.ValidationError(
                "Invalid phone number format. Please include country code."
            )
        return value
    
    def validate_otp_code(self, value):
        """Validate OTP code format"""
        # Remove any spaces or special characters
        cleaned_otp = re.sub(r'[^0-9]', '', value)
        
        if not cleaned_otp:
            raise serializers.ValidationError("OTP code must contain only numbers")
        
        if len(cleaned_otp) < 4 or len(cleaned_otp) > 10:
            raise serializers.ValidationError("OTP code must be between 4-10 digits")
        
        return cleaned_otp


class ResendOTPSerializer(serializers.Serializer):
    """Serializer for resending OTP"""
    
    phone_number = PhoneNumberField(
        help_text="Phone number with country code"
    )
    purpose = serializers.ChoiceField(
        choices=OTPRequest.PurposeChoices.choices,
        default=OTPRequest.PurposeChoices.REGISTRATION,
        help_text="Purpose of OTP request"
    )
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        if not value.is_valid():
            raise serializers.ValidationError(
                "Invalid phone number format. Please include country code."
            )
        return value


class OTPRequestSerializer(serializers.ModelSerializer):
    """Serializer for OTP request model (for admin/debugging purposes)"""
    
    phone_number = serializers.CharField(read_only=True)
    attempts_count = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = OTPRequest
        fields = [
            'id', 'phone_number', 'purpose', 'status',
            'created_at', 'verified_at', 'expires_at',
            'attempt_count', 'attempts_count', 'is_expired', 'time_remaining',
            'external_reference'
        ]
        read_only_fields = fields
    
    def get_attempts_count(self, obj):
        """Get total attempts count including related attempts"""
        return obj.attempts.count()
    
    def get_is_expired(self, obj):
        """Check if OTP request is expired"""
        return obj.is_expired()
    
    def get_time_remaining(self, obj):
        """Get remaining time in seconds"""
        from django.utils import timezone
        
        if obj.is_expired():
            return 0
        
        remaining = (obj.expires_at - timezone.now()).total_seconds()
        return max(0, int(remaining))