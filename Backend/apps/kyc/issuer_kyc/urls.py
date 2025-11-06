from django.urls import path
from .views.CompanyAddressView import ComapnyAdressAPIView
from .views.CompanyInformationCreateView import CompanyInformationCreateView,PanExtractionView,CompanyInfoGetView,CompanyInformationUpdateView,CompanyInfoDeleteView
from .views import BankDetailsView

app_name = 'issuer_kyc'

urlpatterns = [
    path('temp/', ComapnyAdressAPIView.as_view(), name='temp'),
    path('company-info/', CompanyInformationCreateView.as_view(), name='company-info-create'),
    path("company/<uuid:company_id>/address/",ComapnyAdressAPIView.as_view(),name="create-company-address"),
    path("pan-extraction/",PanExtractionView.as_view(),name="create-company-address"),
    path('company-info/<uuid:company_id>/', CompanyInfoGetView.as_view(), name='company-info-get'),
    path('company-info/<uuid:company_id>/update/', CompanyInformationUpdateView.as_view(), name='company-info-update'),
    path("company-info/<uuid:company_id>/delete/", CompanyInfoDeleteView.as_view(), name="company-info-delete"),

    #--- Bank Details ----
    path("bank-details/<uuid:company_id>/verify/", BankDetailsView.BankDetailsVerifyView.as_view(), name="bank-details-verify"),
    path("bank-details/<uuid:company_id>/", BankDetailsView.BankDetailsView.as_view(), name="bank-details-get"),
    path("bank-details/<uuid:company_id>/extract/", BankDetailsView.BankDocumentExtractView.as_view(), name="bank-details-extract"),
    path("bank-details/<uuid:company_id>/submit/", BankDetailsView.BankDetailsView.as_view(), name="bank-details-submit"),

  
]
