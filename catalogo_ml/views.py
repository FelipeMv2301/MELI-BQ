import logging
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

logger = logging.getLogger(__name__)

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


def _leer_filtros(datos):
    return {
        "sincronizado": datos.get("sincronizado") == "1",
        "solo_sync_stock": datos.get("solo_sync_stock") == "1",
        "solo_sync_precio": datos.get("solo_sync_precio") == "1",
    }


def _items_filtrados_localmente(skus_filtrados, busqueda):
    """
    Cuando hay algún filtro de sync activo, el universo lo definen los SKUs locales (chico), no la
    paginación de Stock-Service — se trae el detalle de cada uno por separado y, si además hay
    texto de búsqueda, se filtra en memoria por sku/nombre (ambos ya disponibles en cada item).
    N llamadas a Stock-Service, una por SKU — aceptable mientras estos conjuntos se mantengan
    chicos (hoy, muy por debajo del catálogo completo); revisar si esto crece mucho más adelante.
    """
    items = []
    for sku in sorted(skus_filtrados):
        item = services.obtener_item_stockservice_por_sku(sku)
        if item is None:
            continue
        if busqueda and busqueda.lower() not in item["sku"].lower() and busqueda.lower() not in (item.get("name") or "").lower():
            continue
        items.append(item)
    return items


def _armar_contexto_tabla(busqueda, pagina, filtros):
    skus_filtrados = services.skus_que_cumplen_filtro(**filtros)

    if skus_filtrados is None:
        offset = (pagina - 1) * services.PAGE_SIZE
        respuesta = stockservice_client.obtener_catalogo(
            search=busqueda or None, limit=services.PAGE_SIZE, offset=offset
        )
        items = respuesta["items"]
        total = respuesta["total"]
    else:
        todos = _items_filtrados_localmente(skus_filtrados, busqueda)
        total = len(todos)
        inicio = (pagina - 1) * services.PAGE_SIZE
        items = todos[inicio : inicio + services.PAGE_SIZE]

    skus = [item["sku"] for item in items]
    configs, mapas = services.obtener_config_y_mapa(skus)

    filas = [
        services.construir_fila_catalogo(item, configs.get(item["sku"]), mapas.get(item["sku"]))
        for item in items
    ]

    total_paginas = max(math.ceil(total / services.PAGE_SIZE), 1) if services.PAGE_SIZE else 1

    return {
        "filas": filas, "q": busqueda, "pagina": pagina, "total_paginas": total_paginas, "total": total,
        **filtros,
    }


@login_required
def index(request):
    """HU-CM1.1 — grilla paginada del catálogo (vía Stock-Service) con el estado de sync de cada SKU."""
    busqueda = request.GET.get("q", "").strip()
    pagina = _leer_pagina(request.GET)
    filtros = _leer_filtros(request.GET)

    contexto = _armar_contexto_tabla(busqueda, pagina, filtros)

    es_peticion_htmx = request.headers.get("HX-Request") == "true"
    if es_peticion_htmx:
        return render(request, "catalogo_ml/_tabla.html", contexto)

    contexto["acciones_masivas"] = _ACCIONES_MASIVAS
    contexto["hay_token_ml"] = services.hay_token_ml()
    contexto["porcentaje_ajuste"] = services.obtener_porcentaje_ajuste()
    if services.hay_perfil_seller():
        contexto["modelo_item"] = services.descripcion_modelo_item()
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

    try:
        services.actualizar_perfil_seller()
    except Exception:
        # Best-effort (HU-CM0.3): un fallo acá no debe tumbar un login que sí funcionó. El
        # próximo login (o un reintento manual) lo vuelve a intentar.
        logger.warning("No se pudo detectar el modelo de item del seller tras el login.", exc_info=True)

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
    filtros = _leer_filtros(request.POST)
    contexto = _armar_contexto_tabla(busqueda, pagina, filtros)
    return render(request, "catalogo_ml/_tabla.html", contexto)


