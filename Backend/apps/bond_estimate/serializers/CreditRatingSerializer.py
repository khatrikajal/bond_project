# from rest_framework import serializers
# from ..models.AgencyRatingChoice import RatingAgency, CreditRating
# from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
# from ..models.CreditRatingDetailsModel import CreditRatingDetails
# from datetime import datetime, timezone
# from django.core.files.base import ContentFile
# from django.conf import settings
# import os
# import re
# import uuid
# from ..services.bond_estimation_service import create_or_get_application, update_step


# class CreditRatingSerializer(serializers.Serializer):
#     credit_rating_id = serializers.IntegerField(read_only=True)

#     agency = serializers.ChoiceField(choices=RatingAgency.choices)
#     rating = serializers.ChoiceField(choices=CreditRating.choices)
#     valid_till = serializers.DateField()

#     additional_rating = serializers.CharField(max_length=255, required=False, allow_blank=True)
#     upload_letter = serializers.FileField(required=False, allow_null=True)

#     reting_status = serializers.BooleanField(default=False)

#     created_at = serializers.DateTimeField(read_only=True)
#     updated_at = serializers.DateTimeField(read_only=True)

#     # -------------------------------------------------------
#     # Helper: Build dynamic file path
#     # -------------------------------------------------------
#     def build_file_path(self, company_name, filename):
#         """
#         Returns dynamic file path:
#         <clean_company_name>/credit_rating_certificate/<filename>
#         """

#         clean_name = re.sub(r'[^A-Za-z0-9_-]+', '_', company_name)

#         base_path = os.path.join(
#             settings.MEDIA_ROOT,
#             clean_name,
#             "credit_rating_certificate"
#         )

#         os.makedirs(base_path, exist_ok=True)

#         return os.path.join(clean_name, "credit_rating_certificate", filename)

#     # -------------------------------------------------------
#     # VALIDATION
#     # -------------------------------------------------------
#     def validate(self, data):
#         company_id = self.context.get("company_id")
#         user = self.context["request"].user
#         instance = self.context.get("instance")

#         try:
#             company = CompanyInformation.objects.get(company_id=company_id, user=user)
#         except CompanyInformation.DoesNotExist:
#             raise serializers.ValidationError({"company_id": "Invalid company or not owned by user."})

#         # Duplicate check
#         query = CreditRatingDetails.objects.filter(
#             company=company,
#             agency=data["agency"],
#             rating=data["rating"],
#             is_del=0
#         )

#         if instance:
#             query = query.exclude(credit_rating_id=instance.credit_rating_id)

#         if query.exists():
#             raise serializers.ValidationError({
#                 "rating": f"A {data['rating']} rating from {data['agency']} already exists for this company."
#             })

#         # Valid till must be future date
#         if data["valid_till"] <= datetime.now(timezone.utc).date():
#             raise serializers.ValidationError({
#                 "valid_till": "Valid till date must be a future date."
#             })

#         return data

#     # -------------------------------------------------------
#     # CREATE
#     # -------------------------------------------------------
#     def create(self, validated_data):
#         user = self.context["request"].user
#         company_id = self.context["company_id"]

#         company = CompanyInformation.objects.get(company_id=company_id, user=user)

#         # File upload handler
#         upload_letter = validated_data.pop("upload_letter", None)
#         file_obj = None

#         if upload_letter:
#             filename = f"credit_rating_{uuid.uuid4().hex}.pdf"
#             dynamic_path = self.build_file_path(company.company_name, filename)

#             file_obj = ContentFile(upload_letter.read())
#             file_obj.name = dynamic_path

#         # Create record
#         rating_entry = CreditRatingDetails.objects.create(
#             company=company,
#             upload_letter=file_obj,
#             user_id_updated_by=user,
#             **validated_data,
#         )

#         # Link to app step
#         app = create_or_get_application(user=user, company=company)
#         update_step(
#             application=app,
#             step_id="1.2",
#             record_ids=[str(rating_entry.credit_rating_id)],
#             completed=True
#         )

