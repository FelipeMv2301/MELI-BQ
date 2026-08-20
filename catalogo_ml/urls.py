from django.urls import path

from . import views

app_name = "catalogo_ml"

urlpatterns = [
    path("", views.index, name="index"),
    path("masivo/", views.toggle_masivo, name="toggle_masivo"),
    path("<str:sku>/toggle/", views.toggle_sync, name="toggle_sync"),
]
