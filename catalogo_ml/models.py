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

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Item publicado en Mercado Libre"
        verbose_name_plural = "Items publicados en Mercado Libre"

    def __str__(self):
        return f"{self.sku} -> {self.ml_item_id}"