def _leer_decimal_opcional(valor_crudo):
    """
    Devuelve (decimal_o_None, error). Vacío es válido y significa "sin valor" (usar el nivel de
    arriba) — no es lo mismo que un número mal escrito.
    """
    valor_crudo = (valor_crudo or "").strip()
    if not valor_crudo:
        return None, None
    try:
        return Decimal(valor_crudo), None
    except (InvalidOperation, TypeError):
        return None, f"'{valor_crudo}' no es un número válido."


@login_required
def detalle(request, sku):
    """HU-CM1.6 — pantalla individual del producto: foto, precios, sync y vínculos con ML."""
    detalle_producto = services.armar_detalle_producto(sku)
    if detalle_producto is None:
        return HttpResponseNotFound(f"SKU {sku} no encontrado en Stock-Service")

    contexto = {"p": detalle_producto, "hay_token_ml": services.hay_token_ml()}

    texto_busqueda = request.GET.get("buscar_ml", "").strip()
    if texto_busqueda:
        contexto["texto_busqueda"] = texto_busqueda
        try:
            contexto["candidatos"] = services.buscar_candidatos_para_vincular(texto_busqueda)
        except services.TokenMLNoConfigurado:
            messages.error(request, "Conectá con Mercado Libre antes de buscar ítems para vincular.")
        except Exception as exc:
            messages.error(request, f"No se pudo buscar en Mercado Libre: {exc}")

    return render(request, "catalogo_ml/detalle.html", contexto)


@login_required
@require_POST
def guardar_precio_producto(request, sku):
    """HU-CM1.7 — guarda el % propio y/o el precio manual del producto."""
    porcentaje, error_porcentaje = _leer_decimal_opcional(request.POST.get("porcentaje_propio"))
    precio, error_precio = _leer_decimal_opcional(request.POST.get("precio_manual"))

    error = error_porcentaje or error_precio
    if error:
        messages.error(request, error)
        return redirect("catalogo_ml:detalle", sku=sku)

    if porcentaje is not None and porcentaje <= -100:
        messages.error(request, "El porcentaje no puede ser -100% o menos.")
        return redirect("catalogo_ml:detalle", sku=sku)

    services.guardar_precio_producto(sku, porcentaje, precio, request.user)
    messages.success(request, "Precio del producto actualizado.")
    return redirect("catalogo_ml:detalle", sku=sku)


@login_required
@require_POST
def vincular_a_mano(request, sku):
    """HU-CM2.6 — vincula el ítem de ML elegido a mano, con su factor de unidades."""
    ml_item_id = request.POST.get("ml_item_id", "").strip()
    if not ml_item_id:
        return HttpResponseBadRequest("falta ml_item_id")

    try:
        unidades = int(request.POST.get("unidades_por_item", 1))
    except ValueError:
        messages.error(request, "Las unidades por ítem deben ser un número entero.")
        return redirect("catalogo_ml:detalle", sku=sku)

    if unidades < 1:
        messages.error(request, "Las unidades por ítem deben ser 1 o más.")
        return redirect("catalogo_ml:detalle", sku=sku)

    services.vincular_a_mano(sku, ml_item_id, unidades)
    messages.success(request, f"Ítem {ml_item_id} vinculado a {sku}.")
    return redirect("catalogo_ml:detalle", sku=sku)


@login_required
@require_POST
def guardar_vinculo(request, vinculo_id):
    """HU-CM1.7/2.7 — edita unidades y precio manual de un vínculo existente."""
    sku = request.POST.get("sku", "")
    precio, error = _leer_decimal_opcional(request.POST.get("precio_manual"))
    if error:
        messages.error(request, error)
        return redirect("catalogo_ml:detalle", sku=sku)

    try:
        unidades = int(request.POST.get("unidades_por_item", 1))
    except ValueError:
        messages.error(request, "Las unidades por ítem deben ser un número entero.")
        return redirect("catalogo_ml:detalle", sku=sku)

    if unidades < 1:
        messages.error(request, "Las unidades por ítem deben ser 1 o más.")
        return redirect("catalogo_ml:detalle", sku=sku)

    if services.guardar_vinculo(vinculo_id, unidades, precio) is None:
        return HttpResponseNotFound("vínculo no encontrado")

    messages.success(request, "Vínculo actualizado.")
    return redirect("catalogo_ml:detalle", sku=sku)


