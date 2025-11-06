

from django.contrib import admin
from apps.kyc.issuer_kyc.models.CompanyAdressModel import CompanyAddress
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from apps.kyc.issuer_kyc.models.CompanyOnboardingApplicationModel import CompanyOnboardingApplication
from apps.kyc.issuer_kyc.models.BankDetailsModel import BankDetails

from .models.CompanyDocumentModel import CompanyDocument
from django import forms

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


admin.site.register(CompanyOnboardingApplication)


admin.site.register(BankDetails)
# Form class - NO DECORATOR HERE
class CompanyDocumentAdminForm(forms.ModelForm):
    """Custom form for uploading documents in admin"""
    
    file_upload = forms.FileField(
        required=False,
        label="Upload Document",
        help_text="Upload PDF, JPEG, JPG, or PNG file (max 5MB)"
    )
    
    class Meta:
        model = CompanyDocument
        fields = [
            'company',
            'document_name',
            'is_verified',
            'del_flag',
            'user_id_updated_by'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['file_upload'].required = True
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        file_upload = self.cleaned_data.get('file_upload')
        if file_upload:
            file_content = file_upload.read()
            instance.document_file = file_content
            instance.file_size = file_upload.size
            instance.document_type = CompanyDocument.detect_file_type(file_upload.name)
        if commit:
            instance.save()
        return instance


# Admin class - DECORATOR HERE
@admin.register(CompanyDocument)
class CompanyDocumentAdmin(admin.ModelAdmin):
    """Admin interface for Company Documents"""
    
    form = CompanyDocumentAdminForm
    
    list_display = [
        'document_id',
        'company_name',
        'document_name_display',
        'document_type',
        'file_size_display',
        'is_mandatory',
        'is_verified',
        'status_badge',
        'uploaded_at'
    ]
    
    list_filter = [
        'document_name',
        'document_type',
        'is_mandatory',
        'is_verified',
        'del_flag',
        'uploaded_at'
    ]
    
    search_fields = [
        'company__company_name',
        'company__corporate_identification_number',
        'document_name'
    ]
    
    readonly_fields = [
        'document_id',
        'document_type',
        'uploaded_at',
        'created_at',
        'updated_at',
        'file_size',
        'file_size_display',
        'file_info'
    ]
    
    fieldsets = (
        ('Document Information', {
            'fields': (
                'document_id',
                'company',
                'document_name',
                'file_upload',
            )
        }),
        ('File Details (Auto-detected)', {
            'fields': (
                'document_type',
                'file_size_display',
                'file_info',
                'uploaded_at',
            ),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': (
                'is_mandatory',
                'is_verified',
                'del_flag',
            )
        }),
        ('Audit Information', {
            'fields': (
                'created_at',
                'updated_at',
                'user_id_updated_by',
            ),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 25
    date_hierarchy = 'uploaded_at'
    
    actions = ['mark_as_verified', 'mark_as_unverified', 'soft_delete_documents']
    
    def company_name(self, obj):
        """Display company name"""
        return obj.company.company_name if obj.company else '-'
    company_name.short_description = 'Company'
    company_name.admin_order_field = 'company__company_name'
    
    def document_name_display(self, obj):
        """Display full document name"""
        return obj.get_document_name_display()
    document_name_display.short_description = 'Document Type'
    document_name_display.admin_order_field = 'document_name'
    
    def file_size_display(self, obj):
        """Display file size in human-readable format"""
        if not obj.file_size:
            return '-'
        size_mb = obj.file_size / (1024 * 1024)
        if size_mb < 1:
            size_kb = obj.file_size / 1024
            return f"{size_kb:.2f} KB"
        return f"{size_mb:.2f} MB"
    file_size_display.short_description = 'File Size'
    file_size_display.admin_order_field = 'file_size'
    
    def file_info(self, obj):
        """Display file information"""
        if not obj.document_file:
            return "No file uploaded"
        
        if obj.document_type == 'PDF':
            icon = '📄'
        else:
            icon = '🖼️'
        
        return format_html(
            '{} {} Document ({})',
            icon,
            obj.document_type,
            self.file_size_display(obj)
        )
    file_info.short_description = 'File Info'
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        if obj.del_flag == 1:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">Deleted</span>'
            )
        elif obj.is_verified:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">Verified</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 10px; border-radius: 3px;">Pending</span>'
            )
    status_badge.short_description = 'Status'
    
    def get_queryset(self, request):
        """Optimize queries with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'company',
            'user_id_updated_by'
        )
    
    def save_model(self, request, obj, form, change):
        """Set user who modified the document"""
        obj.user_id_updated_by = request.user
        super().save_model(request, obj, form, change)
    
    # Admin actions
    def mark_as_verified(self, request, queryset):
        """Mark selected documents as verified"""
        updated = queryset.update(
            is_verified=True,
            user_id_updated_by=request.user
        )
        self.message_user(
            request,
            f'{updated} document(s) marked as verified.'
        )
    mark_as_verified.short_description = "Mark as Verified"
    
    def mark_as_unverified(self, request, queryset):
        """Mark selected documents as unverified"""
        updated = queryset.update(
            is_verified=False,
            user_id_updated_by=request.user
        )
        self.message_user(
            request,
            f'{updated} document(s) marked as unverified.'
        )
    mark_as_unverified.short_description = "Mark as Unverified"
    
    def soft_delete_documents(self, request, queryset):
        """Soft delete selected documents"""
        updated = queryset.update(
            del_flag=1,
            user_id_updated_by=request.user
        )
        self.message_user(
            request,
            f'{updated} document(s) soft deleted.'
        )
    soft_delete_documents.short_description = "Soft Delete"
