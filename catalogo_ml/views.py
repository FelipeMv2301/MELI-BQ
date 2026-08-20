import math

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import render
from django.views.decorators.http import require_POST

from integraciones import stockservice_client

from . import services
from .models import SkuSyncConfig

_CAMPOS_VALIDOS = ("sync_stock", "sync_price")

_ACCIONES_MASIVAS = [
    ("Activar stock", "sync_stock", "true"),
    ("Desactivar stock", "sync_stock", "false"),
    ("Activar precio", "sync_price", "true"),
    ("Desactivar precio", "sync_price", "false"),
]


def _leer_pagina(datos):
    try:
        return max(int(datos.get("pagina", 1)), 1)
    except ValueError:
        return 1


def _armar_contexto_tabla(busqueda, pagina):
    offset = (pagina - 1) * services.PAGE_SIZE
    respuesta = stockservice_client.obtener_catalogo(
        search=busqueda or None, limit=services.PAGE_SIZE, offset=offset
    )

    items = respuesta["items"]
    skus = [item["sku"] for item in items]
    configs, mapas = services.obtener_config_y_mapa(skus)

    filas = [
        services.construir_fila_catalogo(item, configs.get(item["sku"]), mapas.get(item["sku"]))
        for item in items
    ]

    total = respuesta["total"]
    total_paginas = max(math.ceil(total / services.PAGE_SIZE), 1) if services.PAGE_SIZE else 1

    return {"filas": filas, "q": busqueda, "pagina": pagina, "total_paginas": total_paginas, "total": total}


@login_required
def index(request):
    """HU-CM1.1 — grilla paginada del catálogo (vía Stock-Service) con el estado de sync de cada SKU."""
    busqueda = request.GET.get("q", "").strip()
    pagina = _leer_pagina(request.GET)

    contexto = _armar_contexto_tabla(busqueda, pagina)

    es_peticion_htmx = request.headers.get("HX-Request") == "true"
    if es_peticion_htmx:
        return render(request, "catalogo_ml/_tabla.html", contexto)

    contexto["acciones_masivas"] = _ACCIONES_MASIVAS
    return render(request, "catalogo_ml/index.html", contexto)


@login_required
@require_POST
def toggle_sync(request, sku):
    """HU-CM1.2 — prende/apaga sync_stock o sync_price de UN producto, sin recargar la página."""
    campo = request.POST.get("campo")
    if campo not in _CAMPOS_VALIDOS:
        return HttpResponseBadRequest("campo debe ser sync_stock o sync_price")

    config, _creado = SkuSyncConfig.objects.get_or_create(sku=sku)
    setattr(config, campo, not getattr(config, campo))
    config.updated_by = request.user
    config.save()

    fila = services.construir_fila_por_sku(sku)
    if fila is None:
        return HttpResponseNotFound(f"SKU {sku} no encontrado en Stock-Service")
    return render(request, "catalogo_ml/_fila.html", {"fila": fila})


@login_required
@require_POST
def toggle_masivo(request):
    """HU-CM1.3 — aplica sync_stock/sync_price a todos los SKU seleccionados de una sola acción."""
    campo = request.POST.get("campo")
    valor = request.POST.get("valor") == "true"
    skus = request.POST.getlist("skus")

    if campo not in _CAMPOS_VALIDOS:
        return HttpResponseBadRequest("campo debe ser sync_stock o sync_price")
    if not skus:
        return HttpResponseBadRequest("no hay productos seleccionados")

    for sku in skus:
        config, _creado = SkuSyncConfig.objects.get_or_create(sku=sku)
        setattr(config, campo, valor)
        config.updated_by = request.user
        config.save()

    busqueda = request.POST.get("q", "").strip()
    pagina = _leer_pagina(request.POST)
    contexto = _armar_contexto_tabla(busqueda, pagina)
    return render(request, "catalogo_ml/_tabla.html", contexto)
