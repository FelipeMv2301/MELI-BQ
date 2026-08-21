from django.urls import path

from . import views

app_name = "catalogo_ml"

urlpatterns = [
    path("", views.index, name="index"),
    path("masivo/", views.toggle_masivo, name="toggle_masivo"),
    path("vincular/", views.vincular_masivo, name="vincular_masivo"),
    path("ml/conectar/", views.ml_login, name="ml_login"),
    path("ml/callback/", views.ml_callback, name="ml_callback"),
    path("ml/precio/", views.actualizar_porcentaje_ajuste, name="actualizar_porcentaje_ajuste"),
    path("ml/precio-masivo/", views.aplicar_porcentaje_masivo, name="aplicar_porcentaje_masivo"),
    path("vinculo/<int:vinculo_id>/guardar/", views.guardar_vinculo, name="guardar_vinculo"),
    path("vinculo/<int:vinculo_id>/borrar/", views.desvincular, name="desvincular"),
    # Las rutas de un solo segmento van al final: `<str:sku>/` matchearía "masivo/" o "vincular/"
    # si estuviera antes que ellas.
    path("<str:sku>/toggle/", views.toggle_sync, name="toggle_sync"),
    path("<str:sku>/precio/", views.guardar_precio_producto, name="guardar_precio_producto"),
    path("<str:sku>/vincular/", views.vincular_a_mano, name="vincular_a_mano"),
    path("<str:sku>/", views.detalle, name="detalle"),
]
