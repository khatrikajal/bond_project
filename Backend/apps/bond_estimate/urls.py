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


capital_details = CapitalDetailsViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

capital_detail = CapitalDetailsViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})


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

# Define URL patterns
urlpatterns = [
    path('', include(router.urls)),

    # Example for future extension:
    # path('borrowing/export/', BorrowingExportView.as_view(), name='borrowing-export'),
    #---------  CaptialDetails ------------
    path(
        "company/<uuid:company_id>/capital-details/",
        capital_details,
        name="capital-details-list",
    ),

    path(
        "company/<uuid:company_id>/capital-details/<int:capital_detail_id>/",
        capital_detail,
        name="capital-details-detail",
    ),

    path(
        "company/<uuid:company_id>/capital-details/<int:capital_detail_id>/",
        capital_detail,
        name="capital-details-detail",
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
   
]

