from django.urls import path
from .views.CompanyAddressView import ComapnyAdressAPIView
from .views.CompanyInformationCreateView import CompanyInformationCreateView,PanExtractionView,CompanyInfoGetView,CompanyInformationUpdateView,CompanyInfoDeleteView
from .views.CompanyDocumentView import (
    CompanyDocumentBulkUploadView,
    CompanyDocumentVerificationView,
    CompanyDocumentListView,
    CompanyDocumentDetailView,
    CompanyDocumentStatusView,
    CompanySingleDocumentUploadView,
)
app_name = 'issuer_kyc'

urlpatterns = [
    path('temp/', ComapnyAdressAPIView.as_view(), name='temp'),
    path('company-info/', CompanyInformationCreateView.as_view(), name='company-info-create'),
    path("company/<uuid:company_id>/address/",ComapnyAdressAPIView.as_view(),name="create-company-address"),
    path("pan-extraction/",PanExtractionView.as_view(),name="create-company-address"),
    path('company-info/<uuid:company_id>/', CompanyInfoGetView.as_view(), name='company-info-get'),
    path('company-info/<uuid:company_id>/update/', CompanyInformationUpdateView.as_view(), name='company-info-update'),
    path("company-info/<uuid:company_id>/delete/", CompanyInfoDeleteView.as_view(), name="company-info-delete"),
   # Bulk upload all documents at once (main endpoint as per UI)
  
    # Bulk upload all documents at once (used during onboarding)
    path(
        'companies/<uuid:company_id>/documents/bulkupload/',
        CompanyDocumentBulkUploadView.as_view(),
        name='document-bulk-upload'
    ),
    
    # Get document upload status (must be before document-list)
    path(
        'companies/<uuid:company_id>/documents/status/',
        CompanyDocumentStatusView.as_view(),
        name='document-status'
    ),
    
    # Upload single document (must be before document-detail)
    path(
        'companies/<uuid:company_id>/documents/upload/',
        CompanySingleDocumentUploadView.as_view(),
        name='document-single-upload'
    ),
    
    # Admin verification endpoint (must be before document-detail)
    path(
        'companies/<uuid:company_id>/documents/<uuid:document_id>/verify/',
        CompanyDocumentVerificationView.as_view(),
        name='document-verify'
    ),
    
    # Get, update, delete specific document (UUID pattern)
    path(
        'companies/<uuid:company_id>/documents/<uuid:document_id>/',
        CompanyDocumentDetailView.as_view(),
        name='document-detail'
    ),
    
    # List all documents for company (must be LAST)
    path(
        'companies/<uuid:company_id>/documents/',
        CompanyDocumentListView.as_view(),
        name='document-list'
    ),
]




