from django.urls import path
from .views.CompanyAddressView import ComapnyAdressAPIView

app_name = 'issuer_kyc'

urlpatterns = [
    path('temp/', ComapnyAdressAPIView.as_view(), name='temp'),
  
]