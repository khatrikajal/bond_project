from rest_framework import serializers
from apps.kyc.issuer_kyc.models.CompanyAdressModel import CompanyAddress

class CompanyAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyAddress
        fields = [
            'address_id',
            'company',
            'registered_office_address',
            'city',
            'state_ut',
            'pin_code',
            'country',
            'company_contact_email',
            'company_contact_phone',
            'address_type',
            'created_at'
        ]
        read_only_fields = ['address_id', 'created_at']