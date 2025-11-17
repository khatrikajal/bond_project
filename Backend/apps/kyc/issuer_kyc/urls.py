from django.urls import path
from .views.CompanyAddressView import ComapnyAdressAPIView
from .views.CompanyAllAddressView import ComapnyAllAdressAPIView

from .views.CompanyInformationCreateView import (
    CompanyInformationCreateView,
    PanExtractionView,
    CompanyInfoGetView,
    CompanyInformationUpdateView,
    CompanyInfoDeleteView,
    CompanyInfoByCINView,
    SectorChoicesView,
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
from .views.FinancialDocumentView import FinancialDocumentViewSet

from .views.CompanySignatoryView import CompanySignatoryCreateView,CompanySignatoryListView,CompanySignatoryDetailView,CompanySignatoryUpdateView,CompanySignatoryDelete,CompanySignatoryStatusUpdate


from .views.CompanySignatoryView import( CompanySignatoryCreateView,
CompanySignatoryListView,
CompanySignatoryDetailView,
CompanySignatoryUpdateView,
CompanySignatoryDelete,
CompanySignatoryStatusUpdate)

from .views.FinalSubmitAPIView import FinalSubmitAPIView
from .views.TempFileUploadView import TempFileUploadView

financial_documents = FinancialDocumentViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

financial_document_detail = FinancialDocumentViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})



app_name = 'issuer_kyc'

urlpatterns = [
    
    


    path('company-info/', CompanyInformationCreateView.as_view(), name='company-info-create'),
    path("company/address/",ComapnyAdressAPIView.as_view(),name="create-company-address"),
    path("addresses/",ComapnyAllAdressAPIView.as_view(),name="create-company-address"),
    path("pan-extraction/",PanExtractionView.as_view(),name="create-company-address"),
    path("doc-extraction/", ComapnyAllAdressAPIView.as_view(), name="upload_document"),
    path("pan-extraction/",PanExtractionView.as_view(),name="create-company-address"),
    path('company-info/<uuid:company_id>/', CompanyInfoGetView.as_view(), name='company-info-get'),
    path('company-info/<uuid:company_id>/update/', CompanyInformationUpdateView.as_view(), name='company-info-update'),
    path("company-info/<uuid:company_id>/delete/", CompanyInfoDeleteView.as_view(), name="company-info-delete"),
    # Fetch Through CIN
    path('company-info/cin/<str:cin>/', CompanyInfoByCINView.as_view(), name='company-info-by-cin'),
    path("company-info/sectors/", SectorChoicesView.as_view(), name="sector-choices"),

    #--- Bank Details ----
    path("bank-details/verify/", BankDetailsView.BankDetailsVerifyView.as_view(), name="bank-details-verify"),
    path("bank-details/", BankDetailsView.BankDetailsView.as_view(), name="bank-details-get"),
    path("bank-details/extract/", BankDetailsView.BankDocumentExtractView.as_view(), name="bank-details-extract"),
    path("bank-details/submit/", BankDetailsView.BankDetailsView.as_view(), name="bank-details-submit"),

    # ---------- Demate Details --------------
    path("company/<uuid:company_id>/demat/", DematAccountCreateView.as_view(), name="demat-account-create"),
    path('company/demat/<int:demat_account_id>/get', DematAccountGetView.as_view(), name='demat-account-get'),
    path("company/demat/<int:demat_account_id>/update", DematAccountUpdateView.as_view(), name="update-demat-account"),
    path("company/demat/<int:demat_account_id>/delete", DematAccountDelateView.as_view(), name="delete-demat-account"),
    path(
        "company/<uuid:company_id>/fetch-demat-details/",
        FetchDematDetailsView.as_view(),
        name="fetch-demat-details",
    ),
   
  
    # Bulk upload all documents at once 
    path(
        'companies/<uuid:company_id>/documents/bulkupload/',
        CompanyDocumentBulkUploadView.as_view(),
        name='document-bulk-upload'
    ),
    
    # Get document upload status 
    path(
        'companies/<uuid:company_id>/documents/status/',
        CompanyDocumentStatusView.as_view(),
        name='document-status'
    ),
    
    # Upload single document
    path(
        'companies/<uuid:company_id>/documents/upload/',
        CompanySingleDocumentUploadView.as_view(),
        name='document-single-upload'
    ),
    
    # Admin verification endpoint 
    path(
        'companies/<uuid:company_id>/documents/<uuid:document_id>/verify/',
        CompanyDocumentVerificationView.as_view(),
        name='document-verify'
    ),
    
    # Get, update, delete specific document
    path(
        'companies/<uuid:company_id>/documents/<uuid:document_id>/',
        CompanyDocumentDetailView.as_view(),
        name='document-detail'
    ),
    
    # List all documents for company 
    path(
        'companies/<uuid:company_id>/documents/',
        CompanyDocumentListView.as_view(),
        name='document-list'
    ),


    # ----------------FinancialDocuments-------------
    path("financial-documents/upload/", TempFileUploadView.as_view(), name="financial-documents-upload"),
    path(
        "company/<uuid:company_id>//",
        financial_documents,
        name="financial-documents"
    ),

    path(
        "company/<uuid:company_id>/financial-documents/<int:document_id>/",
        financial_document_detail,
        name="financial-document-detail"
    ),

    #bulk actions
    path(
        "company/<uuid:company_id>/financial-documents/bulk_upload/",
        FinancialDocumentViewSet.as_view({'post': 'bulk_upload'}),
        name="financial-documents-bulk-upload"
    ),
    path(
        "company/<uuid:company_id>/financial-documents/bulk_update/",
        FinancialDocumentViewSet.as_view({'patch': 'bulk_update'}),
        name="financial-documents-bulk-update"
    ),
    path(
        "company/<uuid:company_id>/financial-documents/bulk_delete/",
        FinancialDocumentViewSet.as_view({'delete': 'bulk_delete'}),
        name="financial-documents-bulk-delete"
    ),

    # extra actions
    path(
        "company/<uuid:company_id>/financial-documents/<int:pk>/verify/",
        FinancialDocumentViewSet.as_view({'post': 'verify'}),
        name="financial-document-verify"
    ),

    path(
        "company/<uuid:company_id>/financial-documents/<int:pk>/download/",
        FinancialDocumentViewSet.as_view({'get': 'download'}),
        name="financial-document-download"
    ),

    path(
        "company/<uuid:company_id>/financial-documents/missing/",
        FinancialDocumentViewSet.as_view({'get': 'missing_documents'}),
        name="financial-documents-missing"
    ),
     #--- Signatory Details ----
     path("company/<uuid:company_id>/signatories/", CompanySignatoryCreateView.as_view(), name="signatory-account-create"),
     path("company/<uuid:company_id>/signatories/list", CompanySignatoryListView.as_view(), name="signatory-list"),
     path("company/<int:signatory_id>/signatories/get", CompanySignatoryDetailView.as_view(), name="signatory-get"),
     path('company/<int:signatory_id>/signatories/update', CompanySignatoryUpdateView.as_view(), name='signatory-update'),
     path('company/<int:signatory_id>/signatories/delete', CompanySignatoryDelete.as_view(), name='signatory-delete'),
     path('company/<int:signatory_id>/signatories/status', CompanySignatoryStatusUpdate.as_view(), name='signatory-delete'),



    #------- Final Submit -------------
   
    path("company/<uuid:company_id>/final-submit/", FinalSubmitAPIView.as_view(), name="final-submit"),



]




