# apps/bond_estimate/urls.py
from django.urls import path
from apps.bond_estimate.views.CapitalDetailsView import CapitalDetailsViewSet
from apps.bond_estimate.views.CreditRatingView import CreditRatingCreateView
from apps.bond_estimate.views.FundPositionViews import (
    FundPositionListCreateView,
    FundPositionDetailView,
    FundPositionBulkView,
)

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



from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.borrowing_views import BorrowingDetailsViewSet  # adjust import if needed

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

]

