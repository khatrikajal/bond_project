# apps/bond_estimate/urls.py
from django.urls import path
from apps.bond_estimate.views.CapitalDetailsView import CapitalDetailsViewSet



from .views.CapitalDetailsView import CapitalDetailsAPI
from .views.BondEstimationStatusView import BondEstimationStatusAPI
from .views.ProfitabilityRatiosView import ProfitabilityRatiosViewSet
profitability_ratios = ProfitabilityRatiosViewSet.as_view({
    "post": "create",
    "get": "list",
    "put": "update",
    "patch": "partial_update",
    "delete": "destroy",
})

from .views.CreditRatingView import CreditRatingViewSet

credit_rating_list = CreditRatingViewSet.as_view({
    "get": "list",
    "post": "create"
})

credit_rating_detail = CreditRatingViewSet.as_view({
    "patch": "partial_update",
    "delete": "destroy"
})



from .views.FundPositionViews import FundPositionAPI
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.borrowing_views import BorrowingDetailsViewSet  


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

from .views.borrowing_views import BorrowingDetailsViewSet
router.register(
    r"applications/(?P<application_id>[0-9a-f-]+)/borrowings",
    BorrowingDetailsViewSet,
    basename="borrowing-details"
)

from .views.BorrowingChoices import BorrowingChoicesAPI
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
    # -------- Fund Position -------
     path(
        "applications/<uuid:application_id>/fund-position/",
        FundPositionAPI.as_view(),
        name="fund-position"
    ),

        # -------- Borrowing Details -------

        path("borrowing/choices/", BorrowingChoicesAPI.as_view(), name="borrowing-choices"),

    # Example for future extension:
    # path('borrowing/export/', BorrowingExportView.as_view(), name='borrowing-export'),

    # -------- Estimation Application -------

    path(
        "applications/<uuid:application_id>/status/",
        BondEstimationStatusAPI.as_view(),
        name="bond-estimation-status"
    ),

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

    path("applications/<uuid:application_id>/credit-ratings/", credit_rating_list),
    path("applications/<uuid:application_id>/credit-ratings/<int:pk>/", credit_rating_detail),
    path("applications/<uuid:application_id>/credit-ratings/choices/", CreditRatingViewSet.as_view({"get": "choices"})),


        #---------  PreliminaryBondRequirements ------------

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


   

    # -------------- ProfitabilityRatios -----------------
 
    path(
        "applications/<uuid:application_id>/profitability/",
        profitability_ratios,
        name="application-profitability-ratios"
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

