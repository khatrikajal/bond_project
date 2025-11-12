#

from rest_framework import serializers
from apps.bond_estimate.model.CapitalDetailsModel import CapitalDetails
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation


class CapitalDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = CapitalDetails
        fields = [
            "capital_detail_id",
            "share_capital",
            "reserves_surplus",
            "net_worth",
            "created_at",
            "updated_at",
            
        ]
        read_only_fields = ["net_worth","capital_detail_id", "created_at", "updated_at"]

    def validate_company(self, value):
        if not CompanyInformation.objects.filter(pk=value.company_id, del_flag=0).exists():
            raise serializers.ValidationError("Invalid company ID.")
        return value
