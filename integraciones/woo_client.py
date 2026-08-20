"""
Cliente de solo lectura de la API REST de WooCommerce — fotos y descripción de producto por SKU.
Credenciales ya disponibles en .env (WOO_URL/WOO_KEY/WOO_SECRET), confirmadas contra un producto
real el 2026-08-20 (ver backlog_proyecto/Documentaciones/MercadoLibre/descripcion-de-productos.md).

Este proyecto NUNCA escribe en WooCommerce — esa responsabilidad es de Stock-Service.
"""

import requests
from django.conf import settings


def _base_url():
    return settings.WOO_URL.rstrip("/")


def obtener_producto_por_sku(sku):
    """
    GET /wp-json/wc/v3/products?sku=$SKU — devuelve el producto completo de WooCommerce
    (incluye description, short_description, images[], sku) o None si no existe.
    """
    respuesta = requests.get(
        f"{_base_url()}/wp-json/wc/v3/products",
        params={"sku": sku},
        auth=(settings.WOO_KEY, settings.WOO_SECRET),
        timeout=30,
    )
    respuesta.raise_for_status()
    resultados = respuesta.json()
    return resultados[0] if resultados else None


def obtener_fotos(sku):
    """HU-CM2.2 — lista de URLs (images[].src) listas para pasar a ML como pictures[].source."""
    producto = obtener_producto_por_sku(sku)
    if not producto:
        return []
    return [imagen["src"] for imagen in producto.get("images", [])]


def obtener_descripcion_html(sku):
    """HU-CM2.4 — (description, short_description) crudos, en HTML, tal como los guarda WooCommerce."""
    producto = obtener_producto_por_sku(sku)
    if not producto:
        return "", ""
    return producto.get("description", ""), producto.get("short_description", "")
