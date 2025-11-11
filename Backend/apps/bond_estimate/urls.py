from django.urls import path
from apps.bond_estimate.views.CapitalDetailsView import CapitalDetailsViewSet

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


app_name = 'bond_estimate'

urlpatterns = [

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

]
