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
from .models import ConfiguracionSyncML, MLItemMap, MLToken, SkuSyncConfig


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

        with patch("catalogo_ml.views.ml_client.intercambiar_code_por_token") as canje_mock:
            canje_mock.return_value = _DATOS_TOKEN
            respuesta = self.client.get("/catalogo/ml/callback/", {"code": "EL_CODE", "state": state})

        self.assertRedirects(respuesta, "/catalogo/")
        self.assertTrue(services.hay_token_ml())
        self.assertEqual(MLToken.objects.get().access_token, "APP_USR-abc")

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
