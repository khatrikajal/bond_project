# from rest_framework import serializers
# from ..models.AgencyRatingChoice import RatingAgency,CreditRating
# from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
# from ..models.CreditRatingDetailsModel import CreditRatingDetails
# from datetime import datetime,timezone
# from django.core.files.base import ContentFile
# import uuid
# from ..services.bond_estimation_service import create_or_get_application,update_step



# class CreditRatingSerializer(serializers.Serializer):
#     agency = serializers.ChoiceField(choices=RatingAgency.choices)
#     rating = serializers.ChoiceField(choices=CreditRating.choices)
#     valid_till = serializers.DateField()
#     additional_rating = serializers.CharField(max_length=255, required=False, allow_blank=True)
#     upload_letter = serializers.FileField(required=False, allow_null=True)
#     reting_status = serializers.BooleanField(default=False)

#     def validate(self, data):
#         """
#         Validate for duplicates and logical consistency.
#         """
#         company_id = self.context.get("company_id")
#         user = self.context["request"].user

#         try:
#             company = CompanyInformation.objects.get(company_id=company_id, user=user)
#         except CompanyInformation.DoesNotExist:
#             raise serializers.ValidationError({"company_id": "Invalid company or not owned by user."})

      
#         if CreditRatingDetails.objects.filter(
#             company=company, agency=data["agency"], rating=data["rating"], is_del=0
#         ).exists():
#             raise serializers.ValidationError({
#                 "rating": f"A {data['rating']} rating from {data['agency']} already exists for this company."
#             })

     
#         if data["valid_till"] <= timezone.now().date():
#             raise serializers.ValidationError({
#                 "valid_till": "Valid till date must be a future date."
#             })

#         return data

#     def create(self, validated_data):
#         """
#         Create a Credit Rating record and link it to the BondEstimationApplication.
#         """
#         user = self.context["request"].user
#         company_id = self.context["company_id"]

    
#         try:
#             company = CompanyInformation.objects.get(company_id=company_id, user=user)
#         except CompanyInformation.DoesNotExist:
#             raise serializers.ValidationError({"company_id": "Invalid company or not owned by user."})

        
#         upload_letter = validated_data.pop("upload_letter", None)
#         file_obj = None
#         if upload_letter:
#             filename = f"credit_rating_{uuid.uuid4().hex}.pdf"
#             file_obj = ContentFile(upload_letter.read(), name=filename)

      
#         rating_entry = CreditRatingDetails.objects.create(
#             company=company,
#             upload_letter=file_obj,
#             user_id_updated_by=user,
#             **validated_data,
#         )

        
#         app = create_or_get_application(user=user, company=company)

#         # Mark step "1.2" as complete in Bond Estimation
#         update_step(
#             application=app,
#             step_id="1.2",
#             record_id=str(rating_entry.credit_rating_id),
#             completed=True
#         )


#         return {
#             "credit_rating_id": rating_entry.credit_rating_id,
#             "company_id": str(company.company_id),
#             "agency": rating_entry.agency,
#             "rating": rating_entry.rating,
#             "valid_till": rating_entry.valid_till,
#             "additional_rating": rating_entry.additional_rating,
#             "reting_status": rating_entry.reting_status,
#             "message": "Credit rating details saved successfully.",
#             "application_id": str(app.application_id),
#             "step_id": "1.2",
#             "step_status": "completed",
#         }


# ============================================
# serializers/CreditRatingSerializer.py
# ============================================

from rest_framework import serializers
from ..models.AgencyRatingChoice import RatingAgency, CreditRating
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from ..models.CreditRatingDetailsModel import CreditRatingDetails
from datetime import datetime, timezone
from django.core.files.base import ContentFile
import uuid
from ..services.bond_estimation_service import create_or_get_application, update_step


class CreditRatingSerializer(serializers.Serializer):
    credit_rating_id = serializers.IntegerField(read_only=True)
    agency = serializers.ChoiceField(choices=RatingAgency.choices)
    rating = serializers.ChoiceField(choices=CreditRating.choices)
    valid_till = serializers.DateField()
    additional_rating = serializers.CharField(max_length=255, required=False, allow_blank=True)
    upload_letter = serializers.FileField(required=False, allow_null=True)
    reting_status = serializers.BooleanField(default=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def validate(self, data):
        """
        Validate for duplicates and logical consistency.
        """
        company_id = self.context.get("company_id")
        user = self.context["request"].user
        instance = self.context.get("instance")  # For update operations

        try:
            company = CompanyInformation.objects.get(company_id=company_id, user=user)
        except CompanyInformation.DoesNotExist:
            raise serializers.ValidationError({"company_id": "Invalid company or not owned by user."})

        # Check for duplicates (exclude current instance on update)
        query = CreditRatingDetails.objects.filter(
            company=company, 
            agency=data["agency"], 
            rating=data["rating"], 
            is_del=0
        )
        
        if instance:
            query = query.exclude(credit_rating_id=instance.credit_rating_id)
        
        if query.exists():
            raise serializers.ValidationError({
                "rating": f"A {data['rating']} rating from {data['agency']} already exists for this company."
            })

        # Validate future date
        if data["valid_till"] <= datetime.now(timezone.utc).date():
            raise serializers.ValidationError({
                "valid_till": "Valid till date must be a future date."
            })

        return data

    def create(self, validated_data):
        """
        Create a Credit Rating record and link it to the BondEstimationApplication.
        """
        user = self.context["request"].user
        company_id = self.context["company_id"]

        try:
            company = CompanyInformation.objects.get(company_id=company_id, user=user)
        except CompanyInformation.DoesNotExist:
            raise serializers.ValidationError({"company_id": "Invalid company or not owned by user."})

        # Handle file upload
        upload_letter = validated_data.pop("upload_letter", None)
        file_obj = None
        if upload_letter:
            filename = f"credit_rating_{uuid.uuid4().hex}.pdf"
            file_obj = ContentFile(upload_letter.read(), name=filename)

        # Create rating entry
        rating_entry = CreditRatingDetails.objects.create(
            company=company,
            upload_letter=file_obj,
            user_id_updated_by=user,
            **validated_data,
        )

        # Get or create bond estimation application
        app = create_or_get_application(user=user, company=company)

        # Mark step "1.2" as complete
        update_step(
            application=app,
            step_id="1.2",
            record_ids=[str(rating_entry.credit_rating_id)],
            completed=True
        )

        return rating_entry

    def update(self, instance, validated_data):
        """
        Update existing credit rating record.
        """
        user = self.context["request"].user
        
        # Handle file upload
        upload_letter = validated_data.pop("upload_letter", None)
        if upload_letter:
            filename = f"credit_rating_{uuid.uuid4().hex}.pdf"
            instance.upload_letter = ContentFile(upload_letter.read(), name=filename)

        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.user_id_updated_by = user
        instance.save()

        return instance


class CreditRatingListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing credit ratings"""
    agency_display = serializers.CharField(source='get_agency_display', read_only=True)
    rating_display = serializers.CharField(source='get_rating_display', read_only=True)
    upload_letter_url = serializers.SerializerMethodField()

    class Meta:
        model = CreditRatingDetails
        fields = [
            'credit_rating_id', 'agency', 'agency_display', 'rating', 
            'rating_display', 'valid_till', 'additional_rating', 
            'reting_status', 'upload_letter_url', 'created_at', 'updated_at'
        ]

    def get_upload_letter_url(self, obj):
        if obj.upload_letter:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.upload_letter.url)
        return None

