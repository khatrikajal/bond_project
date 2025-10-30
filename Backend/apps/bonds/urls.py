# G:\bond_platform\Backend\apps\bonds\urls.py
from django.urls import path
from .views import *

urlpatterns = [
    
    path('stats/', StatsView.as_view(), name='stats'),
    path('bonds/featured/',HomePageFeaturedBonds.as_view(), name='home-featured-bonds'),
    path('bonds/', BondsListView.as_view(), name='bond-list'),
    path('bond/research-data/',BondResearchDataView.as_view(), name='bond-research-data'),
    path('bond/snapshot/',BondSnapshotView.as_view(), name='bond-snapshot'),
    path('bond/',BondDetailView.as_view(), name='bond-detail'),
    path('bonds/search/', BondSearchORMListView.as_view(), name='bond-search'),
    path('similar-bonds/',SimilarBondsView.as_view(), name='similar-bonds'),
    path('contact/', ContactMessageView.as_view(), name='contact'),
    
    
]
