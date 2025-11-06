from django import forms
from apps.kyc.issuer_kyc.models.CompanyDocumentModel import CompanyDocument


class CompanyDocumentAdminForm(forms.ModelForm):
    upload_file = forms.FileField(required=False, label="Upload Document")

    class Meta:
        model = CompanyDocument
        fields = ['company', 'document_name', 'document_type', 'is_mandatory', 'is_verified', 'del_flag']

    def save(self, commit=True):
        instance = super().save(commit=False)

        uploaded = self.cleaned_data.get('upload_file')
        if uploaded:
            instance.document_file = uploaded.read()
            instance.file_size = uploaded.size
            instance.document_type = CompanyDocument.detect_file_type(uploaded.name)

        if commit:
            instance.save()
        return instance
