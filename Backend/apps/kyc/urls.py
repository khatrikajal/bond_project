
from django.urls import path,include

app_name = 'kyc'

urlpatterns = [

    path('v1/',include('apps.kyc.issuer_kyc.urls',namespace='issuer_kyc')),
   
]  