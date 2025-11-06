from ..models.DemateAccountDetailsModel import DematAccount
from rest_framework import serializers
from ..models.CompanyInformationModel import CompanyInformation,CompanyOnboardingApplication

from ..services.onboarding_service import update_step_4_status

class DemateAccountSerializer(serializers.Serializer):
    dp_name = serializers.CharField(max_length=50)
    depository_participant = serializers.ChoiceField(choices=[("NSDL", "NSDL"), ("CDSL", "CDSL")])
    dp_id = serializers.CharField(max_length=20)
    demat_account_number = serializers.CharField(max_length=50)
    client_id_bo_id = serializers.CharField(max_length=20,)

    def validate(self,data):
        if DematAccount.objects.filter(demat_account_number=data["demat_account_number"]).exists():
            raise serializers.ValidationError({"demat_account_number": "This demat account number is already registered."})
        
        if DematAccount.objects.filter(dp_id=data['dp_id']).exists():
            raise serializers.ValidationError({"dp_id": "This DP ID is already used."})
        
        return data
    def create(self,validated_data):
        user = self.context['request'].user
        company_id = self.context["company_id"]

        try:
            company=CompanyInformation.objects.get(company_id=company_id, user=user)

        except CompanyInformation.DoesNotExist:
            raise serializers.ValidationError({"company_id": "Invalid company or not owned by user."})
        
        if hasattr(company, "demat_account"):
            raise serializers.ValidationError({"company": "This company already has a demat account."})
        
        demat_account = DematAccount.objects.create(
            company=company,
            user_id_updated_by=user.user_id,
            **validated_data
        )

        onboarding_app, _ = CompanyOnboardingApplication.objects.get_or_create(
            user=user,
            defaults={
                "status": "IN_PROGRESS",
                "last_accessed_step": 2,
                "company_information": company,
                "step_completion": {},
            },
        )

        update_step_4_status(application=onboarding_app,demat_ids=demat_account.demat_account_id,)
        

        return {
            "demat_account_id": demat_account.demat_account_id,
            "company_id": str(company.company_id),
            "dp_name": demat_account.dp_name,
            "depository_participant": demat_account.depository_participant,
            "dp_id": demat_account.dp_id,
            "demat_account_number": demat_account.demat_account_number,
            "client_id_bo_id": demat_account.client_id_bo_id,
            "message": "Demat account details saved successfully.",
        }

class DemateAccountGetSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()         
    company_id = serializers.SerializerMethodField() 

    class Meta:
        model = DematAccount
        fields = [
            "demat_account_id",
            "user",
            "dp_name",
            "depository_participant",
            "dp_id",
            "demat_account_number",
            "client_id_bo_id",
            "company_id",
        ]
        read_only_fields = fields

    def get_user(self, obj):
        """Return the user ID associated with this demat account."""
        return obj.company.user_id if hasattr(obj.company, "user_id") else None

    def get_company_id(self, obj):
        """Return the company's unique ID."""
        return str(obj.company.company_id)
    
class DemateAccountUpdateSerializer(serializers.Serializer):
    dp_name = serializers.CharField(max_length=50)
    depository_participant = serializers.ChoiceField(
        choices=[("NSDL", "NSDL"), ("CDSL", "CDSL")],
        required=False
    )
    dp_id = serializers.CharField(max_length=20, required=False)
    demat_account_number = serializers.CharField(max_length=50, required=False)
    client_id_bo_id = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate(self,data):
        demat_account = self.instance

        if 'demate_account_number' in data:
            existing = DematAccount.objects.filter(demate_account_number=data['demate_account_number']).exclude(demate_account_id=demat_account.demat_account_id)

            if existing.exists():
                raise serializers.ValidationError({
                    "demat_account_number": "This demat account number is already registered."
                })
            
        if "dp_id" in data:
            existing = DematAccount.objects.filter(
                dp_id=data["dp_id"]
            ).exclude(demat_account_id=demat_account.demat_account_id)
            if existing.exists():
                raise serializers.ValidationError({
                    "dp_id": "This DP ID is already used."
                })
        return data
    def update(self, instance, validated_data):
        """Update demat account details and refresh onboarding step status."""
        user = self.context["request"].user

        # Update fields dynamically
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.user_id_updated_by = user.user_id
        instance.save()

        # Update onboarding status for step 4
        try:
            onboarding_app = CompanyOnboardingApplication.objects.get(user=user)
            update_step_4_status(
                application=onboarding_app,
                demat_ids=instance.demat_account_id
            )
        except CompanyOnboardingApplication.DoesNotExist:
            pass  # If onboarding not yet started, ignore silently

        return {
            "demat_account_id": instance.demat_account_id,
            "dp_name": instance.dp_name,
            "depository_participant": instance.depository_participant,
            "dp_id": instance.dp_id,
            "demat_account_number": instance.demat_account_number,
            "client_id_bo_id": instance.client_id_bo_id,
            "message": "Demat account details updated successfully."
        }

    
           