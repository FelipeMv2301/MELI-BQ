import math
import secrets
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from integraciones import ml_client, stockservice_client

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
    contexto["hay_token_ml"] = services.hay_token_ml()
    contexto["porcentaje_ajuste"] = services.obtener_porcentaje_ajuste()
    return render(request, "catalogo_ml/index.html", contexto)


@login_required
def ml_login(request):
    """HU-CM0.2 — arranca el flujo OAuth: redirige al vendedor a la pantalla de autorización de ML."""
    state = secrets.token_urlsafe(24)
    request.session["ml_oauth_state"] = state
    redirect_uri = request.build_absolute_uri(reverse("catalogo_ml:ml_callback"))
    return redirect(ml_client.construir_url_autorizacion(redirect_uri, state))


@login_required
def ml_callback(request):
    """HU-CM0.2 — recibe el code de ML, lo canjea por access_token/refresh_token y los guarda."""
    error = request.GET.get("error")
    if error:
        messages.error(request, f"Mercado Libre rechazó la autorización: {error}")
        return redirect("catalogo_ml:index")

    state_recibido = request.GET.get("state")
    state_esperado = request.session.pop("ml_oauth_state", None)
    if not state_esperado or state_recibido != state_esperado:
        messages.error(
            request,
            "El login con Mercado Libre no se pudo validar (state inválido) — intentá de nuevo.",
        )
        return redirect("catalogo_ml:index")

    code = request.GET.get("code")
    if not code:
        messages.error(request, "Mercado Libre no envió el código de autorización.")
        return redirect("catalogo_ml:index")

    redirect_uri = request.build_absolute_uri(reverse("catalogo_ml:ml_callback"))
    try:
        datos = ml_client.intercambiar_code_por_token(code, redirect_uri)
    except Exception as exc:
        messages.error(request, f"No se pudo canjear el código por un token: {exc}")
        return redirect("catalogo_ml:index")

    services.guardar_token_ml(datos)
    messages.success(request, "Cuenta de Mercado Libre conectada correctamente.")
    return redirect("catalogo_ml:index")


@login_required
@require_POST
def actualizar_porcentaje_ajuste(request):
    """HU-CM2.1 — guarda el % global de ajuste de precio a aplicar al publicar/actualizar en ML."""
    valor_crudo = request.POST.get("porcentaje", "").strip()
    try:
        porcentaje = Decimal(valor_crudo)
    except (InvalidOperation, TypeError):
        messages.error(request, f"'{valor_crudo}' no es un porcentaje válido.")
        return redirect("catalogo_ml:index")

    if porcentaje <= -100:
        messages.error(
            request,
            "El porcentaje no puede ser -100% o menos (dejaría el precio publicado en cero o negativo).",
        )
        return redirect("catalogo_ml:index")

    config = services.guardar_porcentaje_ajuste(porcentaje, request.user)
    messages.success(request, f"Porcentaje de ajuste actualizado a {config.porcentaje_ajuste_precio}%.")
    return redirect("catalogo_ml:index")


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
