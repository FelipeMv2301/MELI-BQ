TITLE: Órdenes

Gestionar órdenes
Una orden es una solicitud que realiza un cliente para una publicación con
intención de comprarlo conforme a una serie de condiciones que seleccionará
en el flujo del proceso de compra (checkout). Todas las condiciones de la
venta se detallan en la orden, la cual se replicará para las cuentas del
comprador y el vendedor. Conoce más
el flujo para gestionar órdenes simples y de carrito, pagos y
envíos.
Obtener una orden
Una vez que se crea una nueva orden en el usuario, se puede consultar los
detalles al realizar una solicitud al recurso de órdenes. Además, te
recomendamos suscribirte al nuevo tópico
orders
feedback
para estar actualizado sobre los feedbacks recibidos.
Llamada:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/orders/$ORDER_ID
Ejemplo:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/orders/2000003508419013
Respuesta:
{
"id": 2000003508419013,
"status": "paid",
"status_detail": null,
"date_created": "2013-05-27T10:01:50.000-04:00",
"date_closed": "2013-05-27T10:04:07.000-04:00",
"order_items": [{
"item": {
"id": "MLB12345678",
"title": "Samsung Galaxy",
"variation_id": null,
"variation_attributes": []
},
"quantity": 1,
"unit_price": 499,
"currency_id": "BRL"
}],
"total_amount": 499,
"currency_id": "BRL",
"buyer": {
"id": "123456789",
},
"seller": {
"id": "123456789",
},
"payments": [{
"id": "596707837",
"transaction_amount": 499,
"currency_id": "BRL",
"status": "approved",
"date_created": null,
"date_last_modified": null
}],
"feedback": {
"purchase": null,
"sale": null
},
"context": {
"channel": "marketplace",
"site": "MLB",
"flows": [
000]
},
"shipping": {
"id": 20676482441
},
"tags": [
"no_shipping",
"paid",
"not_delivered"
]
}
Notas:
- Para obtener el detalle del feedback, debes realizar un llamado al
recurso
/feedbacks/$feedback_id
con el ID obtenido en la orden.
-También puedes consumir la información de los feedbacks usando el
recurso
/orders/$order_id/feedback.
- Es posible obtener las informaciones del vendedor consultando a la
API de users
utilizando el access_token.
Campos de respuesta:
id: identificador único de la orden.
date_created: fecha de creación de la orden
date_closed: fecha de confirmación de la orden. Se
define cuando una orden cambia por primera vez al estado: confirmed / paid y
se descuenta el stock del ítem.
expiration_date: fecha límite que tiene el usuario
para calificar porque, luego de la misma, se vuelve visible el feedback, se
emiten los pagos (si hubiese) y se crean los cargos.
status: estado de la orden.
Ver los valores posibles.
description: descripción del estado.
buyer: información del comprador.
seller: información del vendedor.
order_items: publicaciones en la orden.
- item: publicación específica.
- cantidad: cantidad de items comprados.
- sale_fee: comisión de ventas.
-  unit_price: precio unitário.
-  gross_price: El atributo gross_price es un campo que representa el monto original que el cliente hubiese pagado por todas las unidades del ítem sin descuentos. Este campo permite visualizar claramente el impacto de los descuentos aplicados en cada orden.
payments: pagos relacionados con la orden.
feedback: ID del feedback relacionada con la orden.
context: detalle de las características de la creación de una
orden.
-
channel: los canales de venta que hoy tiene el ítem.
Valores posibles: proximity, mp-channel, marketplace.
-
site: ID del sitio donde se originó la compra (MLA, MLB,
MLM, etc)
-
flows: es una lista de características del origen de la
compra. Valores posibles b2b, cbt, subscription, reservation, catalog, contract,
supermarket, 3x_campaign, high_concurrency, lite.
shipping: ID del envío para esta orden.
total_amount: monto total de la orden.
currency_id: ID de moneda.
tags: lista de los tags adicionados por MeLi o el vendedor,
tales como entregado, pagado, con descuento, sin envio, b2b.
taxes: monto con la sumatoria de impuestos que hay que
pagar de la orden.
cancel_detail: detalle de la
cancelación de la orden en las que se encuentra.
-
group: agrupación lógica de la cancelación (mediations,
fiscal, buyer, fraud, item, shipment, delivery, seller, internal).
-
code: código de la causa de cancelación.
-
description: descripción de la causa de cancelación.
-
requested_by: quien solicita la cancelación (buyer,
seller, Mercado Libre).
-
date: fecha de la cancelación.
-
Nota: El campo gross_price está disponible en el objeto order_items de cada orden y representa el precio total bruto considerando la cantidad de unidades.
¿Cómo se calcula?
El gross_price se calcula mediante la siguiente fórmula:
gross_price = (unit_price + discounts.full) × quantity
Componentes de la fórmula
Campo
Tipo
Descripción
unit_price
Number
Precio unitario del ítem después de aplicar los descuentos.
discounts.full
Number
Descuento unitario aplicado al ítem (siempre expresado por unidad).
quantity
Number
Cantidad de unidades del ítem en la orden.
gross_price
Number
Monto total original sin descuentos para todas las unidades del ítem.
Características importantes
- Sin descuentos: Cuando no hay descuentos aplicados, el gross_price coincide con el total pagado (unit_price × quantity).
- Moneda: El gross_price se expresa en la misma moneda que el unit_price (definida en el campo currency_id).
- Cálculo por ítem: Cada ítem en order_items tiene su propio valor de gross_price.
Ejemplo de respuesta con gross_price
Llamada:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/orders/$ORDER_ID
Respuesta:
{
"id": 2000003456789012,
"status": "paid",
"status_detail": null,
"date_created": "2026-01-05T10:30:00.000-03:00",
"date_closed": "2026-01-05T10:32:15.000-03:00",
"order_items": [
{
"item": {
"id": "MLM823798303",
"title": "Versace Pour Homme 100ml Edt Spray"
},
"quantity": 2,
"unit_price": 440.00,
"discounts": [
{
"amounts": {
"full": 341.00,
"seller": 341.00
}
}
],
"gross_price": 1562.00,
"currency_id": "MXN"
}
],
"total_amount": 880.00,
"currency_id": "MXN",
"buyer": {
"id": 123456789
},
"seller": {
"id": 987654321
},
"payments": [
{
"id": 12345678901,
"transaction_amount": 880.00,
"currency_id": "MXN",
"status": "approved",
"date_created": "2026-01-05T10:31:00.000-03:00",
"date_last_modified": "2026-01-05T10:32:00.000-03:00"
}
],
"shipping": {
"id": 43210987654321
},
"tags": [
"paid",
"not_delivered"
]
}
Desglose del cálculo en el ejemplo
Cálculo paso a paso:
// Datos del ejemplo
unit_price = 440.00        // Precio unitario CON descuento aplicado
discounts.full = 341.00    // Descuento unitario
quantity = 2               // Cantidad de unidades
// Aplicación de la fórmula
gross_price = (unit_price + discounts.full) × quantity
gross_price = (440.00 + 341.00) × 2
gross_price = 781.00 × 2
gross_price = 1562.00      // Precio bruto total sin descuentos
Consideraciones
- El campo gross_price puede no estar presente en órdenes antiguas creadas antes de la implementación de este atributo.
- Cuando no hay descuentos aplicados (discounts.full = 0), el valor de gross_price será igual a unit_price × quantity.
- El gross_price se expresa en la misma moneda indicada en el campo currency_id del ítem.
- El campo discounts.seller indica la porción del descuento que asume el vendedor, útil para campañas co-fondeadas.
Notas:
- Las comisiones son calculadas al momento de la acreditación del
pago, o sea, solo cuando el pedido si queda visible al vendedor y no
cuando el pedido es creado .
- Ventas donde el pago falló pueden tener el medio de
envío original cambiado ya que hay una recompra. Para casos donde la
compra original tenia un envío asociado y la recompra un "to be
agree", el status del envío si quedará status: "cancelled", substatus:
"closed_by_user" y la venta necesita ser cancelada.
- Para obtener información del envío se debe
realizar un llamado al recurso
/shipments/shipping.id
con el id obtenido en la orden.
-El array “context” trae información sobre flujo de generación de la
compra y puede servir para análisis de los vendedores.
Alertas de fraude (frenados de envíos)
Luego de la aprobación del pago, y debido al relacionamiento con bancos y
emisoras de tarjetas, podemos recibir alertas de que la venta en cuestión se
trata de un fraude y para evitar un gasto finanaciero, la mercadería no debe
ser enviada al comprador.
En este caso,
la orden estará marcada con el tag "fraud_risk_detected" y
enviaremos una notificación al tópico "orders_v2" con el ID de la orden.
Una vez identificada, la orden debe ser cancelada. En caso que el vendedor
haya enviado el producto, será necesario comprobar el envío a través de
Mercado Libre o Mercado Pago.
Consultar envios asociados a una venta Actualizado
Con este recurso puedes obtener el/los envíos asociados a una venta. A partir del ID de la orden, retorna el ID y type correspondientes. Es útil para conocer y relacionar los envíos desde la orden, y conformar la relación de las entidades partiendo de los pedidos. Soporta tanto el envío de compra (forward) como las devoluciones (return) cuando las hubiere.
CAMBIO DE FORMATO
La Hosted View SIEMPRE devuelve un array [], incluso cuando la orden tiene un solo envío. En la vista actual, sin los parámetros list ni list_all, el endpoint devuelve un objeto único {}.
SI MIGRÁS A LA HOSTED VIEW SIN ACTUALIZAR TU DESARROLLO PARA LEER UN ARRAY EN LUGAR DE UN OBJETO, TU INTEGRACIÓN FALLARÁ AUTOMÁTICAMENTE.
Llamada
curl -X GET -H 'Authorization: Bearer ACCESSTOKEN'-H'X-New-Domain:true'https://api.mercadolibre.com/orders/ORDER_ID/shipments
Parametros
Parámetro
Tipo
Required
Descripción
order_id
Long
Sí
ID de la orden
Query Params
Parámetro
Tipo
Required
Default
Descripción
hosted
Boolean
No
false
Parámetro para visualizar la vista soportada por APICore, sin el detalle de los envíos.
Headers
Header
Tipo
Required
Descripción
X-New-Domain
Boolean
No
Necesario en llamadas públicas para hacer el routing hasta la vista hosted.
Respuesta (200 OK)
Retorna un array de shipments (forward, y opcionalmente return):
[
{
"id": 46803546483,
"type": "forward"
},
{
"id": 46862336330,
"type": "return"
},
{
"id": 46875410994,
"type": "return_to_buyer"
}
]
Nota:
No asumas que el primer elemento del array es el envío original. Debés iterar el array y filtrar explícitamente por type == "forward" para identificar el envío de compra.
Descripción de Campos
Campo
Tipo
Descripción
id
Long
ID del shipment
type
String
Tipo de envío (e.g., forward envío de compra, return devolución al seller)
Status Codes
Code
Descripción
200 OK
Shipments encontrados
204 No Content
La orden existe pero no tiene shipments asociados (o están en proceso de propagación asíncrona)
400 Bad Request
Parámetros inválidos (e.g., order_id no numérico)
401 Unauthorized
Autenticación fallida o caller no identificado
403 Forbidden
Sin permisos suficientes para acceder al recurso (e.g., consultar devoluciones sin autorización)
404 Not Found
El order_id no existe
500 Internal Server Error
Error del servidor
503 Service Unavailable
Servicio no disponible
Vista actual
Importante:
Esta vista será deprecada a partir de finales de septiembre de 2026.
Llamada
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' -H 'X-New-Domain: true' https://api.mercadolibre.com/orders/2000014428837134/shipments?list_all=true
Parametros
Parámetro
Tipo
Required
Descripción
order_id
Long
Sí
ID de la orden
Query Params
Parámetro
Tipo
Required
Default
Descripción
list_all
Boolean
No
false
Si true, retorna un array con los shipments de tipo forward + return (devoluciones)
Headers
Header
Tipo
Required
Descripción
X-New-Domain
Boolean
No
Necesario en llamadas públicas para hacer el routing hasta la vista hosted.
X-Api-Version
String
No
Enviar con valor 2 para recibir los datos PII completos (receiver_name, receiver_phone) dentro de receiver_address. Se recomienda enviarlo de forma estable para validar que los flujos funcionan con el contrato desacoplado antes de migrar a la Hosted View.
Response (200 OK) — Caso base (sin list ni list_all)
Retorna un objeto único con el shipment forward de la orden:
{
"id": 46140728791,
"order_id": 2000014428837134,
"pack_id": 2000010703698453,
"status": "delivered",
"substatus": null,
"type": "forward",
"mode": "me2",
"logistic_type": "self_service",
"tracking_number": "46140728791",
"service_id": 413471,
"sender_id": 87778784,
"receiver_id": 182431181,
"site_id": "MPE",
"market_place": "MELI",
"order_cost": 3577.91,
"base_cost": 14.5,
"date_created": "2025-12-22T03:04:56.853-04:00",
"last_updated": "2025-12-23T16:20:08.028-04:00",
"date_first_printed": "2025-12-23T10:57:10.026-04:00",
"created_by": "receiver",
"status_history": {
"date_handling": "2025-12-22T03:05:36.000-04:00",
"date_ready_to_ship": "2025-12-22T03:05:39.891-04:00",
"date_shipped": "2025-12-23T14:29:32.000-04:00",
"date_first_visit": "2025-12-23T16:20:05.000-04:00",
"date_delivered": "2025-12-23T16:20:05.000-04:00"
},
"shipping_items": [
{
"id": "MPE879310016",
"description": "Apple Macbook Air 13 M4 16 Gb De Ram 256 Gb Ssd Plateada",
"quantity": 1,
"user_product_id": "MPEU3190351474",
"sender_id": 87778784
}
],
"shipping_option": {
"id": 656816902,
"name": "Prioritario a domicilio",
"shipping_method_id": 513647,
"cost": 0,
"list_cost": 7.25,
"currency_id": "PEN",
"delivery_type": "estimated"
}
}
Response (200 OK) — Caso lista (con list=true o list_all=true)
Retorna un array de shipments (forward, y opcionalmente return):
[
{
"id": 46803546483,
"order_id": 2000015872907480,
"pack_id": 2000010703698453,
"status": "delivered",
"substatus": null,
"type": "forward",
"mode": "me2",
"logistic_type": "cross_docking",
"tracking_number": "d4cc9f8f-2899-55ff-aac3-30ea36c1eadd",
"tracking_method": "MEL Distribution",
"return_tracking_number": null,
"service_id": 157861,
"sender_id": 1281407372,
"receiver_id": 165500824,
"site_id": "MLB",
"market_place": "MELI",
"order_cost": 480,
"base_cost": 0,
"date_created": "2026-04-07T10:11:29.102-04:00",
"last_updated": "2026-04-11T08:51:38.673-04:00",
"date_first_printed": "2026-04-08T09:32:28.417-04:00",
"created_by": "receiver",
"status_history": {
"date_handling": "2026-04-07T10:12:24.000-04:00",
"date_ready_to_ship": "2026-04-07T10:12:24.000-04:00",
"date_shipped": "2026-04-08T20:31:10.673-04:00",
"date_first_visit": "2026-04-11T08:51:37.000-04:00",
"date_delivered": "2026-04-11T08:51:37.000-04:00",
"date_not_delivered": null,
"date_returned": null,
"date_cancelled": null
},
"shipping_items": [
{
"id": "MLB4440111989",
"description": "Borracha Líquida 45kg Solução Para Vazamento Em Telhado",
"quantity": 1,
"dimensions": "24.0x26.0x33.0,2010.0",
"user_product_id": "MLBU3756435310",
"sender_id": 1281407372
}
],
"shipping_option": {
"id": 3033979541,
"name": "Normal",
"shipping_method_id": 100009,
"cost": 0,
"list_cost": 56.7,
"currency_id": "BRL",
"delivery_type": "estimated"
},
"tags": ["source_pack_split"]
},
{
"id": 46862336330,
"order_id": 2000015872907480,
"pack_id": 2000010703698453,
"status": "delivered",
"substatus": null,
"type": "return",
"mode": "me2",
"logistic_type": "xd_drop_off",
"tracking_number": "MEL46862336330FMDOR01",
"tracking_method": null,
"return_tracking_number": null,
"service_id": null,
"sender_id": 165500824,
"receiver_id": 1281407372,
"site_id": "MLB",
"market_place": "MELI",
"order_cost": 480,
"base_cost": 20,
"date_created": "2026-04-15T13:14:18.637-04:00",
"last_updated": "2026-04-17T00:32:44.587-04:00",
"date_first_printed": "2026-04-15T13:14:18.939-04:00",
"created_by": "receiver",
"status_history": {
"date_handling": "2026-04-15T13:14:18.685-04:00",
"date_ready_to_ship": "2026-04-15T13:14:18.939-04:00",
"date_shipped": "2026-04-16T03:56:43.381-04:00",
"date_first_visit": null,
"date_delivered": "2026-04-17T00:32:42.768-04:00",
"date_not_delivered": null,
"date_returned": null,
"date_cancelled": null
},
"shipping_items": [
{
"id": "MLB4440111989",
"description": "Borracha Líquida 45kg Solução Para Vazamento Em Telhado",
"quantity": 1,
"dimensions": "24.0x26.0x33.0,2010.0",
"user_product_id": "MLBU3756435310",
"sender_id": 165500824
}
],
"shipping_option": {
"id": 5101454440111989,
"name": "Devolução padrão",
"shipping_method_id": 510145,
"cost": 20,
"list_cost": 20,
"currency_id": "BRL",
"delivery_type": "estimated"
},
"tags": ["claims_return"]
},
{
"id": 46875410994,
"order_id": 2000015872907480,
"pack_id": 2000010703698453,
"status": "ready_to_ship",
"substatus": "printed",
"type": "return_to_buyer",
"mode": "me2",
"logistic_type": "melinet",
"tracking_number": "1f3338d7-eebc-5168-bf54-b226b3691178",
"tracking_method": "MEL Distribution",
"return_tracking_number": null,
"service_id": 157861,
"sender_id": 1281407372,
"receiver_id": 165500824,
"site_id": "MLB",
"market_place": "MELI",
"order_cost": 480,
"base_cost": 21.1,
"date_created": "2026-04-17T08:08:54.860-04:00",
"last_updated": "2026-04-17T11:00:23.014-04:00",
"date_first_printed": "2026-04-17T11:00:22.116-04:00",
"created_by": "triage",
"status_history": {
"date_handling": "2026-04-17T08:08:57.000-04:00",
"date_ready_to_ship": "2026-04-17T08:08:59.643-04:00",
"date_shipped": null,
"date_first_visit": null,
"date_delivered": null,
"date_not_delivered": null,
"date_returned": null,
"date_cancelled": null
},
"shipping_items": [
{
"id": "MLB4440111989",
"description": "Borracha Líquida 45kg Solução Para Vazamento Em Telhado",
"quantity": 1,
"dimensions": "15.0x16.0x19.0,2705.0",
"user_product_id": "MLBU3756435310",
"sender_id": 1281407372
}
],
"shipping_option": {
"id": 5101454440111989,
"name": "Devolução padrão",
"shipping_method_id": 510145,
"cost": 21.1,
"list_cost": 21.1,
"currency_id": "BRL",
"delivery_type": "estimated"
},
"tags": []
}
]
Descripción de Campos
Campo
Tipo
Descripción
id
Long
ID del shipment
order_id
Long
ID de la orden asociada
pack_id
Long
ID del pack al que pertenece la orden
status
String
Estado del shipment. Valores conocidos: pending, handling, ready_to_ship, shipped, delivered, not_delivered, not_verified, cancelled
substatus
String (nullable)
Substatus del envío
type
String
Tipo de envío (e.g., forward envío de compra, return devolución al seller, return_to_buyer devolución reenviada al buyer)
mode
String
Modo logístico del envío (e.g., me2)
logistic_type
String
Tipo logístico del envío
tracking_number
String (nullable)
Número de seguimiento del envío
tracking_method
String (nullable)
Método de tracking del carrier
return_tracking_number
String (nullable)
Número de seguimiento de devolución
service_id
Long
ID del servicio de envío
sender_id
Long
ID del vendedor/emisor
receiver_id
Long
ID del comprador/receptor
customer_id
Long (nullable)
ID del cliente asociado
site_id
String
ID del sitio de Mercado Libre (e.g., MLA, MLB, MPE)
market_place
String
Marketplace
order_cost
BigDecimal
Costo del envío para el vendedor
base_cost
BigDecimal
Costo base del envío sin descuentos/promociones
date_created
ISO8601
Fecha de creación del shipment
last_updated
ISO8601
Fecha de última actualización
date_first_printed
ISO8601 (nullable)
Fecha de primera impresión de etiqueta
created_by
String
Quién creó el shipment
application_id
Long (nullable)
ID de la app cliente que originó el shipment
status_history
Object
Timestamps por cada estado: date_handling, date_ready_to_ship, date_shipped, date_first_visit, date_delivered, date_not_delivered, date_returned, date_cancelled
substatus_history
Array
Historial de cambios de substatus con {status, substatus, date}
shipping_items
Array
Items incluidos en el envío con id, description, quantity, dimensions, user_product_id, sender_id
shipping_option
Object
Opción de envío con id, name, shipping_method_id, cost, list_cost, currency_id, delivery_type, estimaciones de entrega
sender_address
Object (nullable)
Dirección de origen. Sólo presente con ?views=origin
receiver_address
Object (nullable)
Dirección de destino. Sólo presente con ?views=destination. Los campos receiver_name y receiver_phone requieren X-Api-Version: 2
Nota:
Los campos sender_address y receiver_address no fueron eliminados de la vista actual. Para recibirlos, debés agregar explícitamente el parámetro ?views=origin,destination a la llamada. Esto permite aligerar el payload cuando las direcciones completas no son necesarias.
Status Codes
Code
Descripción
200 OK
Shipments encontrados
400 Bad Request
Parámetros inválidos (e.g., order_id no numérico)
401 Unauthorized
Autenticación fallida o caller no identificado
403 Forbidden
Sin permisos suficientes para acceder al recurso
404 Not Found
La orden no existe / La orden no tiene shipments asociados
500 Internal Server Error
Error del servidor
503 Service Unavailable
Servicio no disponible
Consideraciones Técnicas
- Timing de propagación: El shipment se asocia a la orden de manera asíncrona luego de la creación de la misma. Puede haber un breve delay entre que la orden se crea y el shipment aparezca en este recurso.
Calcular el monto total con envío
Con la respuesta que se obtiene en el llamado a
GET /orders/:id y en el
GET /shipments/:shipping_id (con el headerx-format-new: true) debes calcular:
total_amount_with_shipping = total_amount +
taxes.amount + lead_time.cost
*En la misma moneda del ítem.
El total_amount y taxes.amount se obtienen
del recurso /orders, mientras que
lead_time.cost se obtiene de /shipments.
Importante:
En caso de que taxes.currency_id sea distinto a
items.currency_id debemos obtener el ratio de
conversión:
Llamada:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/currency_conversions/search?from=$CURRENCY_ID&to=$CURRENCY_ID
Ejemplo:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/currency_conversions/search?from=ARS&to=BRL
Respuesta:
{
"ratio": 0.0704988
}
Información de los productos en orders
Esta búsqueda muestra toda la información de los productos que están en el
mismo pedido:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/orders/$ORDER_ID/product
Respuesta:
{
"attributes": [
{
"name": "IMEI",
"value": "111",
"id": 1
},
{
"name": "IMEI",
"value": "222",
"id": 2
},
{
"name": "entry_date",
"value": "01/01/2001",
"id": 3
}
]
}
Nota:
Para ver las órdenes dentro de una compra carrito es necesario usar el
recurso
/packs. Ten en cuenta que el recurso /orders puede incluir muchos
productos
de la misma publicación en términos de cantidades.
Obtener descuentos aplicados en una venta
Utiliza el recurso /discounts para revisar los detalles de todos los descuentos que impactaron una venta. Ten en
cuenta que los descuentos pueden venir desde una campaña (promoción), cupón o cashback, y que una venta puede
tener más de un descuento aplicado.
Recuerda que actualmente se guardan órdenes creadas hasta 12 meses y si realizas la búsqueda como vendedor,
filtras órdenes canceladas.
Llamada:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/orders/$ORDER_ID/discounts
Ejemplo:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/orders/2000003508419013/discounts
Respuesta:
{
"details": [
{
"type": "coupon",
"coupon": {
"id": 569290732
},
"supplier": {
"meli_campaign": "P-MLA4944001"
},
"items": [
{
"quantity": 1,
"amounts": {
"total": 446.7,
"seller": 0
},
"id": "MLA922971037"
}
]
},
{
"type": "discount",
"supplier": {
"offer_id": "MLA922971037-abc123",
"funding_mode": "sale_fee"
},
"items": [
{
"quantity": 1,
"amounts": {
"total": 446.7,
"seller": 0
},
"id": "MLA922971037"
}
]
},
{
"type": "cashback",
"items": [
{
"element_id": 1,
"quantity": 1,
"id": "MLB1881365644",
"amounts": {
"total": 5.4,
"seller": 0
}
}
],
"supplier": {
"campaign_id": "10116144"
},
"cashback": {
"id": "2251800174114906"
},
"counter_currency": {
"currency_id": "MCN",
"value": 15.6784541
}
}
]
}
Campos de la respuesta
Cada descuento puede tener dentro del atributo details los siguientes campos dependiendo del type:
- coupon.id: Identificador del cupón.
- supplier: Proveedor de la campaña.
- meli_campaign: Campaña de descuentos asociada al cupón.
- offer_id: Identificador de la oferta, útil para recuperar nombre de
campaña.
- funding_mode: Tipo de promoción obtenida desde IPA. Por ejemplo:
sale_fee.
- ítems: Ítems a los que aplica el cupón.
- id: Identificador del ítem.
- quantity: Cantidad de ítems alcanzados por el descuento.
- amounts: Montos del cupón.
- total: Porción del descuento asociado al ítem (p * q).
- seller: Porción del descuento a cargo del vendedor (p * q).
Nota:
- Ten en cuenta que el recurso /orders/$id/discounts solo incluye descuentos aplicados al precio (excluyendo cargos adicionales y devoluciones posteriores), cupones y cashbacks.
Buscar órdenes
Puedes usar la funcionalidad /search del recurso /orders para realizar
búsquedas con filtros. Ten en cuenta que /search no realiza ninguna acción
si no está seguido por algún filtro.
Recuerda que actualmente se guardan órdenes creadas hasta 12 meses y si
realizas la búsqueda como vendedor, filtras órdenes canceladas.
Llamada:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/orders/search
Filtrar órdenes
Para filtrar tus órdenes con status “paid” cuentas con
los siguientes filtros:
item: ID o título
tags:
puede ser varios estados separados por ','
tags.not: puede ser varios estados separados por ','
q: es un campo genérico que permite buscar por:
- id de la orden
- id del item
- título del ítem
- nickname de la contraparte
order.status: puede ser varios estados separados por ','
order.date_last_updated.from : fecha de la última
modificación de la orden
order.date_last_updated.to: fecha de la última modificación
de la orden
order.date_created.from
order.date_created.to
order.date_closed.from
order.date_closed.to
mediations.stage: puede ser varios estados separados por
','
mediations.status: puede ser varios estados separados por
','
feedback.status: puede ser varios estados separados por ','
feedback.sale.rating: puede ser varios estados separados
por ','
feedback.sale.fulfilled
feedback.purchase.rating: puede ser varios estados
separados por ','
feedback.purchase.fulfilled
Nota:
El filtro “q” no considera los valores first_name, last_name e email
al buscar una orden.
Ejemplo para filtrar órdenes por el status:
curl  -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/orders/search?seller=$SELLER_ID&order.status=paid
Ejemplo para buscar por múltiples criterios:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/orders/search?seller=89660613&q=2032217210
Ejemplo para filtrar órdenes por fecha:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN'  https://api.mercadolibre.com/orders/search?seller=$SELLER_ID&order.date_created.from=2015-07-01T00:00:00.000-00:00&order.date_created.to=2015-07-31T00:00:00.000-00:00
Nota:
Utiliza hasta la hora y descarta la información de los minutos,
segundos y milisegundos.
Ejemplo de respuesta:
{
"query": "2032217210",
"results": [{
"seller": {
"nickname": "VENDASDKMB",
"id": 239432672
},
"payments": [{
"reason": "Kit Com 03 Adesivo Spray 3m 75 Cola Silk Sublimação 300g",
"status_code": null,
"total_paid_amount": 129.95,
"operation_type": "regular_payment",
"transaction_amount": 129.95,
"date_approved": "2019-05-22T03:51:07.000-04:00",
"collector": {
"id": 239432672
},
"coupon_id": null,
"installments": 1,
"authorization_code": "008877",
"taxes_amount": 0,
"id": 4792155710,
"date_last_modified": "2019-05-22T03:51:07.000-04:00",
"coupon_amount": 0,
"available_actions": [
"refund"
],
"shipping_cost": 0,
"installment_amount": 129.95,
"date_created": "2019-05-22T03:51:05.000-04:00",
"activation_uri": null,
"overpaid_amount": 0,
"card_id": 203453778,
"status_detail": "accredited",
"issuer_id": "24",
"payment_method_id": "master",
"payment_type": "credit_card",
"deferred_period": null,
"atm_transfer_reference": {
"transaction_id": "135292",
"company_id": null
},
"site_id": "MLB",
"payer_id": 89660613,
"marketplace_fee": 14.290000000000001,
"order_id": 2000003508419013,
"currency_id": "BRL",
"status": "approved",
"transaction_order_id": null
}],
"fulfilled": true,
"buying_mode": "buy_equals_pay",
"taxes": {
"amount": null,
"currency_id": null
},
"order_request": {
"change": null,
"return": null
},
"feedback": {
"sale": null,
"purchase": null
},
"shipping": {
"id": 27968238880
},
"date_closed": "2019-05-22T03:51:07.000-04:00",
"id": 2032217210,
"manufacturing_ending_date": null,
"order_items": [{
"item": {
"seller_custom_field": null,
"condition": "new",
"category_id": "MLB33383",
"variation_id": null,
"variation_attributes": [],
"seller_sku": null,
"warranty": "Garantia de 1 ano fabricante",
"id": "MLB1054990648",
"title": "Kit Com 03 Adesivo Spray 3m 75 Cola Silk Sublimação 300g"
},
"quantity": 1,
"differential_pricing_id": null,
"sale_fee": 14.29,
"listing_type_id": "gold_special",
"base_currency_id": null,
"unit_price": 129.95,
"base_exchange_rate": null,
"currency_id": "BRL",
"manufacturing_days": null
}],
"date_last_updated": "2020-02-14T02:55:49.811Z",
"last_updated": "2019-05-28T15:16:04.000-04:00",
"comments": null,
"pack_id": null,
"coupon": {
"amount": 0,
"id": null
},
"shipping_cost": 0,
"date_created": "2019-05-22T03:51:05.000-04:00",
"status_detail": null,
"tags": [
"delivered",
"paid"
],
"buyer": {
"id": 89660613
},
"total_amount": 129.95,
"paid_amount": 129.95,
"mediations": [],
"currency_id": "BRL",
"status": "paid"
}],
"sort": {
"id": "date_asc",
"name": "Date ascending"
},
"available_sorts": [{
"id": "date_desc",
"name": "Date descending"
}],
"filters": [],
"paging": {
"total": 1,
"offset": 0,
"limit": 50
},
"display": "complete"
}
Ordenar las órdenes
En este caso deberás agregar “sort” con el ID disponible del orden que
quieras aplicar, por ejemplo: “date_desc”.
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/orders/search?seller=$SELLER_ID&order.status=paid&sort=date_desc
Notas:
Por defecto ya viene con una orden date_asc aplicada.
La fecha por la que se ordena es:
- Sellers por date_closed.
- Buyers por date_created.
Estado de la orden
Los estados de la orden son los siguientes:
confirmed
Estado inicial de un orden; aún sin haber sido pagada.
payment_required
Es necesario que se confirme el pago de la orden necesita para mostrar la
información del usuario.
payment_in_process
Existe un pago relacionado con la orden, pero aún no se
acreditó.
partially_paid La orden tiene un
pago asociado acreditado, pero no es suficiente.
paid La orden tiene un pago asociado acreditado.
partially_refunded  La orden tiene devoluciones parciales
de los pagos.
pending_cancel Cuando se quiere cancelar la orden pero nos
cuesta devolver el pago.
cancelled Por alguna razón, la orden no se
completó.*
Notas:
Una orden puede ser cancelada por los siguiente motivos:
- Se
requería aprobación del pago para descontar el stock,
pero en el tiempo de proceso de aprobación el ítem fue
pausado por falta de stock por lo tanto se devuelve el pago al
comprador.
- Se requería el pago, pero después de
cierto tiempo no se abonó, por eso se cancela
automáticamente.
- Luego de efectuarse una
transacción, por alguna razón el vendedor queda
prohibido en el site.
- Si por alguna razón el vendedor
califica como no concretada la operación, la orden toma el
"status = confirmed". En caso de existir unaprobado este se
devolverá automáticamente. Ten en cuenta, que una orden
que no fue concretada por el vendedor por front se verá como
"Cancelada" y por api quedara con "status: confirmed".
Códigos de error
Error_code
Mensaje de error
Descripción
Posible solución
order_not_found
orden no encontrada.
$order_id incorrecto.
No se puede encontrar la orden; consulta si el order_id es correcto.
empty_order_id
El ID de la orden no puede estar vacío.
$order_id es nulo.
El parámetro order_id no puede ser nulo; consulta el URL utilizado.
invalid_order_id
ID de la orden inválido.
$order_id incorrecto.
El parámetro order_id debe ser un número entero. (Para buscar tus
órdenes consulta este tema).
not_identified_user
Falta de Token.
No existe un Token.
Se deberá enviar un Token.
not_owned_order
El usuario no tiene acceso al orden.
$seller o $buyer incorrectos.
Para ver un orden, tu access_token debe ser generado desde el vendedor
o el comprador.
caller.id.invalid
El caller.id no coincide con el comprador ni el vendedor.
$seller o $buyer incorrectos.
Para ver un orden, debes utilizar un ID del vendedor o del comprador.
feedback_not_found
El feedback no existe.
Error de respuesta.
Consulta si existe feedback para dar una respuesta.
invalid_fulfilled
El parámetro ‘completado’ debe ser verdadero o falso.
Error al dar feedback.
Consulta el parámetro $fulfilled; debe ser booleano (elimina las
comillas) y consulta si el parámetro $reason no es nulo en caso de
$fulfilled: falso.
reply_time_expired
El tiempo de respuesta expiró. Existe un período de 14 días para
responder el feedback.
Error al dar respuesta sobre el feedback.
La respuesta se puede enviar en los 14 días posteriores a la fecha del
feedback.
reply_already_exists
Ya existe respuesta para el feedback.
Error al dar respuesta sobre el feedback.
El feedback soporta una sola respuesta.
Código de respuesta HTTP
Orders podrá devolver el código http 206 cuando no se haya podido obtener
algún dato. Ten en cuenta que en la mayoría de los casos la información que
recibas será suficiente para que puedas seguir trabajando. En el header de
respuesta X-Content-Missing tendrás el nombre de los campos sin información,
que pueden ser "buyer", "feedback", "mediations", "seller" y/o "shipping".
Llamada:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/orders/$ORDER_ID
Respuesta:
< HTTP/1.1 206 Partial Content> X-Content-Missing: buyer, feedback
{
"id": 768570754,
"status": "paid",
"status_detail": null,
"date_created": "2013-05-27T10:01:50.000-04:00",
"date_closed": "2013-05-27T10:04:07.000-04:00",
"order_items": - [
- {
"item": - {
"id": "MLB12345678",
"title": "Samsung Galaxy",
"variation_id": null,
"variation_attributes": [
],
},
"quantity": 1,
"unit_price": 499,
"currency_id": "BRL",
},
],
"total_amount": 499,
"currency_id": "BRL",
"buyer": - { },
},
"seller": - {
"id": "123456789",
"payments": - [
- {
"id": "596707837",
"transaction_amount": 499,
"currency_id": "BRL",
"status": "approved",
"date_created": null,
"date_last_modified": null,
},
],
"feedback": - { },
"shipping": - {
"id": 20676482441
},
"tags": - [
"paid",
"not_delivered",
],
}
Siguiente:
Gestionar órdenes de Carrito.