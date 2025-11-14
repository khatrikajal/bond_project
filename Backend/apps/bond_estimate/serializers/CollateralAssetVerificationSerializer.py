from rest_framework import serializers
from apps.bond_estimate.models.CollateralAssetVerificationModel import CollateralAssetVerification


class CollateralAssetVerificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = CollateralAssetVerification
        fields = [
            "id",
            "collateral_type",
            "charge_type",
            "asset_description",
            "estimated_value",
            "valuation_date",
            "security_document_file",
            "security_document_ref",
            "trust_name",
            "ownership_type",
            "asset_cover_certificate",
            "valuation_report",
            "remarks",
        ]
        read_only_fields = ["id"]

    # ---------------------------------------------------
    # Inject company & user into create()
    # ---------------------------------------------------
    def create(self, validated_data):
        company = self.context.get("company")
        request = self.context.get("request")

        validated_data["company"] = company
        validated_data["user_id_updated_by"] = request.user

        return super().create(validated_data)

    # ---------------------------------------------------
    # Update instance safely
    # ---------------------------------------------------
    def update(self, instance, validated_data):
        request = self.context.get("request")

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.user_id_updated_by = request.user
        instance.save()
        return instance

    # ---------------------------------------------------
    # Validation (PATCH-safe)
    # ---------------------------------------------------
    def validate(self, attrs):
        """
        For POST → all required fields must exist.
        For PUT → all required fields must exist.
        For PATCH → validate only fields provided.
        """
        required = [
            "collateral_type",
            "charge_type",
            "asset_description",
            "estimated_value",
            "valuation_date",
            "trust_name",
            "ownership_type",
        ]

        # PATCH mode → only validate incoming fields
        if self.partial:
            return attrs

        # POST/PUT → validate all required fields
        errors = {}
        for field in required:
            if not attrs.get(field):
                errors[field] = "This field is required."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


# ---------------------------------------------------------------------------
# LIST + DETAIL Serializer (returns URLs instead of raw file paths)
# ---------------------------------------------------------------------------
class CollateralAssetVerificationDetailSerializer(serializers.ModelSerializer):

    security_document_file_url = serializers.SerializerMethodField()
    asset_cover_certificate_url = serializers.SerializerMethodField()
    valuation_report_url = serializers.SerializerMethodField()

    class Meta:
        model = CollateralAssetVerification
        fields = [
            "id",
            "collateral_type",
            "charge_type",
            "asset_description",
            "estimated_value",
            "valuation_date",
            "security_document_file_url",
            "security_document_ref",
            "trust_name",
            "ownership_type",
            "asset_cover_certificate_url",
            "valuation_report_url",
            "remarks",
            "created_at",
            "updated_at",
        ]

    def get_security_document_file_url(self, obj):
        request = self.context.get("request")
        if obj.security_document_file:
            return request.build_absolute_uri(obj.security_document_file.url)
        return None

    def get_asset_cover_certificate_url(self, obj):
        request = self.context.get("request")
        if obj.asset_cover_certificate:
            return request.build_absolute_uri(obj.asset_cover_certificate.url)
        return None

    def get_valuation_report_url(self, obj):
        request = self.context.get("request")
        if obj.valuation_report:
            return request.build_absolute_uri(obj.valuation_report.url)
        return None
