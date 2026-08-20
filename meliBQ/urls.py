"""
URL configuration for meliBQ project.

Cada app resuelve sus propias rutas en su `urls.py` — este archivo solo compone.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("catalogo/", include("catalogo_ml.urls")),
    path("facturacion/", include("facturacion_ml.urls")),
]
