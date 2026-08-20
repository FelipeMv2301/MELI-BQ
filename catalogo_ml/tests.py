import json
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import SimpleTestCase, TestCase

from utils import limpiar_descripcion_html

from . import services
from .models import MLItemMap, SkuSyncConfig


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
    def test_sku_y_ml_item_id_son_unicos(self):
        MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC123456789")
        with self.assertRaises(IntegrityError):
            MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC999999999")

    def test_status_default_es_active(self):
        item = MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC123456789")
        self.assertEqual(item.status, MLItemMap.Status.ACTIVE)

    def test_str_incluye_sku_y_item_id(self):
        item = MLItemMap.objects.create(sku="ML000111", ml_item_id="MLC123456789")
        self.assertEqual(str(item), "ML000111 -> MLC123456789")


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

    def test_sin_config_ni_mapa_queda_no_sincronizado(self):
        fila = services.construir_fila_catalogo(self._item_stockservice(), None, None)
        self.assertFalse(fila["sync_stock"])
        self.assertFalse(fila["sync_price"])
        self.assertEqual(fila["estado"], "No sincronizado")
        self.assertIsNone(fila["ml_item_id"])

    def test_stock_web_solo_suma_bodegas_01_y_11(self):
        fila = services.construir_fila_catalogo(self._item_stockservice(), None, None)
        self.assertEqual(fila["stock_web"], 8)  # 5 + 3, sin contar stock_15

    def test_con_config_refleja_los_flags_activos(self):
        config = SkuSyncConfig(sku="ML000111", sync_stock=True, sync_price=False)
        fila = services.construir_fila_catalogo(self._item_stockservice(), config, None)
        self.assertTrue(fila["sync_stock"])
        self.assertFalse(fila["sync_price"])

    def test_con_mapa_muestra_el_estado_publicado(self):
        mapa = MLItemMap(sku="ML000111", ml_item_id="MLC999", status=MLItemMap.Status.PAUSED)
        fila = services.construir_fila_catalogo(self._item_stockservice(), None, mapa)
        self.assertEqual(fila["estado"], "Pausado")
        self.assertEqual(fila["ml_item_id"], "MLC999")

    def test_precio_ausente_no_rompe(self):
        fila = services.construir_fila_catalogo(self._item_stockservice(price=None), None, None)
        self.assertIsNone(fila["precio_neto"])


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