#         return rating_entry

#     # -------------------------------------------------------
#     # UPDATE
#     # -------------------------------------------------------
#     def update(self, instance, validated_data):
#         user = self.context["request"].user

#         upload_letter = validated_data.pop("upload_letter", None)

#         if upload_letter:
#             filename = f"credit_rating_{uuid.uuid4().hex}.pdf"
#             dynamic_path = self.build_file_path(instance.company.company_name, filename)

#             file_obj = ContentFile(upload_letter.read())
#             file_obj.name = dynamic_path

#             instance.upload_letter = file_obj

#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)

#         instance.user_id_updated_by = user
#         instance.save()

#         return instance


# # ==================================================
# # LIST SERIALIZER
# # ==================================================
# class CreditRatingListSerializer(serializers.ModelSerializer):
#     agency_display = serializers.CharField(source='get_agency_display', read_only=True)
#     rating_display = serializers.CharField(source='get_rating_display', read_only=True)
#     upload_letter_url = serializers.SerializerMethodField()

#     class Meta:
#         model = CreditRatingDetails
#         fields = [
#             'credit_rating_id',
#             'agency', 'agency_display',
#             'rating', 'rating_display',
#             'valid_till',
#             'additional_rating',
#             'reting_status',
#             'upload_letter_url',
#             'created_at',
#             'updated_at',
#         ]

#     def get_upload_letter_url(self, obj):
#         if obj.upload_letter:
#             request = self.context.get('request')
#             if request:
#                 return request.build_absolute_uri(obj.upload_letter.url)
#         return None
from rest_framework import serializers
from ..models.AgencyRatingChoice import RatingAgency, CreditRating
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from ..models.CreditRatingDetailsModel import CreditRatingDetails
from datetime import date
from django.core.files.base import ContentFile
from django.conf import settings
import os, re, uuid
from ..services.bond_estimation_service import create_or_get_application, update_step


# -------------------------------------------------------
# Helper function for building dynamic file path
# -------------------------------------------------------
def build_file_path(company_name, filename):
    clean_name = re.sub(r'[^A-Za-z0-9_-]+', '_', company_name)
    return os.path.join(clean_name, "credit_rating_certificate", filename)


