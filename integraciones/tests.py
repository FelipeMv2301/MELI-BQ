"""
Tests de integraciones/*.py — mockean la respuesta HTTP, nunca pegan a la API real (ver memoria
feedback-tests-obligatorios: los clientes hacia APIs externas se testean con la respuesta grabada).
"""

from unittest.mock import Mock, patch
from urllib.parse import parse_qs

from django.test import SimpleTestCase, override_settings

from integraciones import ml_client, stockservice_client

_SETTINGS_TEST = {
    "STOCKSERVICE_BASE_URL": "https://stock-sap-bq-production.up.railway.app",
    "STOCKSERVICE_API_KEY": "clave-de-prueba",
}

_ML_SETTINGS_TEST = {
    "ML_APP_ID": "123456",
    "ML_APP_SECRET": "secreto-de-prueba",
}


def _respuesta_mock(payload):
    respuesta = Mock()
    respuesta.json.return_value = payload
    respuesta.raise_for_status = Mock()  # no-op: estos tests cubren el camino feliz
    return respuesta


@override_settings(**_SETTINGS_TEST)
class ObtenerProductoTests(SimpleTestCase):
    @patch("integraciones.stockservice_client.requests.get")
    def test_pega_al_endpoint_correcto_con_el_header_de_api_key(self, get_mock):
        get_mock.return_value = _respuesta_mock({"sku": "ML000111", "sap": None, "woo": [], "recent_logs": []})

        stockservice_client.obtener_producto("ML000111")

        url_llamada = get_mock.call_args.args[0]
        headers_llamada = get_mock.call_args.kwargs["headers"]
        self.assertEqual(
            url_llamada,
            "https://stock-sap-bq-production.up.railway.app/api/v1/stock/products/ML000111",
        )
        self.assertEqual(headers_llamada, {"X-API-Key": "clave-de-prueba"})

    def test_devuelve_el_json_de_la_respuesta(self):
        payload = {"sku": "ML000111", "sap": {"name": "Xileno"}, "woo": [], "recent_logs": []}
        with patch("integraciones.stockservice_client.requests.get") as get_mock:
            get_mock.return_value = _respuesta_mock(payload)
            resultado = stockservice_client.obtener_producto("ML000111")
        self.assertEqual(resultado, payload)


@override_settings(**_SETTINGS_TEST)
class ObtenerCatalogoTests(SimpleTestCase):
    @patch("integraciones.stockservice_client.requests.get")
    def test_pasa_search_limit_y_offset_como_query_params(self, get_mock):
        get_mock.return_value = _respuesta_mock({"total": 0, "limit": 20, "offset": 0, "items": []})

        stockservice_client.obtener_catalogo(search="xileno", limit=20, offset=40)

        params_llamada = get_mock.call_args.kwargs["params"]
        self.assertEqual(params_llamada, {"limit": 20, "offset": 40, "search": "xileno"})

    @patch("integraciones.stockservice_client.requests.get")
    def test_sin_search_no_manda_ese_parametro(self, get_mock):
        get_mock.return_value = _respuesta_mock({"total": 0, "limit": 0, "offset": 0, "items": []})

        stockservice_client.obtener_catalogo()

        params_llamada = get_mock.call_args.kwargs["params"]
        self.assertNotIn("search", params_llamada)

    def test_devuelve_el_catalogo_paginado(self):
        payload = {
            "total": 1,
            "limit": 20,
            "offset": 0,
            "items": [{"sku": "ML000111", "name": "Xileno (Xilol) Puro - 1 Lt", "price": 9758}],
        }
        with patch("integraciones.stockservice_client.requests.get") as get_mock:
            get_mock.return_value = _respuesta_mock(payload)
            resultado = stockservice_client.obtener_catalogo(search="xileno")
        self.assertEqual(resultado, payload)


@override_settings(**_ML_SETTINGS_TEST)
class ConstruirUrlAutorizacionTests(SimpleTestCase):
    def test_incluye_client_id_redirect_uri_state_y_scope(self):
        url = ml_client.construir_url_autorizacion("https://meli-dev.bioquimica.cl/catalogo/ml/callback/", "abc123")
        query = parse_qs(url.split("?", 1)[1])

        self.assertTrue(url.startswith("https://auth.mercadolibre.cl/authorization?"))
        self.assertEqual(query["client_id"], ["123456"])
        self.assertEqual(query["redirect_uri"], ["https://meli-dev.bioquimica.cl/catalogo/ml/callback/"])
        self.assertEqual(query["state"], ["abc123"])
        self.assertEqual(query["response_type"], ["code"])
        self.assertEqual(query["scope"], ["offline_access read write"])


