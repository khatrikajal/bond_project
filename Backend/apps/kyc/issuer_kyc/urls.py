from django.urls import path
from .views.CompanyAddressView import ComapnyAdressAPIView
from .views.CompanyAllAddressView import ComapnyAllAdressAPIView

from .views.CompanyInformationCreateView import (
    PanExtractionView,
    CompanyInformationCreateView,
    CompanyProfileView,
    SectorChoicesView,
    CompanyInfoByCINView,
)

from .views import BankDetailsView
from .views.CompanyDocumentView import (
    CompanyDocumentBulkUploadView,
    CompanyDocumentVerificationView,
    CompanyDocumentListView,
    CompanyDocumentDetailView,
    CompanyDocumentStatusView,
    CompanySingleDocumentUploadView,
)
from .views.DemateAccountView import DematAccountCreateView,DematAccountGetView,DematAccountUpdateView,DematAccountDelateView,FetchDematDetailsView
from rest_framework.routers import DefaultRouter

from .views.CompanyLoginView import CompanyLoginView
from .views.CompanySignatoryView import CompanySignatoryCreateView,CompanySignatoryListView,CompanySignatoryDetailView,CompanySignatoryUpdateView,CompanySignatoryDelete,CompanySignatoryStatusUpdate

from .views.CompanyRegistrationView import RegisterCompanyView
from .views.CompanySignatoryView import( CompanySignatoryCreateView,
CompanySignatoryListView,
CompanySignatoryDetailView,
CompanySignatoryUpdateView,
CompanySignatoryDelete,
CompanySignatoryStatusUpdate)




app_name = 'issuer_kyc'

urlpatterns = [
    
    path('register-company/', RegisterCompanyView.as_view(), name='register-company'),

    path("login-company/", CompanyLoginView.as_view(),name='login-company'),


    path('company-info/', CompanyInformationCreateView.as_view(), name='company-info-create'),
    path("company/address/",ComapnyAdressAPIView.as_view(),name="create-company-address"),
    path("addresses/",ComapnyAllAdressAPIView.as_view(),name="create-company-address"),
    path("pan-extraction/",PanExtractionView.as_view(),name="create-company-address"),
    path("doc-extraction/", ComapnyAllAdressAPIView.as_view(), name="upload_document"),
    path("pan-extraction/", PanExtractionView.as_view(), name="pan-extraction"),
    path("company-info/", CompanyInformationCreateView.as_view(), name="company-info-create"),

    # GET / PATCH / DELETE using token
    path("company-info/profile/", CompanyProfileView.as_view(), name="company-info-me"),

    path("company-info/cin/<str:cin>/", CompanyInfoByCINView.as_view(), name="company-info-by-cin"),
    path("company-info/sectors/", SectorChoicesView.as_view(), name="sector-choices"),

    #--- Bank Details ----
    path("bank-details/verify/", BankDetailsView.BankDetailsVerifyView.as_view(), name="bank-details-verify"),
    path("bank-details/", BankDetailsView.BankDetailsView.as_view(), name="bank-details-get"),
    path("bank-details/extract/", BankDetailsView.BankDocumentExtractView.as_view(), name="bank-details-extract"),
    path("bank-details/submit/", BankDetailsView.BankDetailsView.as_view(), name="bank-details-submit"),

    # ---------- Demate Details --------------
    path("company/demat/", DematAccountCreateView.as_view(), name="demat-account-create"),
    path('company/demat/<int:demat_account_id>/get', DematAccountGetView.as_view(), name='demat-account-get'),
    path("company/demat/<int:demat_account_id>/update", DematAccountUpdateView.as_view(), name="update-demat-account"),
    path("company/demat/<int:demat_account_id>/delete", DematAccountDelateView.as_view(), name="delete-demat-account"),
    path(
        "company/fetch-demat-details/",
        FetchDematDetailsView.as_view(),
        name="fetch-demat-details",
    ),
   
  
    

        # Bulk upload all documents for company from TOKEN
    path(
        'companies/documents/bulkupload/',
        CompanyDocumentBulkUploadView.as_view(),
        name='document-bulk-upload'
    ),

    # Get document upload status (company from TOKEN)
    path(
        'companies/documents/status/',
        CompanyDocumentStatusView.as_view(),
        name='document-status'
    ),

    # Upload single document (company from TOKEN)
    path(
        'companies/documents/upload/',
        CompanySingleDocumentUploadView.as_view(),
        name='document-single-upload'
    ),

    # Admin: Verify or Reject a document (document_id required)
    path(
        'companies/documents/<uuid:document_id>/verify/',
        CompanyDocumentVerificationView.as_view(),
        name='document-verify'
    ),

    # Get, Update, Delete a specific document (company from TOKEN)
    path(
        'companies/documents/<uuid:document_id>/',
        CompanyDocumentDetailView.as_view(),
        name='document-detail'
    ),

    # List all documents (company from TOKEN)
    path(
        'companies/documents/',
        CompanyDocumentListView.as_view(),
        name='document-list'
    ),

     #--- Signatory Details ----
     path("company/signatories/", CompanySignatoryCreateView.as_view(), name="signatory-account-create"),
     path("company/signatories/list", CompanySignatoryListView.as_view(), name="signatory-list"),
     path("company/signatories/get/<int:signatory_id>", CompanySignatoryDetailView.as_view(), name="signatory-get"),
     path('company/signatories/update/<int:signatory_id>', CompanySignatoryUpdateView.as_view(), name='signatory-update'),
     path('company/signatories/delete/<int:signatory_id>', CompanySignatoryDelete.as_view(), name='signatory-delete'),
     path('company/signatories/status/<int:signatory_id>', CompanySignatoryStatusUpdate.as_view(), name='signatory-delete'),






]




