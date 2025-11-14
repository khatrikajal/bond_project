from rest_framework import serializers
from apps.bond_estimate.models.ProfitabilityRatiosModel  import ProfitabilityRatios
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation


class ProfitabilityRatiosSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProfitabilityRatios
        fields = [
            "ratio_id",
            "net_profit",
            "net_worth",
            "ebitda",
            "debt_equity_ratio",
            "current_ratio",
            "quick_ratio",
            "return_on_equity",
            "return_on_assets",
            "dscr",
            "del_flag",
            "user_id_updated_by",
         
        ]
        read_only_fields = ["ratio_id", "created_at", "updated_at"]

    # ---- BIND COMPANY FROM URL ----
    def create(self, validated_data):
        company_id = self.context["view"].kwargs.get("company_id")

        company = CompanyInformation.objects.filter(company_id=company_id).first()
        if not company:
            raise serializers.ValidationError("Invalid company_id passed in URL.")

        # ---- ENFORCE ONE-TO-ONE ----
        existing = ProfitabilityRatios.objects.filter(company=company).first()
        if existing:
            raise serializers.ValidationError(
                "Profitability ratios already exist for this company."
            )

        validated_data["company"] = company
        return super().create(validated_data)

    # ---- PARTIAL UPDATE HANDLED BY DRF ----
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
