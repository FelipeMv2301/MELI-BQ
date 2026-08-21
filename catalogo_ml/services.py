"""
Reglas de negocio del Módulo 1 — la vista solo orquesta y presenta (mismo criterio arquitectónico
que gestorBQ: pedidos/services.py).
"""

import logging
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone

from integraciones import ml_client, stockservice_client

from .models import ConfiguracionSyncML, MLItemMap, MLToken, SkuSyncConfig

PAGE_SIZE = 50

# Margen antes de que expire (ML da 6hs) para refrescar de forma proactiva — evita que dos
# requests concurrentes intenten refrescar al mismo tiempo y uno pierda el refresh_token de un
# solo uso del otro (ver Documentaciones/MercadoLibre/autenticacion.md).
_MARGEN_REFRESH = timedelta(minutes=10)

# Bodegas "web" (mismo criterio que WEB_WAREHOUSES de Stock-Service, sap_stock.py) — el stock que
# se muestra acá es el que hoy alimenta WooCommerce, no necesariamente el que se termine
# sincronizando a ML (esa regla de bodega por SKU es HU-CM3.2, todavía sin definir).
_BODEGAS_WEB = ("stock_01", "stock_11")

logger = logging.getLogger(__name__)


def obtener_config_y_mapa(skus):
    """Trae SkuSyncConfig y MLItemMap de una sola consulta cada uno — evita N+1 al armar la grilla."""
    configs = {c.sku: c for c in SkuSyncConfig.objects.filter(sku__in=skus)}
    mapas = {m.sku: m for m in MLItemMap.objects.filter(sku__in=skus)}
    return configs, mapas


def construir_fila_catalogo(item, config, mapa):
    """
    item: dict crudo de stockservice_client.obtener_catalogo() (sku, name, price, stock_01...).
    config: SkuSyncConfig o None (todavía no fue tocado desde la grilla).
    mapa: MLItemMap o None (todavía no publicado en ML).
    """
    return {
        "sku": item["sku"],
        "nombre": item.get("name") or "",
        "precio_neto": item.get("price"),
        "stock_web": sum(item.get(bodega) or 0 for bodega in _BODEGAS_WEB),
        "sync_stock": config.sync_stock if config else False,
        "sync_price": config.sync_price if config else False,
        "enabled": config.enabled if config else True,
        "estado": mapa.get_status_display() if mapa else "No sincronizado",
        "ml_item_id": mapa.ml_item_id if mapa else None,
    }


def construir_fila_por_sku(sku):
    """
    HU-CM1.2 — reconstruye UNA fila después de un toggle, sin recargar toda la grilla. Busca por
    `search=sku` en Stock-Service y se queda con el match exacto (search es ILIKE parcial, no
    alcanza con "el primer resultado").
    """
    respuesta = stockservice_client.obtener_catalogo(search=sku, limit=50, offset=0)
    item = next((i for i in respuesta["items"] if i["sku"] == sku), None)
    if item is None:
        return None

    config = SkuSyncConfig.objects.filter(sku=sku).first()
    mapa = MLItemMap.objects.filter(sku=sku).first()
    return construir_fila_catalogo(item, config, mapa)


def obtener_porcentaje_ajuste():
    return ConfiguracionSyncML.obtener().porcentaje_ajuste_precio


def guardar_porcentaje_ajuste(porcentaje, usuario):
    """HU-CM2.1 — el % que se aplica sobre el precio SAP para publicar/actualizar en ML."""
    config = ConfiguracionSyncML.obtener()
    config.porcentaje_ajuste_precio = porcentaje
    config.updated_by = usuario
    config.save()
    return config


def calcular_precio_ml(precio_sap):
    """
    HU-CM2.1 — aplica el % global (ConfiguracionSyncML) sobre el precio SAP. ROUND_HALF_UP:
    mismo criterio de redondeo que usa Stock-Service sobre precios SAP, para no divergir.
    """
    porcentaje = obtener_porcentaje_ajuste()
    precio_ajustado = Decimal(precio_sap) * (Decimal("1") + porcentaje / Decimal("100"))
    return int(precio_ajustado.to_integral_value(rounding=ROUND_HALF_UP))


class TokenMLNoConfigurado(Exception):
    """No hay ningún MLToken guardado todavía — falta completar el login con Mercado Libre."""


def guardar_token_ml(datos_token):
    """
    HU-CM0.2 — persiste el resultado de ml_client.intercambiar_code_por_token/refrescar_token.
    Reemplaza la fila anterior entera: una sola fila siempre, una app = un seller.

    refresh_token con .get() y no ["..."]: si el authorization_code se pidió sin scope
    offline_access, ML devuelve un token "online" sin refresh_token y esto no debe explotar con
    KeyError (pasó en producción contra meli-dev el 2026-08-20) — mejor guardar lo que llegó,
    conservando el refresh_token anterior si había uno, y loguearlo para verlo en el log real.
    """
    anterior = MLToken.objects.first()
    refresh_token = datos_token.get("refresh_token")
    if not refresh_token:
        refresh_token = anterior.refresh_token if anterior else ""
        logger.warning(
            "ML no devolvió refresh_token (¿falta scope=offline_access?). Claves recibidas: %s",
            list(datos_token.keys()),
        )

    MLToken.objects.all().delete()
    return MLToken.objects.create(
        access_token=datos_token["access_token"],
        refresh_token=refresh_token,
        expires_at=timezone.now() + timedelta(seconds=datos_token["expires_in"]),
        ml_user_id=datos_token["user_id"],
    )


def hay_token_ml():
    return MLToken.objects.exists()


def obtener_token_valido():
    """
    Devuelve un access_token vigente, refrescando proactivamente si está por vencer dentro de
    _MARGEN_REFRESH. Refrescar ANTES de que ML lo rechace evita el escenario de dos requests
    concurrentes peleándose por el mismo refresh_token de un solo uso.
    """
    token = MLToken.objects.first()
    if token is None:
        raise TokenMLNoConfigurado("Todavía no se hizo login con Mercado Libre (HU-CM0.2).")

    if timezone.now() < token.expires_at - _MARGEN_REFRESH:
        return token.access_token

    datos = ml_client.refrescar_token(token.refresh_token)
    guardar_token_ml(datos)
    return datos["access_token"]
