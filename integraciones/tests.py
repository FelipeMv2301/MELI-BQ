"""
Tests de integraciones/*.py — mockean la respuesta HTTP, nunca pegan a la API real (ver memoria
feedback-tests-obligatorios: los clientes hacia APIs externas se testean con la respuesta grabada).
"""

from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from integraciones import stockservice_client

_SETTINGS_TEST = {
    "STOCKSERVICE_BASE_URL": "https://stock-sap-bq-production.up.railway.app",
    "STOCKSERVICE_API_KEY": "clave-de-prueba",
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
