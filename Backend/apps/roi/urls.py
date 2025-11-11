from django.urls import path,include


app_name = 'roi'

urlpatterns = [
  
    path("bond_estimation/", include("apps.roi.urls")),
    
]


