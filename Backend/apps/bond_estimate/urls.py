# apps/bond_estimate/urls.py
from django.urls import path
from apps.bond_estimate.views.CapitalDetailsView import CapitalDetailsViewSet
from apps.bond_estimate.views.CreditRatingView import CreditRatingCreateView
from apps.bond_estimate.views.FundPositionViews import (
    FundPositionListCreateView,
    FundPositionDetailView,
    FundPositionBulkView,
)
from apps.bond_estimate.views.ProfitabilityRatiosView import ProfitabilityRatiosViewSet
from .views.CapitalDetailsView import CapitalDetailsAPI




profitability_ratios = ProfitabilityRatiosViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

profitability_ratio = ProfitabilityRatiosViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})


from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.borrowing_views import BorrowingDetailsViewSet  
from .views.CreditRatingView import (
    CreditRatingCreateView,
    CreditRatingListView,
    CreditRatingDetailView,
    CreditRatingBulkDeleteView,
    CreditRatingAgencyChoicesView,
)

from .views.PreliminaryBondRequirementsViews import (
    PreliminaryBondRequirementsListCreateView,
    PreliminaryBondRequirementsDetailView,
)
from .views.CollateralAssetVerificationViews import (
    CollateralAssetVerificationListCreateView,
    CollateralAssetVerificationDetailView,
)

from .views.BondPreviewViews import (
    BondPreviewGetView,
    BondPreviewPatchView,
)
# Initialize the DRF router
router = DefaultRouter()
router.register(r'borrowing', BorrowingDetailsViewSet, basename='borrowing')


from .views.BondEstimationApplicationView import UpdateLastAccessedStepAPI,CreateBondEstimationApplicationAPI,ListCompanyBondApplicationsAPI
from .views.FinancialDocumentView import FinancialDocumentViewSet
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


# Define URL patterns
urlpatterns = [
    path('', include(router.urls)),

    # Example for future extension:
    # path('borrowing/export/', BorrowingExportView.as_view(), name='borrowing-export'),

    # -------- Estimation Application -------

    # 1 Create blank estimation application
    path(
        "company/<uuid:company_id>/applications/create/",
        CreateBondEstimationApplicationAPI.as_view(),
        name="create-estimation-application"
    ),

    # 2 List all applications of a company
    path(
        "company/<uuid:company_id>/applications/",
        ListCompanyBondApplicationsAPI.as_view(),
        name="list-estimation-applications"
    ),

    # 3 Update last accessed step (optional)
    path(
        "company/<uuid:company_id>/applications/<uuid:application_id>/last-accessed/",
        UpdateLastAccessedStepAPI.as_view(),
        name="update-last-accessed-step"
    ),


    #---------  CaptialDetails ------------
 
    path(
        "applications/<uuid:application_id>/capital-details/",
        CapitalDetailsAPI.as_view(),
        name="capital-details"
    ),


     #---------  RatingDetails ------------
     path("company/<uuid:company_id>/credit-rating/", CreditRatingCreateView.as_view(), name="credit-rating-create"),
    

    path('choices/', CreditRatingAgencyChoicesView.as_view(), name='credit-rating-choices'),
    
    # CRUD operations
    path('ratings/<uuid:company_id>', CreditRatingListView.as_view(), name='credit-rating-list'),
    path('ratings/create/<uuid:company_id>', CreditRatingCreateView.as_view(), name='credit-rating-create'),
    path('ratings/<int:credit_rating_id>/<uuid:company_id>', CreditRatingDetailView.as_view(), name='credit-rating-detail'),
    
    # Bulk operations
    path('ratings/bulk-delete/<uuid:company_id>', CreditRatingBulkDeleteView.as_view(), name='credit-rating-bulk-delete'),


     path(
        "preliminary-bond/<uuid:company_id>",
        PreliminaryBondRequirementsListCreateView.as_view(),
        name="preliminary-bond-list-create",
    ),

    path(
        "preliminary-bond/<uuid:company_id>/<uuid:pbr_id>",
        PreliminaryBondRequirementsDetailView.as_view(),
        name="preliminary-bond-detail",
    ),

   path(
        "collateral/<uuid:company_id>/",
        CollateralAssetVerificationListCreateView.as_view(),
        name="collateral-list-create"
    ),

    # -------------------------------------------------------
    # FETCH SINGLE  +  UPDATE  +  DELETE
    # -------------------------------------------------------
    path(
        "collateral/<uuid:company_id>/<uuid:record_id>/",
        CollateralAssetVerificationDetailView.as_view(),
        name="collateral-detail"
    ),
   path(
        'fund-positions/',
        FundPositionListCreateView.as_view(),
        name='fund-position-list-create'
    ),
    path(
        'fund-positions/bulk/',
        FundPositionBulkView.as_view(),
        name='fund-position-bulk'
    ),
    path(
        'fund-positions/<uuid:pk>/',  
        FundPositionDetailView.as_view(),
        name='fund-position-detail'
    ),


    # -------------- ProfitabilityRatios -----------------
    path(
        "company/<uuid:company_id>/profitability-ratios/",
        profitability_ratios,
        name="profitability-ratios-list",
    ),
    path(
        "company/<uuid:company_id>/profitability-ratios/<int:ratio_id>/",
        profitability_ratio,
        name="profitability-ratios-detail",
    ),
     path(
        "preview/<uuid:company_id>/",
        BondPreviewGetView.as_view(),
        name="bond-preview-get",
    ),
    path(
        "preview/<uuid:company_id>/update/",
        BondPreviewPatchView.as_view(),
        name="bond-preview-patch",
    ),


 # ----------------FinancialDocuments-------------
    path("financial-documents/upload/", TempFileUploadView.as_view(), name="financial-documents-upload"),
    path(
        "company/financial-documents/",
        financial_documents,
        name="financial-documents"
    ),

    path(
        "company/financial-documents/<int:document_id>/",
        financial_document_detail,
        name="financial-document-detail"
    ),

    #bulk actions
    path(
        "company/financial-documents/bulk_upload/",
        FinancialDocumentViewSet.as_view({'post': 'bulk_upload'}),
        name="financial-documents-bulk-upload"
    ),
    path(
        "company/financial-documents/bulk_update/",
        FinancialDocumentViewSet.as_view({'patch': 'bulk_update'}),
        name="financial-documents-bulk-update"
    ),
    path(
        "company/financial-documents/bulk_delete/",
        FinancialDocumentViewSet.as_view({'delete': 'bulk_delete'}),
        name="financial-documents-bulk-delete"
    ),

    # extra actions
    path(
        "company/financial-documents/<int:pk>/verify/",
        FinancialDocumentViewSet.as_view({'post': 'verify'}),
        name="financial-document-verify"
    ),

    path(
        "company/financial-documents/<int:pk>/download/",
        FinancialDocumentViewSet.as_view({'get': 'download'}),
        name="financial-document-download"
    ),

    path(
        "company/financial-documents/missing/",
        FinancialDocumentViewSet.as_view({'get': 'missing_documents'}),
        name="financial-documents-missing"
    ),

    #------- Final Submit -------------
   
    # path("company/final-submit/", FinalSubmitAPIView.as_view(), name="final-submit"),
   
]

