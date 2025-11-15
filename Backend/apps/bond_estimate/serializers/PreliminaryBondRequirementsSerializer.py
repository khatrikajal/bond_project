from rest_framework import serializers
from apps.bond_estimate.models.PreliminaryBondRequirementsModel import PreliminaryBondRequirements


class PreliminaryBondRequirementsSerializer(serializers.ModelSerializer):

    class Meta:
        model = PreliminaryBondRequirements
        fields = [
            "id",
            "company",
            "issue_amount",
            "security_type",
            "tenure",
            "coupon_rate",
            "preferred_roi",
            "preferred_investor_categories",
            "preferred_interest_payment_cycle",
            "del_flag",
            "created_at",
            "updated_at",
            "user_id_updated_by",
        ]
        read_only_fields = ["id", "del_flag", "created_at", "updated_at"]

    def validate(self, attrs):
        """
        POST / PUT → all required fields mandatory
        PATCH      → only validate fields provided
        """
        required_fields = [
            "company",
            "issue_amount",
            "security_type",
            "tenure",
            "coupon_rate",
            "preferred_roi",
            "preferred_investor_categories",
            "preferred_interest_payment_cycle",
        ]

        # ---------- PATCH MODE ----------
        if self.partial:
            return attrs   # do not validate missing required fields

        # ---------- POST / PUT MODE ----------
        errors = {}
        for field in required_fields:
            if not attrs.get(field):
                errors[field] = "This field is required."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs