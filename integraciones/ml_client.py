"""
Cliente de la API de Mercado Libre. Sin modelos propios (viven en catalogo_ml/facturacion_ml) —
este módulo solo habla HTTP, no guarda nada en la base.

Referencia completa: backlog_proyecto/Documentaciones/MercadoLibre/*.md
"""

from urllib.parse import urlencode

import requests
from django.conf import settings

BASE_URL = "https://api.mercadolibre.com"
AUTH_URL = "https://auth.mercadolibre.cl/authorization"


def construir_url_autorizacion(redirect_uri, state):
    """
    HU-CM0.2 — URL a la que se redirige el navegador para que el vendedor autorice la app.
    Dominio .cl fijo por ahora (ML_SITE_ID=MLC, proyecto de un solo país) — si algún día se
    soportan otros sites, esto necesita un mapeo site_id -> dominio de auth.

    scope=offline_access es necesario para que ML devuelva refresh_token junto al access_token —
    sin él, la app queda "online" (solo access_token, sin forma de renovarlo) y
    intercambiar_code_por_token revienta con KeyError('refresh_token') — confirmado en producción
    contra meli-dev el 2026-08-20.
    """
    params = {
        "response_type": "code",
        "client_id": settings.ML_APP_ID,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": "offline_access read write",
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def intercambiar_code_por_token(authorization_code, redirect_uri, code_verifier=None):
    """HU-CM0.2 — canjea el authorization_code por access_token/refresh_token. Ver autenticacion.md."""
    datos = {
        "grant_type": "authorization_code",
        "client_id": settings.ML_APP_ID,
        "client_secret": settings.ML_APP_SECRET,
        "code": authorization_code,
        "redirect_uri": redirect_uri,
    }
    if code_verifier:
        datos["code_verifier"] = code_verifier

    respuesta = requests.post(f"{BASE_URL}/oauth/token", data=datos, timeout=15)
    respuesta.raise_for_status()
    return respuesta.json()


def refrescar_token(refresh_token):
    """HU-CM0.2 — el refresh_token es de un solo uso, persistir el nuevo en cada llamada."""
    datos = {
        "grant_type": "refresh_token",
        "client_id": settings.ML_APP_ID,
        "client_secret": settings.ML_APP_SECRET,
        "refresh_token": refresh_token,
    }
    respuesta = requests.post(f"{BASE_URL}/oauth/token", data=datos, timeout=15)
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_usuario(access_token, user_id):
    """HU-CM0.3 — trae los tags del seller (user_product_seller, warehouse_management, ...)."""
    respuesta = requests.get(
        f"{BASE_URL}/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    respuesta.raise_for_status()
    return respuesta.json()


def buscar_item_por_sku(access_token, seller_id, sku):
    """
    HU-CM2.2 — antes de publicar, busca si el SKU ya está en la cuenta: por `sku=` (busca sobre
    `seller_custom_field`, campo legacy) o por `seller_sku=` (atributo `SELLER_SKU`, forma actual)
    — un ítem viejo puede estar en cualquiera de los dos según cuándo se publicó. Devuelve el
    primer item_id que aparezca, o None si no está en ninguno.

    El parámetro del campo legacy es `sku=`, NO `seller_custom_field=` — usar el nombre del campo
    como parámetro (como se probó al principio) devuelve la lista general de ítems del vendedor
    SIN FILTRAR, no vacía. Confirmado contra la cuenta real de bioquimica.cl el 2026-08-21: con
    `seller_custom_field=` devolvía 50 ítems sin relación con el SKU buscado (ver KeyError/vínculo
    incorrecto detectado y corregido esa fecha); con `sku=` filtra de verdad.
    """
    for parametro in ("sku", "seller_sku"):
        respuesta = requests.get(
            f"{BASE_URL}/users/{seller_id}/items/search",
            headers={"Authorization": f"Bearer {access_token}"},
            params={parametro: sku},
            timeout=15,
        )
        respuesta.raise_for_status()
        resultados = respuesta.json().get("results", [])
        if resultados:
            return resultados[0]
    return None


def publicar_item(access_token, payload):
    """HU-CM2.2 — POST /items."""
    raise NotImplementedError


def actualizar_item(access_token, item_id, payload):
    """HU-CM3.2/3.3 — PUT /items/$ITEM_ID (stock/precio, modelo legacy)."""
    raise NotImplementedError


def actualizar_descripcion(access_token, item_id, plain_text, existe):
    """HU-CM2.4 — POST (si no existe) o PUT ?api_version=2 (si ya existe) /items/$ITEM_ID/description."""
    raise NotImplementedError


def obtener_orden(access_token, order_id):
    """HU-FM1.1 — GET /orders/$ORDER_ID."""
    raise NotImplementedError


def obtener_billing_info(access_token, site_id, billing_info_id):
    """HU-FM2.1 — GET /orders/billing-info/$SITE_ID/$BILLING_INFO_ID."""
    raise NotImplementedError
