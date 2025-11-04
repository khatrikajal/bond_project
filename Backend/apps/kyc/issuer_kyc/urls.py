from django.urls import path
from .views.CompanyAddressView import ComapnyAdressAPIView
from .views.CompanyInformationCreateView import CompanyInformationCreateView,PanExtractionView

app_name = 'issuer_kyc'

urlpatterns = [
    path('temp/', ComapnyAdressAPIView.as_view(), name='temp'),
    path('company-info/', CompanyInformationCreateView.as_view(), name='company-info-create'),
    path("company/<uuid:company_id>/address/",ComapnyAdressAPIView.as_view(),name="create-company-address"),
    path("pan-extraction/",PanExtractionView.as_view(),name="create-company-address")
   
  
]