@override_settings(**_ML_SETTINGS_TEST)
class IntercambiarCodePorTokenTests(SimpleTestCase):
    @patch("integraciones.ml_client.requests.post")
    def test_manda_grant_type_authorization_code_con_las_credenciales(self, post_mock):
        post_mock.return_value = _respuesta_mock({
            "access_token": "APP_USR-abc", "refresh_token": "TG-xyz",
            "expires_in": 10800, "user_id": 999,
        })

        ml_client.intercambiar_code_por_token("EL_CODE", "https://meli-dev.bioquimica.cl/catalogo/ml/callback/")

        datos_enviados = post_mock.call_args.kwargs["data"]
        self.assertEqual(datos_enviados["grant_type"], "authorization_code")
        self.assertEqual(datos_enviados["client_id"], "123456")
        self.assertEqual(datos_enviados["client_secret"], "secreto-de-prueba")
        self.assertEqual(datos_enviados["code"], "EL_CODE")
        self.assertEqual(datos_enviados["redirect_uri"], "https://meli-dev.bioquimica.cl/catalogo/ml/callback/")
        self.assertNotIn("code_verifier", datos_enviados)

    @patch("integraciones.ml_client.requests.post")
    def test_incluye_code_verifier_si_se_usa_pkce(self, post_mock):
        post_mock.return_value = _respuesta_mock({"access_token": "x", "refresh_token": "y", "expires_in": 1, "user_id": 1})

        ml_client.intercambiar_code_por_token("EL_CODE", "https://x/callback/", code_verifier="verificador")

        self.assertEqual(post_mock.call_args.kwargs["data"]["code_verifier"], "verificador")

    @patch("integraciones.ml_client.requests.post")
    def test_devuelve_el_json_de_la_respuesta(self, post_mock):
        payload = {"access_token": "APP_USR-abc", "refresh_token": "TG-xyz", "expires_in": 10800, "user_id": 999}
        post_mock.return_value = _respuesta_mock(payload)

        resultado = ml_client.intercambiar_code_por_token("EL_CODE", "https://x/callback/")

        self.assertEqual(resultado, payload)


@override_settings(**_ML_SETTINGS_TEST)
class RefrescarTokenTests(SimpleTestCase):
    @patch("integraciones.ml_client.requests.post")
    def test_manda_grant_type_refresh_token(self, post_mock):
        post_mock.return_value = _respuesta_mock({
            "access_token": "APP_USR-nuevo", "refresh_token": "TG-nuevo",
            "expires_in": 10800, "user_id": 999,
        })

        ml_client.refrescar_token("TG-viejo")

        datos_enviados = post_mock.call_args.kwargs["data"]
        self.assertEqual(datos_enviados["grant_type"], "refresh_token")
        self.assertEqual(datos_enviados["refresh_token"], "TG-viejo")
        self.assertEqual(datos_enviados["client_id"], "123456")


class ObtenerUsuarioTests(SimpleTestCase):
    @patch("integraciones.ml_client.requests.get")
    def test_pega_al_endpoint_correcto_con_el_bearer_token(self, get_mock):
        get_mock.return_value = _respuesta_mock({"id": 999, "tags": ["normal", "user_product_seller"]})

        ml_client.obtener_usuario("APP_USR-abc", 999)

        url_llamada = get_mock.call_args.args[0]
        headers_llamada = get_mock.call_args.kwargs["headers"]
        self.assertEqual(url_llamada, "https://api.mercadolibre.com/users/999")
        self.assertEqual(headers_llamada, {"Authorization": "Bearer APP_USR-abc"})

    def test_devuelve_el_json_de_la_respuesta(self):
        payload = {"id": 999, "tags": ["user_product_seller", "warehouse_management", "multiwarehouse"]}
        with patch("integraciones.ml_client.requests.get") as get_mock:
            get_mock.return_value = _respuesta_mock(payload)
            resultado = ml_client.obtener_usuario("APP_USR-abc", 999)
        self.assertEqual(resultado, payload)
