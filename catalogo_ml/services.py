"""
Reglas de negocio del Módulo 1 — la vista solo orquesta y presenta (mismo criterio arquitectónico
que gestorBQ: pedidos/services.py).
"""

from integraciones import stockservice_client

from .models import MLItemMap, SkuSyncConfig

PAGE_SIZE = 50

# Bodegas "web" (mismo criterio que WEB_WAREHOUSES de Stock-Service, sap_stock.py) — el stock que
# se muestra acá es el que hoy alimenta WooCommerce, no necesariamente el que se termine
# sincronizando a ML (esa regla de bodega por SKU es HU-CM3.2, todavía sin definir).
_BODEGAS_WEB = ("stock_01", "stock_11")


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
