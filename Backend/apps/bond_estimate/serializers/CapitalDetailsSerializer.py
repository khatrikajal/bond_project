
from rest_framework import serializers
from apps.bond_estimate.models.CapitalDetailsModel import CapitalDetails




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
