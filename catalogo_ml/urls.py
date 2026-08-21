from django.urls import path

from . import views

app_name = "catalogo_ml"

urlpatterns = [
    path("", views.index, name="index"),
    path("masivo/", views.toggle_masivo, name="toggle_masivo"),
    path("ml/conectar/", views.ml_login, name="ml_login"),
    path("ml/callback/", views.ml_callback, name="ml_callback"),
    path("ml/precio/", views.actualizar_porcentaje_ajuste, name="actualizar_porcentaje_ajuste"),
    path("<str:sku>/toggle/", views.toggle_sync, name="toggle_sync"),
]
