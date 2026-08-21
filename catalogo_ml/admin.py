from django.contrib import admin

from .models import ConfiguracionSyncML, MLItemMap, PerfilSellerML, SkuSyncConfig


@admin.register(SkuSyncConfig)
class SkuSyncConfigAdmin(admin.ModelAdmin):
    list_display = (
        "sku", "sync_stock", "sync_price", "enabled",
        "porcentaje_ajuste_propio", "precio_manual", "updated_at", "updated_by",
    )
    list_editable = ("sync_stock", "sync_price", "enabled", "porcentaje_ajuste_propio", "precio_manual")
    search_fields = ("sku",)
    list_filter = ("enabled", "sync_stock", "sync_price")

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MLItemMap)
class MLItemMapAdmin(admin.ModelAdmin):
    list_display = (
        "sku", "ml_item_id", "unidades_por_item", "precio_manual",
        "ml_site_id", "status", "last_checked_at",
    )
    list_editable = ("unidades_por_item", "precio_manual")
    search_fields = ("sku", "ml_item_id")
    list_filter = ("status", "ml_site_id")


@admin.register(ConfiguracionSyncML)
class ConfiguracionSyncMLAdmin(admin.ModelAdmin):
    list_display = ("porcentaje_ajuste_precio", "updated_at", "updated_by")

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PerfilSellerML)
class PerfilSellerMLAdmin(admin.ModelAdmin):
    list_display = ("tags", "updated_at")
