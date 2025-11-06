from django.urls import path
from .views.CompanyAddressView import ComapnyAdressAPIView
from .views.CompanyAllAddressView import ComapnyAllAdressAPIView
from .views.CompanyInformationCreateView import CompanyInformationCreateView,PanExtractionView
from .views.CompanyInformationCreateView import CompanyInformationCreateView,PanExtractionView,CompanyInfoGetView,CompanyInformationUpdateView,CompanyInfoDeleteView
from .views.DemateAccountView import DematAccountCreateView,DematAccountGetView,DematAccountUpdateView,DematAccountDelateView

app_name = 'issuer_kyc'

urlpatterns = [
    path('temp/', ComapnyAdressAPIView.as_view(), name='temp'),
    path('company-info/', CompanyInformationCreateView.as_view(), name='company-info-create'),
    path("company/<uuid:company_id>/address/",ComapnyAdressAPIView.as_view(),name="create-company-address"),
    path("addresses/",ComapnyAllAdressAPIView.as_view(),name="create-company-address"),
    path("pan-extraction/",PanExtractionView.as_view(),name="create-company-address"),
    path("doc-extraction/", ComapnyAllAdressAPIView.as_view(), name="upload_document"),
    path("pan-extraction/",PanExtractionView.as_view(),name="create-company-address"),
    path('company-info/<uuid:company_id>/', CompanyInfoGetView.as_view(), name='company-info-get'),
    path('company-info/<uuid:company_id>/update/', CompanyInformationUpdateView.as_view(), name='company-info-update'),
    path("company-info/<uuid:company_id>/delete/", CompanyInfoDeleteView.as_view(), name="company-info-delete"),
    path("company/<uuid:company_id>/demat/", DematAccountCreateView.as_view(), name="demat-account-create"),
    path('company/demat/<int:demat_account_id>/get', DematAccountGetView.as_view(), name='demat-account-get'),
    path("company/demat/<int:demat_account_id>/update", DematAccountUpdateView.as_view(), name="update-demat-account"),
    path("company/demat/<int:demat_account_id>/delete", DematAccountDelateView.as_view(), name="delete-demat-account"),
   
  
]
