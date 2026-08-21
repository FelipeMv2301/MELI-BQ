"""
Modelos del Módulo 1 — selección de sync de catálogo hacia Mercado Libre.

SkuSyncConfig: lo que el usuario elige desde la UI (persistente, ver HU-CM1.2/1.3).
MLItemMap: el resultado — a qué item_id de ML quedó publicado cada SKU (ver HU-CM2.2).

Ver backlog_proyecto/plan-integracion-mercadolibre.md sección 6 (modelo de datos borrador).
"""

from django.conf import settings
from django.db import models


class SkuSyncConfig(models.Model):
    """
    Una fila por SKU seleccionado desde la grilla. enabled=False excluye el SKU del plan sin
    perder la configuración de sync_stock/sync_price (para poder reactivarlo tal cual estaba).
    """

    sku = models.CharField(max_length=50, unique=True, db_index=True)

    sync_stock = models.BooleanField(default=False)
    sync_price = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sku_sync_configs_editados",
    )

    class Meta:
        verbose_name = "Configuración de sync por SKU"
        verbose_name_plural = "Configuraciones de sync por SKU"

    def __str__(self):
        return self.sku

    @property
    def participa_del_plan(self):
        """True si corresponde evaluarlo en plan_sync_ml — excluido si está deshabilitado o si
        no tiene NADA activado (mismo criterio que R7 de Stock-Service: sin flags, sin log)."""
        return self.enabled and (self.sync_stock or self.sync_price)


class MLItemMap(models.Model):
    """Un SKU publicado en Mercado Libre — de acá en adelante ese SKU se actualiza, no se publica de nuevo."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Activo"
        PAUSED = "paused", "Pausado"
        CLOSED = "closed", "Cerrado"
        UNDER_REVIEW = "under_review", "En revisión"

    sku = models.CharField(max_length=50, unique=True, db_index=True)
    ml_item_id = models.CharField(max_length=30, unique=True)
    ml_site_id = models.CharField(max_length=10, default="MLC")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    last_checked_at = models.DateTimeField(null=True, blank=True)

    # Último precio que efectivamente se empujó a ML (HU-CM3.3) — no es una consulta en vivo a la
    # API por fila (2000 SKUs por página harían inviable la grilla), es el último valor conocido.
    ultimo_precio_sincronizado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Item publicado en Mercado Libre"
        verbose_name_plural = "Items publicados en Mercado Libre"

    def __str__(self):
        return f"{self.sku} -> {self.ml_item_id}"


class ConfiguracionSyncML(models.Model):
    """
    Config global del Módulo 1 (HU-CM2.1, SPK-MELI-7 resuelto: un % único para todo el catálogo,
    editable desde la propia UI). Fila única — `obtener()` siempre trabaja sobre pk=1.
    """

    porcentaje_ajuste_precio = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="configuraciones_sync_ml_editadas",
    )

    class Meta:
        verbose_name = "Configuración de sync de Mercado Libre"
        verbose_name_plural = "Configuración de sync de Mercado Libre"

    def __str__(self):
        return f"Ajuste de precio: {self.porcentaje_ajuste_precio}%"

    @classmethod
    def obtener(cls):
        return cls.objects.get_or_create(pk=1)[0]


class PerfilSellerML(models.Model):
    """
    HU-CM0.3 — tags reales del seller en Mercado Libre (SPK-MELI-2), consultados una vez tras el
    login (ver `services.actualizar_perfil_seller`, llamado desde `views.ml_callback`). Condicionan
    qué endpoint de stock usar más adelante (HU-CM3.2): `PUT /items/$ITEM_ID` (legacy o User
    Products sin multiorigen) vs `PUT /user-products/.../stock` (multiorigen activo).
    Fila única — `obtener()` siempre trabaja sobre pk=1.
    """

    tags = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil del seller en Mercado Libre"
        verbose_name_plural = "Perfil del seller en Mercado Libre"

    def __str__(self):
        return f"Tags: {', '.join(self.tags) or '(sin datos)'}"

    @classmethod
    def obtener(cls):
        return cls.objects.get_or_create(pk=1)[0]

    @property
    def usa_user_products(self):
        return "user_product_seller" in self.tags

    @property
    def tiene_multiorigen(self):
        return "warehouse_management" in self.tags and "multiwarehouse" in self.tags


class MLToken(models.Model):
    """
    Token OAuth2 de la app de Mercado Libre (HU-CM0.2) — una sola fila, siempre la más reciente
    (una app, un seller, no hace falta múltiples filas). Se reemplaza entera en cada
    login/refresh, nunca se edita a mano.
    """

    access_token = models.CharField(max_length=200)
    refresh_token = models.CharField(max_length=200)
    expires_at = models.DateTimeField()
    ml_user_id = models.BigIntegerField()

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Token de Mercado Libre"
        verbose_name_plural = "Token de Mercado Libre"

    def __str__(self):
        return f"ML user {self.ml_user_id} (actualizado {self.updated_at:%Y-%m-%d %H:%M})"