@login_required
@require_POST
def desvincular(request, vinculo_id):
    """HU-CM2.6 — borra el vínculo. No toca nada en ML, solo deja de sincronizarse desde acá."""
    sku = services.desvincular(vinculo_id)
    if sku is None:
        return HttpResponseNotFound("vínculo no encontrado")

    messages.success(request, "Vínculo eliminado (no se modificó nada en Mercado Libre).")
    return redirect("catalogo_ml:detalle", sku=sku)


@login_required
@require_POST
def aplicar_porcentaje_masivo(request):
    """HU-CM1.8 — fija el mismo % propio a todos los SKU seleccionados."""
    skus = request.POST.getlist("skus")
    if not skus:
        return HttpResponseBadRequest("no hay productos seleccionados")

    porcentaje, error = _leer_decimal_opcional(request.POST.get("porcentaje_masivo"))
    if error:
        messages.error(request, error)
        return redirect("catalogo_ml:index")
    if porcentaje is None:
        messages.error(request, "Escribí un porcentaje antes de aplicarlo.")
        return redirect("catalogo_ml:index")
    if porcentaje <= -100:
        messages.error(request, "El porcentaje no puede ser -100% o menos.")
        return redirect("catalogo_ml:index")

    cantidad = services.aplicar_porcentaje_masivo(skus, porcentaje, request.user)
    messages.success(request, f"{porcentaje}% aplicado a {cantidad} producto{'s' if cantidad != 1 else ''}.")

    busqueda = request.POST.get("q", "").strip()
    pagina = _leer_pagina(request.POST)
    filtros = _leer_filtros(request.POST)
    contexto = _armar_contexto_tabla(busqueda, pagina, filtros)
    return render(request, "catalogo_ml/_tabla.html", contexto)


@login_required
@require_POST
def vincular_masivo(request):
    """
    HU-CM2.2 (parte 1) — busca los SKU seleccionados en la cuenta real de ML y vincula
    (`MLItemMap`) los que ya estén publicados. Los que no aparezcan quedan sin tocar: publicar uno
    nuevo necesita category_id resuelto (HU-CM2.3), todavía sin construir.
    """
    skus = request.POST.getlist("skus")
    if not skus:
        return HttpResponseBadRequest("no hay productos seleccionados")

    try:
        encontrados, no_encontrados = services.vincular_masivo(skus)
    except services.TokenMLNoConfigurado:
        messages.error(request, "Conectá con Mercado Libre antes de sincronizar.")
        return redirect("catalogo_ml:index")
    except Exception as exc:
        messages.error(request, f"No se pudo consultar Mercado Libre: {exc}")
        return redirect("catalogo_ml:index")

    if encontrados:
        messages.success(
            request,
            f"{len(encontrados)} producto{'s' if len(encontrados) != 1 else ''} vinculado{'s' if len(encontrados) != 1 else ''} con un ítem ya existente en Mercado Libre.",
        )
    if no_encontrados:
        messages.warning(
            request,
            f"{len(no_encontrados)} no se encontraron en Mercado Libre — todavía no se pueden "
            "publicar (falta definir categoría, HU-CM2.3).",
        )

    busqueda = request.POST.get("q", "").strip()
    pagina = _leer_pagina(request.POST)
    filtros = _leer_filtros(request.POST)
    contexto = _armar_contexto_tabla(busqueda, pagina, filtros)
    return render(request, "catalogo_ml/_tabla.html", contexto)
