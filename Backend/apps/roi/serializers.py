from rest_framework import serializers
from .models import FundPosition, CreditRating, BorrowingDetail, CapitalDetail, ProfitabilityRatio
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from apps.authentication.issureauth.models import User


class CompanyMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyInformation
        fields = ["company_id", "company_name"]


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["user_id", "email"]


class FundPositionSerializer(serializers.ModelSerializer):
    company = CompanyMiniSerializer(read_only=True)
    user_id_updated_by = UserMiniSerializer(read_only=True)

    company_id = serializers.PrimaryKeyRelatedField(
        queryset=CompanyInformation.objects.all(), source="company", write_only=True
    )
    user_id_updated_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user_id_updated_by", write_only=True, required=False
    )

    class Meta:
        model = FundPosition
        fields = "__all__"


class CreditRatingSerializer(serializers.ModelSerializer):
    company = CompanyMiniSerializer(read_only=True)
    user_id_updated_by = UserMiniSerializer(read_only=True)

    company_id = serializers.PrimaryKeyRelatedField(
        queryset=CompanyInformation.objects.all(), source="company", write_only=True
    )
    user_id_updated_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user_id_updated_by", write_only=True, required=False
    )

    class Meta:
        model = CreditRating
        fields = "__all__"


class BorrowingDetailSerializer(serializers.ModelSerializer):
    company = CompanyMiniSerializer(read_only=True)
    user_id_updated_by = UserMiniSerializer(read_only=True)

    company_id = serializers.PrimaryKeyRelatedField(
        queryset=CompanyInformation.objects.all(), source="company", write_only=True
    )
    user_id_updated_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user_id_updated_by", write_only=True, required=False
    )

    class Meta:
        model = BorrowingDetail
        fields = "__all__"


class CapitalDetailSerializer(serializers.ModelSerializer):
    company = CompanyMiniSerializer(read_only=True)
    user_id_updated_by = UserMiniSerializer(read_only=True)

    company_id = serializers.PrimaryKeyRelatedField(
        queryset=CompanyInformation.objects.all(), source="company", write_only=True
    )
    user_id_updated_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user_id_updated_by", write_only=True, required=False
    )

    class Meta:
        model = CapitalDetail
        fields = "__all__"


class ProfitabilityRatioSerializer(serializers.ModelSerializer):
    company = CompanyMiniSerializer(read_only=True)
    user_id_updated_by = UserMiniSerializer(read_only=True)

    company_id = serializers.PrimaryKeyRelatedField(
        queryset=CompanyInformation.objects.all(), source="company", write_only=True
    )
    user_id_updated_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user_id_updated_by", write_only=True, required=False
    )

    class Meta:
        model = ProfitabilityRatio
        fields = "__all__"
