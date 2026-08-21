import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from utils import limpiar_descripcion_html

from . import services
from .models import ConfiguracionSyncML, MLItemMap, MLToken, PerfilSellerML, SkuSyncConfig


class LimpiarDescripcionHtmlTests(SimpleTestCase):
    """
    HU-CM2.4 — contra el payload real de WooCommerce dejado en la raíz del proyecto
    (ejemplo-payload-woocommerce.json, SKU ML000111), no un HTML inventado a mano.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ruta = settings.BASE_DIR / "ejemplo-payload-web-antigua.json"
        cls.producto = json.loads(ruta.read_text(encoding="utf-8"))

    def test_no_deja_ningun_tag_html(self):
        resultado = limpiar_descripcion_html(self.producto["description"])
        self.assertNotIn("<", resultado)
        self.assertNotIn(">", resultado)

    def test_aplana_tabla_de_specs_como_lineas_legibles(self):
        resultado = limpiar_descripcion_html(self.producto["description"])
        self.assertIn("Largo: 180 mm", resultado)
        self.assertIn("Diametro: 18 mm", resultado)

    def test_conserva_texto_del_link_y_descarta_la_url(self):
        resultado = limpiar_descripcion_html(self.producto["description"])
        self.assertIn("Thermal expansion test report.pdf", resultado)
        self.assertNotIn("https://", resultado)
        self.assertNotIn("jumpseller", resultado.lower())

    def test_items_de_lista_quedan_con_guion(self):
        resultado = limpiar_descripcion_html(self.producto["description"])
        self.assertIn("- Realización de reacciones químicas a pequeña escala", resultado)

    def test_decodifica_entidades_html(self):
        resultado = limpiar_descripcion_html(self.producto["short_description"])
        # short_description trae &#8211; (en dash) en el payload real — no debe quedar la entidad cruda.
        self.assertNotIn("&#8211;", resultado)
        self.assertIn("–", resultado)

    def test_string_vacio_no_rompe(self):
        self.assertEqual(limpiar_descripcion_html(""), "")
        self.assertEqual(limpiar_descripcion_html(None), "")


class SkuSyncConfigTests(TestCase):
    def test_sku_es_unico(self):
        SkuSyncConfig.objects.create(sku="ML000111")
        with self.assertRaises(IntegrityError):
            SkuSyncConfig.objects.create(sku="ML000111")

    def test_valores_default(self):
        config = SkuSyncConfig.objects.create(sku="ML000111")
        self.assertFalse(config.sync_stock)
        self.assertFalse(config.sync_price)
        self.assertTrue(config.enabled)

    def test_participa_del_plan_requiere_algun_flag_activo(self):
        config = SkuSyncConfig.objects.create(sku="ML000111")
        self.assertFalse(config.participa_del_plan)  # ambos flags en False

        config.sync_stock = True
        self.assertTrue(config.participa_del_plan)

    def test_participa_del_plan_false_si_esta_deshabilitado(self):
        config = SkuSyncConfig.objects.create(sku="ML000111", sync_stock=True, enabled=False)
        self.assertFalse(config.participa_del_plan)

    def test_guarda_quien_lo_edito_por_admin(self):
        usuario = get_user_model().objects.create(email="test@bioquimica.cl")
        config = SkuSyncConfig.objects.create(sku="ML000111", updated_by=usuario)
        self.assertEqual(config.updated_by.email, "test@bioquimica.cl")

    def test_str_es_el_sku(self):
        config = SkuSyncConfig.objects.create(sku="ML000111")
        self.assertEqual(str(config), "ML000111")


class MLItemMapTests(TestCase):
    def test_el_mismo_item_de_ml_no_puede_vincularse_dos_veces(self):
        MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC123456789")
        with self.assertRaises(IntegrityError):
            MLItemMap.objects.create(sku="ML000222", ml_item_id="MLC123456789")

    def test_un_sku_puede_tener_varios_items_de_ml(self):
        """HU-CM2.7 — unidad suelta + pack de 100 del mismo SKU."""
        MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC111", unidades_por_item=1)
        MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC222", unidades_por_item=100)

        self.assertEqual(MLItemMap.objects.filter(sku="ML000111").count(), 2)

    def test_unidades_por_item_default_es_1(self):
        item = MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC123456789")
        self.assertEqual(item.unidades_por_item, 1)

    def test_status_default_es_active(self):
        item = MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC123456789")
        self.assertEqual(item.status, MLItemMap.Status.ACTIVE)

    def test_str_incluye_sku_y_item_id(self):
        item = MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC123456789")
        self.assertEqual(str(item), "ML000111 -> MLC123456789")

    def test_str_de_un_pack_muestra_las_unidades(self):
        item = MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC999", unidades_por_item=100)
        self.assertEqual(str(item), "ML000111 x100 -> MLC999")


class ConstruirFilaCatalogoTests(TestCase):
    """HU-CM1.1 — la función pura que arma cada fila de la grilla, sin pegarle a ninguna API."""

    def _item_stockservice(self, **overrides):
        base = {
            "sku": "ML000111",
            "name": "Tubo de Ensayo - Borosilicato - 18x180mm",
            "price": 1234,
            "stock_01": 5,
            "stock_11": 3,
            "stock_15": 100,  # bodega de tienda física — no debe contar en stock_web
        }
        base.update(overrides)
        return base

    def test_sin_config_ni_vinculos_queda_no_sincronizado(self):
        fila = services.construir_fila_catalogo(self._item_stockservice(), None, [])
        self.assertFalse(fila["sync_stock"])
        self.assertFalse(fila["sync_price"])
        self.assertEqual(fila["estado"], "No sincronizado")
        self.assertIsNone(fila["ml_item_id"])
        self.assertEqual(fila["cantidad_vinculos"], 0)

    def test_precio_ml_es_el_que_se_publicaria_aunque_no_este_vinculado(self):
        """Sin % configurado el precio ML es igual al neto de SAP — se ve antes de publicar nada."""
        fila = services.construir_fila_catalogo(self._item_stockservice(), None, [])
        self.assertEqual(fila["precio_ml"], 1234)

    def test_precio_ml_de_un_pack_multiplica_por_las_unidades(self):
        vinculo = MLItemMap(sku="ML000111", ml_item_id="MLC999", unidades_por_item=100)
        fila = services.construir_fila_catalogo(self._item_stockservice(), None, [vinculo])
        self.assertEqual(fila["precio_ml"], 123400)

    def test_con_varios_vinculos_no_muestra_un_precio_unico(self):
        vinculos = [
            MLItemMap(sku="ML000111", ml_item_id="MLC111", unidades_por_item=1),
            MLItemMap(sku="ML000111", ml_item_id="MLC222", unidades_por_item=100),
        ]
        fila = services.construir_fila_catalogo(self._item_stockservice(), None, vinculos)

        self.assertEqual(fila["estado"], "2 ítems vinculados")
        self.assertIsNone(fila["precio_ml"])
        self.assertIsNone(fila["ml_item_id"])
        self.assertEqual(fila["cantidad_vinculos"], 2)

    def test_stock_web_solo_suma_bodegas_01_y_11(self):
        fila = services.construir_fila_catalogo(self._item_stockservice(), None, [])
        self.assertEqual(fila["stock_web"], 8)  # 5 + 3, sin contar stock_15

    def test_con_config_refleja_los_flags_activos(self):
        config = SkuSyncConfig(sku="ML000111", sync_stock=True, sync_price=False)
        fila = services.construir_fila_catalogo(self._item_stockservice(), config, [])
        self.assertTrue(fila["sync_stock"])
        self.assertFalse(fila["sync_price"])

    def test_con_un_vinculo_muestra_el_estado_publicado(self):
        vinculo = MLItemMap(sku="ML000111", ml_item_id="MLC999", status=MLItemMap.Status.PAUSED)
        fila = services.construir_fila_catalogo(self._item_stockservice(), None, [vinculo])
        self.assertEqual(fila["estado"], "Pausado")
        self.assertEqual(fila["ml_item_id"], "MLC999")

    def test_precio_ausente_no_rompe(self):
        fila = services.construir_fila_catalogo(self._item_stockservice(price=None), None, [])
        self.assertIsNone(fila["precio_neto"])
        self.assertIsNone(fila["precio_ml"])


class ObtenerConfigYMapaTests(TestCase):
    def test_trae_solo_los_skus_pedidos(self):
        SkuSyncConfig.objects.create(sku="ML000111", sync_stock=True)
        SkuSyncConfig.objects.create(sku="ML000999", sync_stock=True)  # no debe aparecer
        MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC123")

        configs, mapas = services.obtener_config_y_mapa(["ML000111"])

        self.assertEqual(set(configs.keys()), {"ML000111"})
        self.assertEqual(set(mapas.keys()), {"ML000111"})

    def test_sku_sin_fila_local_no_aparece(self):
        configs, mapas = services.obtener_config_y_mapa(["ML000111"])
        self.assertEqual(configs, {})
        self.assertEqual(mapas, {})

    def test_devuelve_todos_los_vinculos_de_un_sku_no_solo_uno(self):
        """HU-CM2.7 — con un dict plano sku->vínculo se perdía silenciosamente el resto."""
        MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC111", unidades_por_item=1)
        MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC222", unidades_por_item=100)

        _configs, mapas = services.obtener_config_y_mapa(["ML000111"])

        self.assertEqual(len(mapas["ML000111"]), 2)

    def test_los_vinculos_vienen_ordenados_por_unidades(self):
        MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC222", unidades_por_item=100)
        MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC111", unidades_por_item=1)

        _configs, mapas = services.obtener_config_y_mapa(["ML000111"])

        self.assertEqual([v.unidades_por_item for v in mapas["ML000111"]], [1, 100])


class ResolverPrecioMlTests(TestCase):
    """HU-CM1.7/2.7 — precedencia de precios y factor de pack."""

    def test_sin_config_usa_el_porcentaje_global(self):
        services.guardar_porcentaje_ajuste(Decimal("10"), usuario=None)
        self.assertEqual(services.resolver_precio_ml(1000, None), 1100)

    def test_porcentaje_propio_del_producto_pisa_el_global(self):
        services.guardar_porcentaje_ajuste(Decimal("10"), usuario=None)
        config = SkuSyncConfig(sku="ML000111", porcentaje_ajuste_propio=Decimal("50"))

        self.assertEqual(services.resolver_precio_ml(1000, config), 1500)

    def test_precio_manual_del_producto_pisa_cualquier_porcentaje(self):
        services.guardar_porcentaje_ajuste(Decimal("10"), usuario=None)
        config = SkuSyncConfig(
            sku="ML000111", porcentaje_ajuste_propio=Decimal("50"), precio_manual=Decimal("777")
        )

        self.assertEqual(services.resolver_precio_ml(1000, config), 777)

    def test_precio_manual_del_vinculo_pisa_al_del_producto(self):
        config = SkuSyncConfig(sku="ML000111", precio_manual=Decimal("777"))
        vinculo = MLItemMap(sku="ML000111", ml_item_id="MLC1", precio_manual=Decimal("99000"))

        self.assertEqual(services.resolver_precio_ml(1000, config, vinculo), 99000)

    def test_precio_manual_del_vinculo_no_se_multiplica_por_unidades(self):
        """Ya es el precio del pack tal como se tipeó — multiplicarlo de nuevo lo inflaría x100."""
        vinculo = MLItemMap(
            sku="ML000111", ml_item_id="MLC1", unidades_por_item=100, precio_manual=Decimal("21100")
        )

        self.assertEqual(services.resolver_precio_ml(211, None, vinculo), 21100)

    def test_pack_multiplica_el_precio_unitario_resuelto(self):
        """Caso real de Felipe: ML000111 a $211 la unidad, agrupación de 100 en ML."""
        vinculo = MLItemMap(sku="ML000111", ml_item_id="MLC1", unidades_por_item=100)
        self.assertEqual(services.resolver_precio_ml(211, None, vinculo), 21100)

    def test_pack_con_porcentaje_aplica_el_ajuste_antes_de_multiplicar(self):
        services.guardar_porcentaje_ajuste(Decimal("10"), usuario=None)
        vinculo = MLItemMap(sku="ML000111", ml_item_id="MLC1", unidades_por_item=100)

        self.assertEqual(services.resolver_precio_ml(211, None, vinculo), 23210)  # 211*1.1*100

    def test_redondea_una_sola_vez_al_final(self):
        """Redondear el unitario primero daría 23200 (232*100) en vez de 23210."""
        services.guardar_porcentaje_ajuste(Decimal("10"), usuario=None)
        vinculo = MLItemMap(sku="ML000111", ml_item_id="MLC1", unidades_por_item=100)

        self.assertNotEqual(services.resolver_precio_ml(211, None, vinculo), 23200)


class ResolverStockMlTests(TestCase):
    def test_sin_pack_es_el_stock_tal_cual(self):
        vinculo = MLItemMap(sku="ML000111", ml_item_id="MLC1", unidades_por_item=1)
        self.assertEqual(services.resolver_stock_ml(250, vinculo), 250)

    def test_pack_devuelve_cuantos_packs_completos_se_pueden_armar(self):
        vinculo = MLItemMap(sku="ML000111", ml_item_id="MLC1", unidades_por_item=100)
        self.assertEqual(services.resolver_stock_ml(250, vinculo), 2)

    def test_stock_insuficiente_para_un_pack_completo_da_cero(self):
        vinculo = MLItemMap(sku="ML000111", ml_item_id="MLC1", unidades_por_item=100)
        self.assertEqual(services.resolver_stock_ml(99, vinculo), 0)


class IndexViewTests(TestCase):
    """HU-CM1.1 — la vista, con Stock-Service mockeado (nunca se le pega de verdad en un test)."""

    def setUp(self):
        self.usuario = get_user_model().objects.create(email="test@bioquimica.cl")
        self.client.force_login(self.usuario)

    def _catalogo_mock(self, items=None, total=None):
        items = items if items is not None else [
            {"sku": "ML000111", "name": "Tubo de Ensayo", "price": 1234, "stock_01": 5, "stock_11": 0}
        ]
        return {"total": total if total is not None else len(items), "limit": 50, "offset": 0, "items": items}

    def test_requiere_login(self):
        self.client.logout()
        respuesta = self.client.get("/catalogo/")
        self.assertEqual(respuesta.status_code, 302)

    @patch("catalogo_ml.views.stockservice_client.obtener_catalogo")
    def test_pagina_completa_muestra_la_tabla(self, obtener_catalogo_mock):
        obtener_catalogo_mock.return_value = self._catalogo_mock()

        respuesta = self.client.get("/catalogo/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "ML000111")
        self.assertContains(respuesta, "No sincronizado")

    @patch("catalogo_ml.views.stockservice_client.obtener_catalogo")
    def test_busqueda_se_pasa_al_cliente_de_stockservice(self, obtener_catalogo_mock):
        obtener_catalogo_mock.return_value = self._catalogo_mock(items=[])

        self.client.get("/catalogo/", {"q": "xileno"})

        obtener_catalogo_mock.assert_called_once_with(search="xileno", limit=services.PAGE_SIZE, offset=0)

    @patch("catalogo_ml.views.stockservice_client.obtener_catalogo")
    def test_pagina_2_calcula_el_offset_correcto(self, obtener_catalogo_mock):
        obtener_catalogo_mock.return_value = self._catalogo_mock(items=[])

        self.client.get("/catalogo/", {"pagina": 2})

        obtener_catalogo_mock.assert_called_once_with(search=None, limit=services.PAGE_SIZE, offset=services.PAGE_SIZE)

    @patch("catalogo_ml.views.stockservice_client.obtener_catalogo")
    def test_peticion_htmx_devuelve_solo_la_tabla_sin_layout(self, obtener_catalogo_mock):
        obtener_catalogo_mock.return_value = self._catalogo_mock()

        respuesta = self.client.get("/catalogo/", HTTP_HX_REQUEST="true")

        self.assertNotContains(respuesta, "<html")
        self.assertContains(respuesta, "ML000111")

    @patch("catalogo_ml.views.stockservice_client.obtener_catalogo")
    def test_muestra_fila_ya_configurada(self, obtener_catalogo_mock):
        obtener_catalogo_mock.return_value = self._catalogo_mock()
        SkuSyncConfig.objects.create(sku="ML000111", sync_stock=True, sync_price=True)

        respuesta = self.client.get("/catalogo/")

        # sync_stock y sync_price son checkboxes (HU-CM1.2) — ambos deben venir marcados. Substring
        # específico (no solo "checked") porque el JS del "seleccionar todos" también usa esa
        # palabra (c.checked = this.checked).
        self.assertContains(respuesta, 'type="checkbox" checked', count=2)


class ToggleSyncTests(TestCase):
    """HU-CM1.2 — prender/apagar sync_stock o sync_price de un solo SKU sin recargar la página."""

    def setUp(self):
        self.usuario = get_user_model().objects.create(email="test@bioquimica.cl")
        self.client.force_login(self.usuario)

    def _catalogo_mock(self):
        return {
            "total": 1, "limit": 50, "offset": 0,
            "items": [{"sku": "ML000111", "name": "Tubo de Ensayo", "price": 1234, "stock_01": 5, "stock_11": 0}],
        }

    def test_requiere_login(self):
        self.client.logout()
        respuesta = self.client.post("/catalogo/ML000111/toggle/", {"campo": "sync_stock"})
        self.assertEqual(respuesta.status_code, 302)

    def test_solo_acepta_post(self):
        respuesta = self.client.get("/catalogo/ML000111/toggle/")
        self.assertEqual(respuesta.status_code, 405)

    def test_campo_invalido_da_400(self):
        respuesta = self.client.post("/catalogo/ML000111/toggle/", {"campo": "otra_cosa"})
        self.assertEqual(respuesta.status_code, 400)

    @patch("catalogo_ml.services.stockservice_client.obtener_catalogo")
    def test_crea_config_si_no_existia_y_prende_el_flag(self, obtener_catalogo_mock):
        obtener_catalogo_mock.return_value = self._catalogo_mock()

        respuesta = self.client.post("/catalogo/ML000111/toggle/", {"campo": "sync_stock"})

        self.assertEqual(respuesta.status_code, 200)
        config = SkuSyncConfig.objects.get(sku="ML000111")
        self.assertTrue(config.sync_stock)
        self.assertEqual(config.updated_by, self.usuario)

    @patch("catalogo_ml.services.stockservice_client.obtener_catalogo")
    def test_segundo_toggle_lo_apaga(self, obtener_catalogo_mock):
        obtener_catalogo_mock.return_value = self._catalogo_mock()
        SkuSyncConfig.objects.create(sku="ML000111", sync_stock=True)

        self.client.post("/catalogo/ML000111/toggle/", {"campo": "sync_stock"})

        self.assertFalse(SkuSyncConfig.objects.get(sku="ML000111").sync_stock)

    @patch("catalogo_ml.services.stockservice_client.obtener_catalogo")
    def test_no_toca_el_otro_flag(self, obtener_catalogo_mock):
        obtener_catalogo_mock.return_value = self._catalogo_mock()
        SkuSyncConfig.objects.create(sku="ML000111", sync_price=True)

        self.client.post("/catalogo/ML000111/toggle/", {"campo": "sync_stock"})

        config = SkuSyncConfig.objects.get(sku="ML000111")
        self.assertTrue(config.sync_price)
        self.assertTrue(config.sync_stock)

    @patch("catalogo_ml.services.stockservice_client.obtener_catalogo")
    def test_sku_inexistente_en_stockservice_da_404(self, obtener_catalogo_mock):
        obtener_catalogo_mock.return_value = {"total": 0, "limit": 50, "offset": 0, "items": []}

        respuesta = self.client.post("/catalogo/ML999999/toggle/", {"campo": "sync_stock"})

        self.assertEqual(respuesta.status_code, 404)


class ToggleMasivoTests(TestCase):
    """HU-CM1.3 — aplicar sync_stock/sync_price a varios SKU seleccionados de una sola acción."""

    def setUp(self):
        self.usuario = get_user_model().objects.create(email="test@bioquimica.cl")
        self.client.force_login(self.usuario)

    def _catalogo_mock(self):
        return {
            "total": 2, "limit": 50, "offset": 0,
            "items": [
                {"sku": "ML000111", "name": "Tubo A", "price": 100, "stock_01": 1, "stock_11": 0},
                {"sku": "ML000222", "name": "Tubo B", "price": 200, "stock_01": 2, "stock_11": 0},
            ],
        }

    def test_requiere_login(self):
        self.client.logout()
        respuesta = self.client.post("/catalogo/masivo/", {"campo": "sync_stock", "valor": "true"})
        self.assertEqual(respuesta.status_code, 302)

    def test_sin_seleccion_da_400(self):
        respuesta = self.client.post("/catalogo/masivo/", {"campo": "sync_stock", "valor": "true"})
        self.assertEqual(respuesta.status_code, 400)

    def test_campo_invalido_da_400(self):
        respuesta = self.client.post(
            "/catalogo/masivo/", {"campo": "otro", "valor": "true", "skus": ["ML000111"]}
        )
        self.assertEqual(respuesta.status_code, 400)

    @patch("catalogo_ml.views.stockservice_client.obtener_catalogo")
    def test_activa_el_flag_en_todos_los_seleccionados(self, obtener_catalogo_mock):
        obtener_catalogo_mock.return_value = self._catalogo_mock()

        respuesta = self.client.post(
            "/catalogo/masivo/", {"campo": "sync_price", "valor": "true", "skus": ["ML000111", "ML000222"]}
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(SkuSyncConfig.objects.get(sku="ML000111").sync_price)
        self.assertTrue(SkuSyncConfig.objects.get(sku="ML000222").sync_price)

    @patch("catalogo_ml.views.stockservice_client.obtener_catalogo")
    def test_desactiva_el_flag_en_los_seleccionados(self, obtener_catalogo_mock):
        obtener_catalogo_mock.return_value = self._catalogo_mock()
        SkuSyncConfig.objects.create(sku="ML000111", sync_stock=True)

        self.client.post("/catalogo/masivo/", {"campo": "sync_stock", "valor": "false", "skus": ["ML000111"]})

        self.assertFalse(SkuSyncConfig.objects.get(sku="ML000111").sync_stock)

    @patch("catalogo_ml.views.stockservice_client.obtener_catalogo")
    def test_no_toca_skus_no_seleccionados(self, obtener_catalogo_mock):
        obtener_catalogo_mock.return_value = self._catalogo_mock()

        self.client.post("/catalogo/masivo/", {"campo": "sync_stock", "valor": "true", "skus": ["ML000111"]})

        self.assertFalse(SkuSyncConfig.objects.filter(sku="ML000222").exists())

    @patch("catalogo_ml.views.stockservice_client.obtener_catalogo")
    def test_guarda_quien_hizo_el_cambio_masivo(self, obtener_catalogo_mock):
        obtener_catalogo_mock.return_value = self._catalogo_mock()

        self.client.post("/catalogo/masivo/", {"campo": "sync_stock", "valor": "true", "skus": ["ML000111"]})

        self.assertEqual(SkuSyncConfig.objects.get(sku="ML000111").updated_by, self.usuario)


_DATOS_TOKEN = {"access_token": "APP_USR-abc", "refresh_token": "TG-xyz", "expires_in": 10800, "user_id": 999}


class GuardarTokenMlTests(TestCase):
    def test_crea_la_fila_si_no_existia(self):
        services.guardar_token_ml(_DATOS_TOKEN)

        token = MLToken.objects.get()
        self.assertEqual(token.access_token, "APP_USR-abc")
        self.assertEqual(token.refresh_token, "TG-xyz")
        self.assertEqual(token.ml_user_id, 999)

    def test_calcula_expires_at_desde_expires_in(self):
        antes = timezone.now()
        services.guardar_token_ml(_DATOS_TOKEN)
        token = MLToken.objects.get()

        self.assertGreater(token.expires_at, antes + timedelta(seconds=10799))
        self.assertLess(token.expires_at, antes + timedelta(seconds=10801))

    def test_reemplaza_la_fila_anterior_en_vez_de_acumular(self):
        services.guardar_token_ml(_DATOS_TOKEN)
        services.guardar_token_ml({**_DATOS_TOKEN, "access_token": "APP_USR-nuevo"})

        self.assertEqual(MLToken.objects.count(), 1)
        self.assertEqual(MLToken.objects.get().access_token, "APP_USR-nuevo")

    def test_sin_refresh_token_no_explota_y_conserva_el_anterior(self):
        services.guardar_token_ml(_DATOS_TOKEN)
        datos_sin_refresh = {"access_token": "APP_USR-online", "expires_in": 10800, "user_id": 999}

        services.guardar_token_ml(datos_sin_refresh)

        self.assertEqual(MLToken.objects.get().refresh_token, "TG-xyz")

    def test_sin_refresh_token_y_sin_fila_anterior_guarda_vacio(self):
        datos_sin_refresh = {"access_token": "APP_USR-online", "expires_in": 10800, "user_id": 999}

        services.guardar_token_ml(datos_sin_refresh)

        self.assertEqual(MLToken.objects.get().refresh_token, "")


class HayTokenMlTests(TestCase):
    def test_false_si_no_hay_ninguno(self):
        self.assertFalse(services.hay_token_ml())

    def test_true_si_ya_se_guardo_uno(self):
        services.guardar_token_ml(_DATOS_TOKEN)
        self.assertTrue(services.hay_token_ml())


class ObtenerTokenValidoTests(TestCase):
    def test_sin_token_lanza_error_claro(self):
        with self.assertRaises(services.TokenMLNoConfigurado):
            services.obtener_token_valido()

    def test_token_vigente_se_devuelve_sin_refrescar(self):
        MLToken.objects.create(
            access_token="vigente", refresh_token="TG-1",
            expires_at=timezone.now() + timedelta(hours=5), ml_user_id=1,
        )
        with patch("catalogo_ml.services.ml_client.refrescar_token") as refrescar_mock:
            resultado = services.obtener_token_valido()

        self.assertEqual(resultado, "vigente")
        refrescar_mock.assert_not_called()

    def test_token_por_vencer_se_refresca_solo(self):
        MLToken.objects.create(
            access_token="por_vencer", refresh_token="TG-viejo",
            expires_at=timezone.now() + timedelta(minutes=5), ml_user_id=1,
        )
        with patch("catalogo_ml.services.ml_client.refrescar_token") as refrescar_mock:
            refrescar_mock.return_value = {**_DATOS_TOKEN, "access_token": "recien_refrescado"}
            resultado = services.obtener_token_valido()

        refrescar_mock.assert_called_once_with("TG-viejo")
        self.assertEqual(resultado, "recien_refrescado")
        self.assertEqual(MLToken.objects.get().access_token, "recien_refrescado")


class MlLoginViewTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create(email="test@bioquimica.cl")
        self.client.force_login(self.usuario)

    def test_requiere_login(self):
        self.client.logout()
        respuesta = self.client.get("/catalogo/ml/conectar/")
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/accounts/login/", respuesta.url)

    def test_redirige_a_mercadolibre_con_state_guardado_en_sesion(self):
        respuesta = self.client.get("/catalogo/ml/conectar/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta.url.startswith("https://auth.mercadolibre.cl/authorization?"))
        self.assertIn("state=", respuesta.url)
        self.assertIn("ml_oauth_state", self.client.session)


class MlCallbackViewTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create(email="test@bioquimica.cl")
        self.client.force_login(self.usuario)

    def _con_state_en_sesion(self, state="el-state"):
        session = self.client.session
        session["ml_oauth_state"] = state
        session.save()
        return state

    def test_error_de_ml_no_rompe_y_redirige_con_mensaje(self):
        respuesta = self.client.get("/catalogo/ml/callback/", {"error": "access_denied"})

        self.assertRedirects(respuesta, "/catalogo/")
        mensajes = [str(m) for m in respuesta.wsgi_request._messages]
        self.assertTrue(any("rechazó" in m for m in mensajes))

    def test_state_invalido_no_canjea_nada(self):
        self._con_state_en_sesion("el-state-correcto")

        with patch("catalogo_ml.views.ml_client.intercambiar_code_por_token") as canje_mock:
            self.client.get("/catalogo/ml/callback/", {"code": "abc", "state": "otro-distinto"})

        canje_mock.assert_not_called()
        self.assertFalse(services.hay_token_ml())

    def test_sin_code_no_canjea_nada(self):
        state = self._con_state_en_sesion()

        with patch("catalogo_ml.views.ml_client.intercambiar_code_por_token") as canje_mock:
            self.client.get("/catalogo/ml/callback/", {"state": state})

        canje_mock.assert_not_called()

    def test_code_y_state_correctos_guardan_el_token(self):
        state = self._con_state_en_sesion()

        with patch("catalogo_ml.views.ml_client.intercambiar_code_por_token") as canje_mock, \
             patch("catalogo_ml.services.ml_client.obtener_usuario") as usuario_mock:
            canje_mock.return_value = _DATOS_TOKEN
            usuario_mock.return_value = {"id": 999, "tags": []}
            respuesta = self.client.get("/catalogo/ml/callback/", {"code": "EL_CODE", "state": state})

        self.assertRedirects(respuesta, "/catalogo/")
        self.assertTrue(services.hay_token_ml())
        self.assertEqual(MLToken.objects.get().access_token, "APP_USR-abc")

    def test_code_y_state_correctos_tambien_detectan_el_modelo_de_item(self):
        state = self._con_state_en_sesion()

        with patch("catalogo_ml.views.ml_client.intercambiar_code_por_token") as canje_mock, \
             patch("catalogo_ml.services.ml_client.obtener_usuario") as usuario_mock:
            canje_mock.return_value = _DATOS_TOKEN
            usuario_mock.return_value = {"id": 999, "tags": ["user_product_seller"]}
            self.client.get("/catalogo/ml/callback/", {"code": "EL_CODE", "state": state})

        usuario_mock.assert_called_once_with("APP_USR-abc", 999)
        self.assertTrue(PerfilSellerML.obtener().usa_user_products)

    def test_si_falla_la_deteccion_del_modelo_el_login_sigue_exitoso(self):
        state = self._con_state_en_sesion()

        with patch("catalogo_ml.views.ml_client.intercambiar_code_por_token") as canje_mock, \
             patch("catalogo_ml.services.ml_client.obtener_usuario") as usuario_mock:
            canje_mock.return_value = _DATOS_TOKEN
            usuario_mock.side_effect = Exception("ML devolvió 500")
            respuesta = self.client.get("/catalogo/ml/callback/", {"code": "EL_CODE", "state": state})

        self.assertRedirects(respuesta, "/catalogo/")
        self.assertTrue(services.hay_token_ml())
        mensajes = [str(m) for m in respuesta.wsgi_request._messages]
        self.assertTrue(any("conectada correctamente" in m for m in mensajes))

    def test_falla_el_canje_no_rompe_con_500(self):
        state = self._con_state_en_sesion()

        with patch("catalogo_ml.views.ml_client.intercambiar_code_por_token") as canje_mock:
            canje_mock.side_effect = Exception("ML devolvió 400")
            respuesta = self.client.get("/catalogo/ml/callback/", {"code": "EL_CODE", "state": state})

        self.assertRedirects(respuesta, "/catalogo/")
        self.assertFalse(services.hay_token_ml())


class ConfiguracionSyncMLTests(TestCase):
    def test_obtener_crea_la_fila_con_cero_por_defecto(self):
        config = ConfiguracionSyncML.obtener()
        self.assertEqual(config.porcentaje_ajuste_precio, Decimal("0"))

    def test_obtener_siempre_devuelve_la_misma_fila(self):
        primera = ConfiguracionSyncML.obtener()
        primera.porcentaje_ajuste_precio = Decimal("15")
        primera.save()

        self.assertEqual(ConfiguracionSyncML.obtener().porcentaje_ajuste_precio, Decimal("15"))
        self.assertEqual(ConfiguracionSyncML.objects.count(), 1)


class CalcularPrecioMlTests(TestCase):
    def test_sin_ajuste_configurado_devuelve_el_mismo_precio(self):
        self.assertEqual(services.calcular_precio_ml(1000), 1000)

    def test_aplica_el_porcentaje_configurado(self):
        services.guardar_porcentaje_ajuste(Decimal("10"), usuario=None)
        self.assertEqual(services.calcular_precio_ml(1000), 1100)

    def test_porcentaje_negativo_descuenta(self):
        services.guardar_porcentaje_ajuste(Decimal("-20"), usuario=None)
        self.assertEqual(services.calcular_precio_ml(1000), 800)

    def test_redondea_con_round_half_up(self):
        services.guardar_porcentaje_ajuste(Decimal("2.5"), usuario=None)
        self.assertEqual(services.calcular_precio_ml(1001), 1026)  # 1026.025 -> 1026


class ActualizarPorcentajeAjusteViewTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create(email="test@bioquimica.cl")
        self.client.force_login(self.usuario)

    def test_requiere_login(self):
        self.client.logout()
        respuesta = self.client.post("/catalogo/ml/precio/", {"porcentaje": "10"})
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/accounts/login/", respuesta.url)

    def test_guarda_un_porcentaje_valido(self):
        respuesta = self.client.post("/catalogo/ml/precio/", {"porcentaje": "12.5"})

        self.assertRedirects(respuesta, "/catalogo/")
        self.assertEqual(ConfiguracionSyncML.obtener().porcentaje_ajuste_precio, Decimal("12.5"))
        self.assertEqual(ConfiguracionSyncML.obtener().updated_by, self.usuario)

    def test_valor_no_numerico_no_guarda_y_avisa(self):
        respuesta = self.client.post("/catalogo/ml/precio/", {"porcentaje": "abc"})

        self.assertRedirects(respuesta, "/catalogo/")
        self.assertEqual(ConfiguracionSyncML.obtener().porcentaje_ajuste_precio, Decimal("0"))
        mensajes = [str(m) for m in respuesta.wsgi_request._messages]
        self.assertTrue(any("no es un porcentaje válido" in m for m in mensajes))

    def test_menos_cien_por_ciento_o_menos_se_rechaza(self):
        respuesta = self.client.post("/catalogo/ml/precio/", {"porcentaje": "-100"})

        self.assertRedirects(respuesta, "/catalogo/")
        self.assertEqual(ConfiguracionSyncML.obtener().porcentaje_ajuste_precio, Decimal("0"))
        mensajes = [str(m) for m in respuesta.wsgi_request._messages]
        self.assertTrue(any("no puede ser -100%" in m for m in mensajes))


class HomeRedirigeACatalogoTests(TestCase):
    def test_raiz_redirige_al_catalogo(self):
        respuesta = self.client.get("/")
        self.assertRedirects(respuesta, "/catalogo/", fetch_redirect_response=False)


class PerfilSellerMLTests(TestCase):
    def test_obtener_crea_la_fila_con_tags_vacios_por_defecto(self):
        perfil = PerfilSellerML.obtener()
        self.assertEqual(perfil.tags, [])
        self.assertFalse(perfil.usa_user_products)
        self.assertFalse(perfil.tiene_multiorigen)

    def test_usa_user_products_sin_multiorigen(self):
        perfil = PerfilSellerML.obtener()
        perfil.tags = ["normal", "user_product_seller"]
        self.assertTrue(perfil.usa_user_products)
        self.assertFalse(perfil.tiene_multiorigen)

    def test_tiene_multiorigen_requiere_ambos_tags(self):
        perfil = PerfilSellerML.obtener()
        perfil.tags = ["warehouse_management"]
        self.assertFalse(perfil.tiene_multiorigen)
        perfil.tags = ["warehouse_management", "multiwarehouse"]
        self.assertTrue(perfil.tiene_multiorigen)


class ActualizarPerfilSellerTests(TestCase):
    def setUp(self):
        MLToken.objects.create(
            access_token="vigente", refresh_token="TG-1",
            expires_at=timezone.now() + timedelta(hours=5), ml_user_id=999,
        )

    def test_guarda_los_tags_devueltos_por_ml(self):
        with patch("catalogo_ml.services.ml_client.obtener_usuario") as usuario_mock:
            usuario_mock.return_value = {"id": 999, "tags": ["user_product_seller", "warehouse_management", "multiwarehouse"]}
            services.actualizar_perfil_seller()

        usuario_mock.assert_called_once_with("vigente", 999)
        self.assertTrue(PerfilSellerML.obtener().tiene_multiorigen)

    def test_sin_tags_en_la_respuesta_guarda_lista_vacia(self):
        with patch("catalogo_ml.services.ml_client.obtener_usuario") as usuario_mock:
            usuario_mock.return_value = {"id": 999}
            services.actualizar_perfil_seller()

        self.assertEqual(PerfilSellerML.obtener().tags, [])


class DescripcionModeloItemTests(TestCase):
    def test_multiorigen_tiene_prioridad(self):
        perfil = PerfilSellerML.obtener()
        perfil.tags = ["user_product_seller", "warehouse_management", "multiwarehouse"]
        perfil.save()
        self.assertEqual(services.descripcion_modelo_item(), "Multiorigen")

    def test_user_products_sin_multiorigen(self):
        perfil = PerfilSellerML.obtener()
        perfil.tags = ["user_product_seller"]
        perfil.save()
        self.assertEqual(services.descripcion_modelo_item(), "User Products (sin multiorigen)")

    def test_sin_tags_relevantes_es_legacy(self):
        self.assertEqual(services.descripcion_modelo_item(), "Legacy")


class VincularSiExisteEnMlTests(TestCase):
    @patch("catalogo_ml.services.ml_client.buscar_item_por_sku")
    def test_lo_encuentra_y_crea_el_mapa(self, buscar_mock):
        buscar_mock.return_value = "MLC111"

        mapa = services.vincular_si_existe_en_ml("ML000111", "APP_USR-abc", 999)

        buscar_mock.assert_called_once_with("APP_USR-abc", 999, "ML000111")
        self.assertEqual(mapa.ml_item_id, "MLC111")
        self.assertEqual(MLItemMap.objects.get(sku="ML000111").ml_item_id, "MLC111")

    @patch("catalogo_ml.services.ml_client.buscar_item_por_sku")
    def test_no_lo_encuentra_no_crea_nada(self, buscar_mock):
        buscar_mock.return_value = None

        mapa = services.vincular_si_existe_en_ml("ML000111", "APP_USR-abc", 999)

        self.assertIsNone(mapa)
        self.assertFalse(MLItemMap.objects.filter(sku="ML000111").exists())


class VincularMasivoServiceTests(TestCase):
    def setUp(self):
        MLToken.objects.create(
            access_token="vigente", refresh_token="TG-1",
            expires_at=timezone.now() + timedelta(hours=5), ml_user_id=999,
        )

    @patch("catalogo_ml.services.ml_client.buscar_item_por_sku")
    def test_separa_encontrados_de_no_encontrados(self, buscar_mock):
        buscar_mock.side_effect = lambda access_token, seller_id, sku: "MLC1" if sku == "ML000111" else None

        encontrados, no_encontrados = services.vincular_masivo(["ML000111", "ML000222"])

        self.assertEqual(encontrados, ["ML000111"])
        self.assertEqual(no_encontrados, ["ML000222"])

    @patch("catalogo_ml.services.ml_client.buscar_item_por_sku")
    def test_no_vuelve_a_buscar_un_sku_ya_vinculado(self, buscar_mock):
        MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC1")

        encontrados, no_encontrados = services.vincular_masivo(["ML000111"])

        buscar_mock.assert_not_called()
        self.assertEqual(encontrados, ["ML000111"])
        self.assertEqual(no_encontrados, [])

    def test_sin_token_lanza_error_claro(self):
        MLToken.objects.all().delete()
        with self.assertRaises(services.TokenMLNoConfigurado):
            services.vincular_masivo(["ML000111"])


class VincularMasivoViewTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create(email="test@bioquimica.cl")
        self.client.force_login(self.usuario)

    def _catalogo_mock(self):
        return {
            "total": 1, "limit": 50, "offset": 0,
            "items": [{"sku": "ML000111", "name": "Tubo A", "price": 100, "stock_01": 1, "stock_11": 0}],
        }

    def test_requiere_login(self):
        self.client.logout()
        respuesta = self.client.post("/catalogo/vincular/")
        self.assertEqual(respuesta.status_code, 302)

    def test_sin_seleccion_da_400(self):
        respuesta = self.client.post("/catalogo/vincular/")
        self.assertEqual(respuesta.status_code, 400)

    def test_sin_token_avisa_que_hay_que_conectar(self):
        respuesta = self.client.post("/catalogo/vincular/", {"skus": ["ML000111"]})

        self.assertRedirects(respuesta, "/catalogo/")
        mensajes = [str(m) for m in respuesta.wsgi_request._messages]
        self.assertTrue(any("Conectá con Mercado Libre" in m for m in mensajes))

    @patch("catalogo_ml.views.stockservice_client.obtener_catalogo")
    @patch("catalogo_ml.services.ml_client.buscar_item_por_sku")
    def test_encontrado_queda_vinculado_y_avisa(self, buscar_mock, obtener_catalogo_mock):
        MLToken.objects.create(
            access_token="vigente", refresh_token="TG-1",
            expires_at=timezone.now() + timedelta(hours=5), ml_user_id=999,
        )
        buscar_mock.return_value = "MLC111"
        obtener_catalogo_mock.return_value = self._catalogo_mock()

        respuesta = self.client.post("/catalogo/vincular/", {"skus": ["ML000111"]})

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(MLItemMap.objects.get(sku="ML000111").ml_item_id, "MLC111")
        mensajes = [str(m) for m in respuesta.wsgi_request._messages]
        self.assertTrue(any("vinculado" in m for m in mensajes))

    @patch("catalogo_ml.views.stockservice_client.obtener_catalogo")
    @patch("catalogo_ml.services.ml_client.buscar_item_por_sku")
    def test_no_encontrado_avisa_que_falta_categoria(self, buscar_mock, obtener_catalogo_mock):
        MLToken.objects.create(
            access_token="vigente", refresh_token="TG-1",
            expires_at=timezone.now() + timedelta(hours=5), ml_user_id=999,
        )
        buscar_mock.return_value = None
        obtener_catalogo_mock.return_value = self._catalogo_mock()

        respuesta = self.client.post("/catalogo/vincular/", {"skus": ["ML000111"]})

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(MLItemMap.objects.filter(sku="ML000111").exists())
        mensajes = [str(m) for m in respuesta.wsgi_request._messages]
        self.assertTrue(any("no se encontraron" in m for m in mensajes))


class SkusQueCumplenFiltroTests(TestCase):
    def test_sin_filtros_devuelve_none(self):
        self.assertIsNone(services.skus_que_cumplen_filtro())

    def test_sincronizado_devuelve_los_que_tienen_mapa(self):
        MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC1")
        MLItemMap.objects.create(sku="ML000222", ml_item_id="MLC2")

        resultado = services.skus_que_cumplen_filtro(sincronizado=True)

        self.assertEqual(resultado, {"ML000111", "ML000222"})

    def test_solo_sync_stock_devuelve_los_que_tienen_el_flag(self):
        SkuSyncConfig.objects.create(sku="ML000111", sync_stock=True)
        SkuSyncConfig.objects.create(sku="ML000222", sync_stock=False)

        resultado = services.skus_que_cumplen_filtro(solo_sync_stock=True)

        self.assertEqual(resultado, {"ML000111"})

    def test_solo_sync_precio_devuelve_los_que_tienen_el_flag(self):
        SkuSyncConfig.objects.create(sku="ML000111", sync_price=True)

        resultado = services.skus_que_cumplen_filtro(solo_sync_precio=True)

        self.assertEqual(resultado, {"ML000111"})

    def test_varios_filtros_se_combinan_con_and(self):
        SkuSyncConfig.objects.create(sku="ML000111", sync_stock=True, sync_price=True)
        SkuSyncConfig.objects.create(sku="ML000222", sync_stock=True, sync_price=False)

        resultado = services.skus_que_cumplen_filtro(solo_sync_stock=True, solo_sync_precio=True)

        self.assertEqual(resultado, {"ML000111"})


class FiltrosEnLaGrillaViewTests(TestCase):
    """Filtros de la grilla (sincronizado / sync stock / sync precio) — vía la vista index."""

    def setUp(self):
        self.usuario = get_user_model().objects.create(email="test@bioquimica.cl")
        self.client.force_login(self.usuario)

    @patch("catalogo_ml.views.stockservice_client.obtener_catalogo")
    def test_sin_filtros_usa_la_paginacion_normal_de_stockservice(self, obtener_catalogo_mock):
        obtener_catalogo_mock.return_value = {"total": 0, "limit": 50, "offset": 0, "items": []}

        self.client.get("/catalogo/")

        obtener_catalogo_mock.assert_called_once_with(search=None, limit=services.PAGE_SIZE, offset=0)

    @patch("catalogo_ml.services.stockservice_client.obtener_catalogo")
    def test_con_filtro_sincronizado_no_usa_la_paginacion_de_stockservice(self, obtener_catalogo_mock):
        MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC1")
        obtener_catalogo_mock.return_value = {
            "total": 1, "limit": 50, "offset": 0,
            "items": [{"sku": "ML000111", "name": "Tubo A", "price": 100, "stock_01": 1, "stock_11": 0}],
        }

        respuesta = self.client.get("/catalogo/", {"sincronizado": "1"})

        self.assertContains(respuesta, "ML000111")
        # Se busca por sku (obtener_item_stockservice_por_sku), no con la paginación normal.
        obtener_catalogo_mock.assert_called_once_with(search="ML000111", limit=50, offset=0)

    @patch("catalogo_ml.services.stockservice_client.obtener_catalogo")
    def test_filtro_sincronizado_no_muestra_lo_que_no_tiene_mapa(self, obtener_catalogo_mock):
        SkuSyncConfig.objects.create(sku="ML000333", sync_stock=True)  # sin MLItemMap

        respuesta = self.client.get("/catalogo/", {"sincronizado": "1"})

        self.assertEqual(respuesta.context["total"], 0)
        obtener_catalogo_mock.assert_not_called()

    @patch("catalogo_ml.services.stockservice_client.obtener_catalogo")
    def test_filtro_solo_sync_stock(self, obtener_catalogo_mock):
        SkuSyncConfig.objects.create(sku="ML000111", sync_stock=True)
        SkuSyncConfig.objects.create(sku="ML000222", sync_stock=False)
        obtener_catalogo_mock.return_value = {
            "total": 1, "limit": 50, "offset": 0,
            "items": [{"sku": "ML000111", "name": "Tubo A", "price": 100, "stock_01": 1, "stock_11": 0}],
        }

        respuesta = self.client.get("/catalogo/", {"solo_sync_stock": "1"})

        self.assertContains(respuesta, "ML000111")
        self.assertEqual(respuesta.context["total"], 1)

    @patch("catalogo_ml.services.stockservice_client.obtener_catalogo")
    def test_filtro_combinado_con_busqueda_de_texto(self, obtener_catalogo_mock):
        MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC1")
        MLItemMap.objects.create(sku="ML000222", ml_item_id="MLC2")

        def _catalogo_por_sku(search=None, limit=0, offset=0):
            productos = {
                "ML000111": {"sku": "ML000111", "name": "Xileno", "price": 100, "stock_01": 1, "stock_11": 0},
                "ML000222": {"sku": "ML000222", "name": "Etanol", "price": 200, "stock_01": 2, "stock_11": 0},
            }
            return {"total": 1, "limit": 50, "offset": 0, "items": [productos[search]]}

        obtener_catalogo_mock.side_effect = _catalogo_por_sku

        respuesta = self.client.get("/catalogo/", {"sincronizado": "1", "q": "xileno"})

        self.assertContains(respuesta, "ML000111")
        self.assertNotContains(respuesta, "ML000222")
