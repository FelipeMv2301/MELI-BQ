"""
Cliente de solo lectura de la API REST de Stock-Service (catálogo, stock por bodega, precio SAP
ya calculado). SPK-MELI-5 resuelto 2026-08-20: API REST, mismo patrón que ya usa BQ-Integraciones
en producción (app/services/stockservice/client.py, decisión D2 de su plan.md) — sin espejo propio
del catálogo en MELI-BQ.

Este proyecto NUNCA escribe en Stock-Service — es la fuente de verdad de SAP, no al revés.
"""

import requests
from django.conf import settings


def _base_url():
    return settings.STOCKSERVICE_BASE_URL.rstrip("/")


def _headers():
    return {"X-API-Key": settings.STOCKSERVICE_API_KEY}


def obtener_producto(sku):
    """GET /api/v1/stock/products/{sku} — trazabilidad completa de un SKU (sap/woo/recent_logs)."""
    respuesta = requests.get(
        f"{_base_url()}/api/v1/stock/products/{sku}",
        headers=_headers(),
        timeout=15,
    )
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_catalogo(search=None, limit=0, offset=0):
    """
    GET /api/v1/stock/catalog — catálogo paginado para la grilla de selección (HU-CM1.1).
    El campo price viene NETO en CLP (sin IVA), tal como lo calcula Stock-Service desde SAP Lista 1
    — la regla de precio (HU-CM2.1) es responsabilidad de este proyecto, no de Stock-Service.
    """
    params = {"limit": limit, "offset": offset}
    if search:
        params["search"] = search

    respuesta = requests.get(
        f"{_base_url()}/api/v1/stock/catalog",
        headers=_headers(),
        params=params,
        timeout=15,
    )
    respuesta.raise_for_status()
    return respuesta.json()
