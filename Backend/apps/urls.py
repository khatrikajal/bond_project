# G:\bond_platform\Backend\apps\urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # path('admin/', admin.site.urls),

    # Authentication app
    path('auth/', include('apps.authentication.urls')),

 

    path('bond_estimate/',include('apps.bond_estimate.urls')),

    # # Audit app
    # path('audit/', include('apps.audit.urls')),

    # # Bonds app
    path('bonds/', include('apps.bonds.urls')),

    path('kyc/',include('apps.kyc.urls')),
    
    
    path('roi/',include('apps.roi.urls'))


    # # Compliance app
    # path('api/compliance/', include('apps.compliance.urls')),

    # # Dashboard app
    # path('api/dashboard/', include('apps.dashboard.urls')),

    # # Investments app
    # path('api/investments/', include('apps.investments.urls')),

    # # Market Data app
    # path('api/market_data/', include('apps.market_data.urls')),

    # # Notifications app
    # path('api/notifications/', include('apps.notifications.urls')),

    # # Payments app
    # path('api/payments/', include('apps.payments.urls')),

    # # Regulatory app
    # path('api/regulatory/', include('apps.regulatory.urls')),

    # # Reporting app
    # path('api/reporting/', include('apps.reporting.urls')),

    # # Risk Management app
    # path('api/risk_management/', include('apps.risk_management.urls')),

    # # Settlement app
    # path('api/settlement/', include('apps.settlement.urls')),

    # # Trading app
    # path('api/trading/', include('apps.trading.urls')),
]
