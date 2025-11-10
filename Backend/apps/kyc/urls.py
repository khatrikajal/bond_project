from django.urls import path,include


app_name = 'kyc'

urlpatterns = [
  
    path("issuer_kyc/", include("apps.kyc.issuer_kyc.urls")),
    
]
