from django.urls import path

from . import views

app_name = "facturacion_ml"

urlpatterns = [
    path("", views.index, name="index"),
]
