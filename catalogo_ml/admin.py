from django.contrib import admin

from .models import MLItemMap, SkuSyncConfig


@admin.register(SkuSyncConfig)
class SkuSyncConfigAdmin(admin.ModelAdmin):
    list_display = ("sku", "sync_stock", "sync_price", "enabled", "updated_at", "updated_by")
    list_editable = ("sync_stock", "sync_price", "enabled")
    search_fields = ("sku",)
    list_filter = ("enabled", "sync_stock", "sync_price")

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MLItemMap)
class MLItemMapAdmin(admin.ModelAdmin):
    list_display = ("sku", "ml_item_id", "ml_site_id", "status", "last_checked_at")
    search_fields = ("sku", "ml_item_id")
    list_filter = ("status", "ml_site_id")
