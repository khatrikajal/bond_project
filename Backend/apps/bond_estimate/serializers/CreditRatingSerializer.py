from rest_framework import serializers
from ..models.AgencyRatingChoice import RatingAgency, CreditRating
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from ..models.CreditRatingDetailsModel import CreditRatingDetails
from datetime import date
from django.core.files.base import ContentFile
import os, re, uuid


# -------------------------------------------------------
# Helper: Dynamic file path
# -------------------------------------------------------
def build_file_path(company_name, filename):
    clean_name = re.sub(r"[^A-Za-z0-9_-]+", "_", company_name)
    return os.path.join(clean_name, "credit_rating_certificate", filename)


# -------------------------------------------------------
# CREATE + PATCH SERIALIZER
# -------------------------------------------------------
class CreditRatingSerializer(serializers.Serializer):
    credit_rating_id = serializers.IntegerField(read_only=True)

    agency = serializers.ChoiceField(choices=RatingAgency.choices, required=False)
    rating = serializers.ChoiceField(choices=CreditRating.choices, required=False)
    valid_till = serializers.DateField(required=False)

    additional_rating = serializers.CharField(max_length=255, required=False, allow_blank=True)
    upload_letter = serializers.FileField(required=False, allow_null=True)
    reting_status = serializers.BooleanField(default=False, read_only=True)

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    # -------------------------------------------------------
    # VALIDATION
    # -------------------------------------------------------
    def validate(self, data):
        company_id = self.context.get("company_id")
        user = self.context["request"].user
        instance = self.context.get("instance")

        try:
            company = CompanyInformation.objects.get(company_id=company_id, user=user)
        except CompanyInformation.DoesNotExist:
            raise serializers.ValidationError({"company_id": "Invalid company or not owned by user"})

        agency = data.get("agency", instance.agency if instance else None)
        rating = data.get("rating", instance.rating if instance else None)

        # Skip duplicate check if rating & agency unchanged (PATCH request)
        if instance and agency == instance.agency and rating == instance.rating:
            pass
        else:
            if agency and rating:
                qs = CreditRatingDetails.objects.filter(
                    company=company, agency=agency, rating=rating, is_del=0
                )
                if instance:
                    qs = qs.exclude(credit_rating_id=instance.credit_rating_id)
                if qs.exists():
                    raise serializers.ValidationError({
                        "rating": f"{rating} from {agency} already exists for this company."
                    })

        valid_till = data.get("valid_till")
        if valid_till and valid_till <= date.today():
            raise serializers.ValidationError({"valid_till": "Valid till date must be a future date"})

        return data

    # -------------------------------------------------------
    # CREATE
    # -------------------------------------------------------
    def create(self, validated_data):
        user = self.context["request"].user
        company_id = self.context["company_id"]
        company = CompanyInformation.objects.get(company_id=company_id, user=user)

        upload_letter = validated_data.pop("upload_letter", None)
        file_obj = None

        if upload_letter:
            filename = f"credit_rating_{uuid.uuid4().hex}.pdf"
            file_path = build_file_path(company.company_name, filename)
            file_obj = ContentFile(upload_letter.read())
            file_obj.name = file_path

        rating_entry = CreditRatingDetails.objects.create(
            company=company,
            upload_letter=file_obj,
            **validated_data,
            user_id_updated_by=user,
            reting_status=validated_data.get("valid_till", date.today()) > date.today(),
        )

        return rating_entry

    # -------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------
    def update(self, instance, validated_data):
        user = self.context["request"].user
        upload_letter = validated_data.pop("upload_letter", None)

        if upload_letter:
            filename = f"credit_rating_{uuid.uuid4().hex}.pdf"
            file_path = build_file_path(instance.company.company_name, filename)
            file_obj = ContentFile(upload_letter.read())
            file_obj.name = file_path
            instance.upload_letter = file_obj

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.reting_status = instance.valid_till > date.today()
        instance.user_id_updated_by = user
        instance.save()

        return instance


# -------------------------------------------------------
# LIST SERIALIZER
# -------------------------------------------------------
class CreditRatingListSerializer(serializers.ModelSerializer):
    agency_display = serializers.CharField(source="get_agency_display", read_only=True)
    rating_display = serializers.CharField(source="get_rating_display", read_only=True)
    upload_letter_url = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = CreditRatingDetails
        fields = [
            "credit_rating_id",
            "agency", "agency_display",
            "rating", "rating_display",
            "valid_till",
            "additional_rating",
            "reting_status",
            "upload_letter_url",
            "status",
            "created_at",
            "updated_at",
        ]

    def get_upload_letter_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.upload_letter.url) if obj.upload_letter and request else None

    def get_status(self, obj):
        return "valid" if obj.valid_till >= date.today() else "expired"
