"""
Cliente de la API de Mercado Libre. Sin modelos propios (viven en catalogo_ml/facturacion_ml) —
este módulo solo habla HTTP.

Referencia completa: backlog_proyecto/Documentaciones/MercadoLibre/*.md

Pendiente de credenciales reales — SPK-MELI-1 (ver backlog_proyecto/plan-integracion-mercadolibre.md).
Todas las funciones son stubs hasta que la app de ML exista y HU-CM0.2 se implemente.
"""

from django.conf import settings

BASE_URL = "https://api.mercadolibre.com"


def obtener_access_token(authorization_code, code_verifier=None):
    """HU-CM0.2 — canjea el authorization_code por access_token/refresh_token. Ver autenticacion.md."""
    raise NotImplementedError("Pendiente SPK-MELI-1 (credenciales de la app ML)")


def refrescar_token(refresh_token):
    """HU-CM0.2 — el refresh_token es de un solo uso, persistir el nuevo en cada llamada."""
    raise NotImplementedError("Pendiente SPK-MELI-1 (credenciales de la app ML)")


def obtener_usuario(access_token, user_id):
    """HU-CM0.3 — trae los tags del seller (user_product_seller, warehouse_management, ...)."""
    raise NotImplementedError


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
