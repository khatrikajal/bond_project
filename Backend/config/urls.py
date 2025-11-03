from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views import defaults as default_views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# Default error handlers
handler400 = default_views.bad_request
handler403 = default_views.permission_denied
handler500 = default_views.server_error

# Base urlpatterns
urlpatterns = [
    # path(settings.ADMIN_URL, admin.site.urls),  
    path("admin/", admin.site.urls),
    # # Keep this for admin
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]

# Serve static files in DEBUG mode
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()

# API URLs
urlpatterns += [
    # API docs
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
    # Placeholder for your app URLs (create apps/urls.py later)
    path("api/", include("apps.urls")),

    # path("api/", include("apps.kyc.issuer_kyc.urls")),
]

# Debug error pages in development
if settings.DEBUG:
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "500/",
            default_views.server_error,
        ),
    ]

    # Optional: debug toolbar
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
