from django.contrib import admin
from apps.kyc.issuer_kyc.models.CompanyAdressModel import CompanyAddress
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation

@admin.register(CompanyAddress)
class CompanyAddressAdmin(admin.ModelAdmin):
    list_display = (
        "address_id",
        "company",
        "city",
        "state_ut",
        "pin_code",
        "country",
        "address_type",
        "company_contact_email",
        "company_contact_phone",
        "created_at",
    )
    search_fields = (
        "company__company_name",
        "city",
        "state_ut",
        "company_contact_email",
    )
    list_filter = ("state_ut", "country", "address_type")
    list_select_related = ("company",)
    ordering = ("-created_at",)


@admin.register(CompanyInformation)
class CompanyInformationAdmin(admin.ModelAdmin):
    list_display = (
        "company_id",
        "company_name",
        "corporate_identification_number",
        "company_pan_number",
        "entity_type",
        "gstin",
        "date_of_incorporation",
        "created_at",
    )
    search_fields = (
        "company_name",
        "corporate_identification_number",
        "company_pan_number",
        "gstin",
    )
    list_filter = ("entity_type", "state_of_incorporation", "created_at")
    ordering = ("-created_at",)