from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "roi"

router = DefaultRouter()
router.register(r'fund-position', views.FundPositionViewSet, basename='fund_position')
router.register(r'credit-rating', views.CreditRatingViewSet, basename='credit_rating')
router.register(r'borrowing-details', views.BorrowingDetailViewSet, basename='borrowing_detail')
router.register(r'capital-details', views.CapitalDetailViewSet, basename='capital_detail')
router.register(r'profitability-ratio', views.ProfitabilityRatioViewSet, basename='profitability_ratio')

urlpatterns = [
    path('', include(router.urls)),
]