# -------------------------------------------------------
# POST + PATCH SERIALIZER
# -------------------------------------------------------
class CreditRatingSerializer(serializers.Serializer):
    credit_rating_id = serializers.IntegerField(read_only=True)

    agency = serializers.ChoiceField(choices=RatingAgency.choices, required=False)
    rating = serializers.ChoiceField(choices=CreditRating.choices, required=False)
    valid_till = serializers.DateField(required=False)

    additional_rating = serializers.CharField(max_length=255, required=False, allow_blank=True)
    upload_letter = serializers.FileField(required=False, allow_null=True)
    reting_status = serializers.BooleanField(default=False)

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    # -----------------------------
    # File path generator
    # -----------------------------
    def build_file_path(self, company_name, filename):
        clean_name = re.sub(r'[^A-Za-z0-9_-]+', '_', company_name)

        base_path = os.path.join(
            settings.MEDIA_ROOT,
            clean_name,
            "credit_rating_certificate"
        )
        os.makedirs(base_path, exist_ok=True)

        return os.path.join(clean_name, "credit_rating_certificate", filename)

    # -----------------------------
    # Validation (PATCH Compatible)
    # -----------------------------
    def validate(self, data):
        company_id = self.context.get("company_id")
        user = self.context["request"].user
        instance = self.context.get("instance")

        try:
            company = CompanyInformation.objects.get(company_id=company_id, user=user)
        except CompanyInformation.DoesNotExist:
            raise serializers.ValidationError({"company_id": "Invalid company or not owned by user."})

        # Extract values safely
        agency = data.get("agency", instance.agency if instance else None)
        rating = data.get("rating", instance.rating if instance else None)

        if agency and rating:
            query = CreditRatingDetails.objects.filter(
                company=company,
                agency=agency,
                rating=rating,
                is_del=0
            )

            if instance:
                query = query.exclude(credit_rating_id=instance.credit_rating_id)

            if query.exists():
                raise serializers.ValidationError({
                    "rating": f"A {rating} rating from {agency} already exists for this company."
                })

        valid_till = data.get("valid_till")
        if valid_till and valid_till <= date.today():
            raise serializers.ValidationError({"valid_till": "Valid till date must be a future date."})

        return data

    # -----------------------------
    # CREATE
    # -----------------------------
    def create(self, validated_data):
        user = self.context["request"].user
        company_id = self.context["company_id"]
        company = CompanyInformation.objects.get(company_id=company_id, user=user)

        upload_letter = validated_data.pop("upload_letter", None)
        file_obj = None

        if upload_letter:
            filename = f"credit_rating_{uuid.uuid4().hex}.pdf"
            path = self.build_file_path(company.company_name, filename)
            file_obj = ContentFile(upload_letter.read())
            file_obj.name = path

        rating_entry = CreditRatingDetails.objects.create(
            company=company,
            upload_letter=file_obj,
            user_id_updated_by=user,
            **validated_data
        )

        app = create_or_get_application(user=user, company=company)
        update_step(app, "1.2", [str(rating_entry.credit_rating_id)], True)

        return rating_entry

    # -----------------------------
    # UPDATE (PATCH uses this)
    # -----------------------------
    def update(self, instance, validated_data):
        user = self.context["request"].user
        upload_letter = validated_data.pop("upload_letter", None)

        if upload_letter:
            filename = f"credit_rating_{uuid.uuid4().hex}.pdf"
            path = self.build_file_path(instance.company.company_name, filename)
            file_obj = ContentFile(upload_letter.read())
            file_obj.name = path
            instance.upload_letter = file_obj

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.user_id_updated_by = user
        instance.save()
        return instance
# -------------------------------------------------------
# PUT SERIALIZER (Full update only)
# -------------------------------------------------------
class CreditRatingPutSerializer(serializers.Serializer):
    agency = serializers.ChoiceField(choices=RatingAgency.choices, required=True)
    rating = serializers.ChoiceField(choices=CreditRating.choices, required=True)
    valid_till = serializers.DateField(required=True)

    additional_rating = serializers.CharField(max_length=255, required=False, allow_blank=True)
    upload_letter = serializers.FileField(required=False, allow_null=True)
    reting_status = serializers.BooleanField(required=True)

    def validate(self, data):
        company_id = self.context.get("company_id")
        user = self.context["request"].user
        instance = self.context.get("instance")

        company = CompanyInformation.objects.get(company_id=company_id, user=user)

        agency = data["agency"]
        rating = data["rating"]

        # ---------------------------------------
        # FIXED: Do NOT treat same record as duplicate
        # ---------------------------------------
        exists = CreditRatingDetails.objects.filter(
            company=company,
            agency=agency,
            rating=rating,
            is_del=0
        ).exclude(credit_rating_id=instance.credit_rating_id).exists()

        if exists:
            raise serializers.ValidationError({
                "rating": f"{rating} from {agency} already exists"
            })

        # ---------------------------------------
        # DATE VALIDATION
        # ---------------------------------------
        if data["valid_till"] <= date.today():
            raise serializers.ValidationError({
                "valid_till": "Valid till date must be a future date"
            })

        return data

    def update(self, instance, validated_data):
        upload_letter = validated_data.pop("upload_letter", None)

        if upload_letter:
            filename = f"credit_rating_{uuid.uuid4().hex}.pdf"
            path = f"{instance.company.company_name}/credit_rating_certificate/{filename}"
            instance.upload_letter = ContentFile(upload_letter.read(), name=path)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.user_id_updated_by = self.context["request"].user
        instance.save()

        return instance


# -------------------------------------------------------
# LIST SERIALIZER WITH STATUS
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
