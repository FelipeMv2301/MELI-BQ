TITLE: Notificaciones

Notificaciones
Algunos eventos son producidos solo en el lado de Mercado Libre y la única forma de conocerlos es a través de notificaciones. Con las notificaciones tendrás un feed en tiempo real de los cambios realizados en los diferentes recursos de nuestra API. Por ejemplo, si anunciaste un artículo y luego decidiste pausarlo, si alguien hizo una pregunta, si compraron un artículo o incluso si pagaron y/o solicitaron el envío. Una forma eficiente sin tener que consultar permanentemente nuestra API.
Si quieres comenzar a recibir notificaciones, debes acceder a tu gestor de aplicaciones, donde creaste tu aplicación por primera vez, editar los detalles especificando cuáles son los temas que recibirás. Si aún no has creado tu aplicación, accede a la sección Crear tu aplicación.
Configuración de notificaciones
URL de Retorno de Llamada (Callback URL):
Especifica la URL pública donde el sistema enviará las notificaciones a través de HTTP POST. Esta URL debe ser accesible y estar configurada para recibir datos de los temas seleccionados. Ejemplo: http://myapp.com/notifications.
Tópicos:
Elige los temas de interés para recibir notificaciones específicas. Cada tema corresponde a un tipo de evento en el sistema, y al configurarlos, las notificaciones enviadas estarán restringidas a los eventos de esos temas.
Nota:
Los temas payments y messages no se utilizan para inmuebles, servicios y automóviles.
Las notificaciones tienen zona horaria UTC.
Tópicos
Actualmente, tenemos dos enfoques para la organización de los temas de notificaciones en la plataforma:
Modelo de Tema General: En este modelo, el tema agrupa y envía todas las notificaciones de una entidad, de forma más amplia y unificada, sin la visualización o segmentación de sub-temas. Es decir, no hay una estructura visible de filtros aplicados a esa entidad/tema, y todas las notificaciones se entregan de manera centralizada en una única entidad principal correspondiente a una funcionalidad.
Modelo con Subtemas (tipificado): A diferencia del modelo anterior y con la evolución de nuestra estructura, permitiremos en este nuevo modelo la visualización y organización de las notificaciones en subtemas (o filtros). Así, es posible segmentar las novedades conforme las acciones/atributos/filtros específicos que se apliquen, proporcionando mayor eficiencia, autonomía y control sobre qué notificaciones el usuario desea recibir.
Nota:
Estamos migrando gradualmente la estructura de temas de las notificaciones. Hoy, ya contamos con algunos temas organizados con subtemas (filtros), lo que proporciona mayor organización y control sobre los filtros y los tipos de notificación. A partir de ahora, continuaremos expandiendo esta estructura, permitiendo una segmentación y un uso aún más eficiente de las notificaciones.
Estructura Modelo con Subtópicos:
Entidad principal: Esta es la entidad principal que engloba todos los subtipos de notificaciones de un recurso.
Subtópicos (Filtros): Dentro de la Entidad principal, podrás configurar filtros específicos para segmentar las notificaciones. Cada filtro corresponde a una categoría de notificación.
Flujo de filtros/subtópicos
Cada subtópico puede tener notificaciones asociadas a eventos y acciones específicas. Estas novedades se disparan conforme las actividades que ocurren dentro de Mercado Libre, permitiendo que el integrador siga los cambios relevantes.
El nivel de especificidad de las notificaciones puede ajustarse según el filtro disponible. Esto ofrece al integrador la posibilidad de seleccionar directamente los eventos dentro de un tópico/entidad, pudiendo optar por eventos más específicos de su interés, según la necesidad de control y seguimiento en su integración.
Tópicos disponibles
Órdenes:
orders_v2: recibirás notificaciones desde la creación y modificaciones realizadas en alguna de tus ventas confirmadas. (recomendado)
Respuesta de notificación:
{
"resource":"/orders/2195160686",
"user_id": 468424240,
"topic":"orders_v2",
"application_id": 5503910054141466,
"attempts":1,
"sent":"2019-10-30T16:19:20.129Z",
"received":"2019-10-30T16:19:20.106Z"
}
Con esta información, podrás realizar un GET al recurso orders:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/orders/$ORDER_ID
orders feedback: recibirás notificaciones sobre la creación y modificaciones realizadas en los feedbacks de tus ventas confirmadas.
Messages:
Estructura Modelo con Subtópicos
created: recibirás notificaciones de los nuevos mensajes que se generen, teniendo como destinatario el user_id correspondiente (Comprador o Vendedor).
read: recibirás notificaciones de las lecturas de los mensajes.
Respuesta de notificación:
{
"id": ""5e2827f2-99b7-474e-b68b-6a86e934cc7e",
"resource": "3f6da1e35ac84f70a24af7360d24c7bc",
"user_id": 123456789,
"topic": "messages",
"actions": ["created"], o  ["read"]
"application_id": 89745685555,
"attempts": 1,
"sent": "2017-10-09T13:44:33.006Z",
"received": "2017-10-09T13:44:32.984Z"
}
Con esta información, podrás realizar un GET al recurso mensajes:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/messages/$RESOURCE
Prices:
Sugerencia de precios: recibirás notificaciones sobre las sugerencias de precios en Mercado Libre.
Respuesta de notificación:
{
"resource": "suggestions/items/$ITEM_ID/details”,
"user_id": 318494000,
"topic": "price_suggestion",
"application_id": 22299753060000,
"attempts": 1,
"sent": "2024-05-09T13:44:33.006Z",
"received": "2024-05-09T13:44:32.984Z"
}
Con esta información, podrás realizar un GET al recurso mensajes:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/suggestions/items/$ITEM_ID/details
Items:
Items recibirás notificaciones sobre cualquier cambio en un ítem que hayas publicado.
Respuesta de notificación:
{
"resource": "/items/MLA686791111",
"user_id": 123456789,
"topic": "items",
"application_id": 2069392825111111,
"attempts": 1,
"sent": "2017-10-09T13:44:33.006Z",
"received": "2017-10-09T13:44:32.984Z"
}
Con esta información, podrás realizar un GET al recurso items:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/items/$ITEM_ID
Preguntas: recibirás notificaciones de preguntas y respuestas realizadas.
Respuesta de notificación:
{
"resource": "/questions/5036111111",
"user_id": "123456789",
"topic": "questions",
"application_id": 2069392825111111,
"attempts": 1,
"sent": "2017-10-09T13:51:05.464Z",
"received": "2017-10-09T13:51:05.438Z"
}
Con esta información, podrás realizar un GET al recurso mensajes:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/questions/$QUESTION_ID
Items Price: recibirás notificaciones del item_id cada vez que el precio sea creado, actualizado o eliminado.
Respuesta de notificación:
{
"_id":"f9f08571-1f65-4c46-9e0a-c0f43faas1557e",
"resource": "/items/MLA686791111",
"user_id": 123456789,
"topic": "items",
"application_id": 2069392825111111,
"attempts": 1,
"sent": "2023-02-06T13:44:33.006Z",
"received": "2023-02-06T13:44:32.984Z"
}
Con esta información, puedes realizar un GET al recurso /sale_price:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/items/$ITEM_ID/sale_price?context=$CONTEXT
Ubicación de stock: recibirás notificaciones cuando las ubicaciones de stock del user_product sean modificadas, aumentando o disminuyendo el campo de cantidad.
Respuesta de notificación:
{
"_id": "495cac10-8496-45f8-a6f5-8bff0a948597",
"topic": "stock-location",
"resource": "/user-products/$USER_PRODUCT_ID/stock",
"user_id": 123456789,
"application_id": 213123389095511,
"sent": "2022-09-13T21:06:13.632Z",
"attempts": 4,
"received": "2022-09-13T20:59:13.911Z"
}
Con esta información, podrás realizar un GET al recurso de User product ID:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/user-products/$USER_PRODUCT_ID/stock
Familias de productos del usuario: recibirás notificaciones cuando se modifiquen las familias de los productos del usuario, debido a un cambio en los atributos que impacten en ello.
Catalog:
Competencia de artículos: recibirás notificaciones cuando las publicaciones de catálogo competidoras cambien de estado. Tanto del competidor al ganador y viceversa. "Este tópico está disponible en Argentina, Brasil y México"
Respuesta de notificación>
{
"resource":"/items/ITEM_ID/price_to_win",
"user_id":"123456789",
"topic":"catalog_item_competition_status",
"application_id":4806348059754779,
"attempts":1,
"sent":"2020-03-03T18:57:54.824Z",
"received":"2020-03-03T18:57:54.819Z"
}
Con esta información, podrás realizar un GET para el recurso mensagens:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/items/$ITEM_ID/price_to_win
catalog_suggestions: recibirás notificaciones sobre los cambios de estado de las sugerencias de productos para nuestro catálogo - Brand Central.
Respuesta de notificación:
{  "topic": "catalog_suggestions",
"resource": "/catalog_suggestions/MLA123456",
"user_id": 123456,
"application_id": 5775857146034005,
"attempts": 1,
"recieved": "2021-12-05T17:13:53.617074685Z",
"sent": "2021-12-05T19:22:31.579985295Z"
}
Con esta información, podrás realizar un GET para el recurso de mensajes:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/catalog_suggestions/$SUGGESTION_ID
Shipments:
shipments: recibirás notificaciones a partir de la creación y modificaciones realizadas en los envíos (shippings) de tus ventas confirmadas.
Respuesta de notificación:
{
"resource":"/shipments/40546549876",
"user_id":1234,
"topic":"shipments",
"application_id":12341234,
"attempts":1,
"sent":"2017-10-09T13:58:23.347Z",
"received":"2017-10-09T13:58:23.329Z"
}
Con esta información, podrás realizar un GET al recurso /shipments:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/shipments/$SHIPMENT_ID
Operaciones de stock FBM: notificaciones relacionadas a operaciones de stock del modelo FBM.
Respuesta de notificación:
{
"resource":"/stock/fulfillment/operations/9876",
"user_id":1234,
"topic":"fbm_stock_operations",
"application_id":12341234,
"attempts":1,
"sent":"2017-10-09T13:58:23.347Z",
"received":"2017-10-09T13:58:23.329Z"
}
Con esta información, podrás realizar un GET al recurso /stock/fulfillment/operations:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/$RESOURCE
flex-handshakes: recibirás notificaciones cuando haya transferencias de paquetes entre transportistas y cuando se escaneen por primera vez (cuando se marque como enviado).
Respuesta de notificación:
{
"_id": "495cac10-8496-45f8-a6f5-8bff0a948597",
"topic": "flex-handshakes",
"resource": "/flex/sites/MLA/shipments/407323124706/assignment/v1",
"user_id": 123456789,
"application_id": 213123389095511,
"sent": "2022-09-13T21:06:13.632Z",
"attempts": 4,
"received": "2022-09-13T20:59:13.911Z"
}
Con esta información, podrás realizar un GET al recurso /flex
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN'
https://api.mercadolibre.com/flex/sites/$SITE_ID/shipments/$SHIPMENT_ID/assignment/v1
Promotions:
Public offers: recibirás notificaciones cuando se cree o modifique el estado de una oferta en un artículo.
Respuesta de notificación:
{
"topic": "public_offers",
"resource": "/seller-promotions/offers/1234567",
"user_id": 2222222,
"application_id": 5111111111111,
"attempts": 1,
"recieved": "2022-01-20T17:13:53.617074685Z",
"sent": "2022-01-20T19:22:31.579985295Z"
}
Con esta información, podrás realizar un GET en el recurso /seller-promotions/offers:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/seller-promotions/offers/$OFFERS_ID
Public Candidates:: recibirás notificaciones cuando un artículo sea candidato a una promoción.
Respuesta de notificación:
{
"topic": "public_candidates",
"_id":"f9f08571-1f65-4c46-9e0a-c0f43faas1557e",
"resource": "/seller-promotions/candidates/CANDIDATE-MLA1111111111-11111111",
"user_id": 2222222,
"application_id": 5111111111111,
"attempts": 1,
"recieved": "2021-12-23T17:13:53.617074685Z",
"sent": "2021-12-23T19:22:31.579985295Z"
}
Con esta información, podrás realizar un GET en el recurso /seller-promotions/candidates:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN'  https://api.mercadolibre.com/seller-promotions/candidates/$CANDIDATE_ID
VIS Leads:
Importante:
Como parte de la evolución del flujo de Leads, el tópico “quotations” de Items será deprecado el 13 de agosto de 2026. Además, el envío del e-mail de notificación de cotización asociado a este tópico también será discontinuado el 13 de agosto de 2026. A partir de estas fechas, las notificaciones de cotización pasarán a enviarse exclusivamente por el subtópico “quotation” en el tópico de VIS Leads.
Para evitar la pérdida de notificaciones, recomendamos que realicen la activación del subtópico “quotation” en VIS Leads.
Estructura Modelo con Subtópicos
VIS Leads: Al hacer clic, recibirás notificaciones de todos los subtópicos.
-
WhatsApp: Notifica cuando un comprador presiona el botón de WhatsApp.
-
Call: Notifica cuando un comprador presiona el botón de llamada.
-
Question: Notifica cuando un comprador hace una pregunta.
-
Contact request: Notifica cuando un comprador solicita un contacto.
-
Reservation: Notifica cuando un comprador hace una reserva.
-
Quotations:
Notifica cuando un comprador solicita una cotización del inmueble (si está disponible).
Respuesta de notificación:
{
"_id":"f9f08571-1f65-4c46-9e0a-c0f43faas1557e",
"resource": "/vis/leads/14b52fd8-85dc-11eb-8436-2753cb1f9665",
"user_id": 123456789,
"topic": "vis_leads",
"actions": ["whatsapp"], |  ["call"], | ["question"], | ["visit_request"], | ["contact_request"], |  ["reservation"], |  ["quotations"]
"application_id": 2069392825111111,
"attempts": 1,
"sent": "2024-05-09T13:44:33.006Z",
"received": "2024-05-09T13:44:32.984Z"
}
Con esta información, podrás realizar un GET en el recurso vis_leads:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/vis/leads/$LEAD_ID
Visit_request: Notifica cuando haya una solicitud para agendar una visita en una propiedad.
Respuesta de notificación:
{
"resource": "/vis_leads/93a14ee6-0356-4e20-b0c6-f4ad8f80bkikfff",
"user_id": 123456789,
"actions": ["visit_request"]
}'
Ten en cuenta que las notificaciones de Questions pueden ser generadas por dos flujos: el tópico Items y el VIS_Leads - question. Cuando ambos tópicos están seleccionados, habrá duplicidad en los leads, ya que las notificaciones serán enviadas por ambos los tópicos. Para integraciones VIS, activa solo el tópico VIS_Leads para evitar este problema.
Nota:
-
Para los tipos de leads contact_request y reservation, la consulta debe realizarse a través del endpoint
/leads/$LEAD_ID/details. Actualmente estos leads están disponibles solo para publicaciones de la categoría de Motors.
-
El formulario de preguntas (botón “Preguntar”) permanece activo solo para sellers con "user_type": "car_dealer" que
no poseen número de WhatsApp registrado. De esta forma, el subtópico de Question recibirá notificaciones solo para las publicaciones de la vertical de Automóviles que cumplan con estos criterios específicos.
Post Purchase:
Estructura Modelo con Subtópicos
Claims: Recibirás notificaciones sobre los reclamos que se realicen respecto a las ventas. Ver más sobre cómo trabajar con reclamos.
Claims_actions: Recibirás notificaciones cuando se ejecute una acción sobre la reclamación.
Respuesta de notificación:
{
"id": ""5e2827f2-99b7-474e-b68b-6a86e934cc7e",
"resource": post-purchase/v1/claims/5108684499",
"user_id": 123456789,
"topic": "post_purchase",
"actions": ["claims"], o  ["claims_actions"]
"application_id": 89745685555,
"attempts": 1,
"sent": "2017-10-09T13:44:33.006Z",
"received": "2017-10-09T13:44:32.984Z"
}
Con esta información, deberás realizar un GET en el recurso recibido:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/$resource
Importante:
El campo resource de las notificaciones ahora incluirá el prefijo /post-purchase en el path, que antes no se enviaba.Este cambio puede afectar su integración si no se ajusta para reconocer el nuevo formato. Actualice su implementación para garantizar la compatibilidad.
Others:
payments: recibirás notificaciones cuando se cree un pago en una orden o cuando su estado cambie.
Respuesta de notificación:
{
"resource": "/collections/3043111111",
"user_id": 123456789,
"topic": "payments",
"application_id": 2069392825111111,
"attempts": 1,
"sent": "2017-10-09T13:58:22.081Z",
"received": "2017-10-09T13:58:22.061Z"
}
Con esta información, podrás realizar un GET en el recurso mensajes:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/collections/$PAYMENT_ID
invoices: recibirás notificaciones sobre las facturas generadas a través del Facturador Mercado Libre.
Respuesta de notificación:
{
"resource": "/users/123456789/invoices/$INVOICE_ID",
"user_id": 123456789,
"topic": "invoices",
"application_id": 5503910054141466,
"attempts": 1,
"sent": "2018-03-21T20:51:11.906Z",
"received": "2018-03-21T20:51:11.884Z"
}
Con esta información, podrás obtener los detalles de la factura:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/users/$USER_ID/invoices/$INVOICE_ID
leads credits: recibirás notificaciones relacionadas con créditos aprobados o rechazados en Mercado Libre (aplica a vehículos e inmuebles).
Respuesta de notificación:
{
"_id": "15b0e685-65be-40b6-8d23-alkdjf6465a4f",
"topic": "leads-credits",
"resource": "/vis/loan/66e93589-2d10-11ed-ae7f-0aa30fafa621",
"user_id": 123456789,
"application_id": 874563217565897,
"sent": "2022-09-13T21:03:24.581Z",
"attempts": 2,
"received": "2022-09-13T21:02:22.735Z"
}
Con esta información, podrás realizar un GET en el recurso mensajes:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/vis/loans/$CREDIT_ID?seller_id=$SELLER_ID
¿Qué eventos disparan notificaciones?
Ten en cuenta que cualquier cambio que ocurra en el JSON, en cualquier tema, disparará las notificaciones correspondientes a estos.
Es importante que siempre escuches las notificaciones y, luego, hagas la consulta en el recurso correspondiente para verificar si hay algún cambio respecto a tu aplicación, ya que los cambios también pueden provenir de otras fuentes, como acciones a través del front-end, Seller Central u otras aplicaciones, etc.
Consideraciones Importantes
Importante:
Actualiza tu integración para recibir siempre una respuesta con HTTP 200 y en 500 milisegundos después de recibir la notificación, así evitarás que los temas de tus notificaciones sean desactivados por fall back. Ten en cuenta que si ocurre la desactivación, las notificaciones correspondientes a este período no serán guardadas en "my feeds", y tendrás que suscribirte nuevamente a los tópicos.
- Enviaremos un POST a la URL de callback y tu aplicación deberá confirmar con un HTTP 200 la recepción correcta. De lo contrario, el mensaje se considerará no entregado y se intentará enviar nuevamente.
- Los mensajes serán enviados y nuevos intentos de envío se harán durante un intervalo de 1 hora. Después de este período, si no son aceptados por la aplicación, serán eliminados.
- Dado que puede haber una gran cantidad de notificaciones, se recomienda trabajar con colas, donde tu servidor debe confirmar la recepción de las notificaciones (HTTP 200) instantáneamente y solo después realizar la consulta del tema en la API; de esta forma evitarás nuevos intentos de notificación y no generará la sensación de notificaciones duplicadas.
- Ten en cuenta que existen eventos internos no visibles para el integrador, pero estos disparan notificaciones.
Cómo consultar las notificaciones
Cuando recibas una notificación sobre un tema, necesitarás realizar una solicitud GET al recurso indicado para obtener los detalles completos. Si has guardado una versión anterior del JSON, es importante compararla con la nueva respuesta para identificar cambios.
Estructura de Notificación tema general:
Las notificaciones tienen una estructura uniforme, lo que facilita el acceso y el análisis de los datos:
{
"_id": "id_unico",
"resource": "/camino_del_recurso",
"user_id": "id_del_usuario",
"topic": "tema",
"application_id": "id_de_la_aplicación",
"attempts": numero_intentos,
"sent": "timestamp_envio",
"received": "timestamp_recepcion"
}
Cómo Acceder al Recurso:
- Identifica el resource: El campo resource en la notificación indica la URL a la que debes hacer la solicitud GET.
- Determina el topic: El campo topic indica el tipo de recurso (por ejemplo, items, orders, claims).
- Realiza la Solicitud GET: Basado en el resource, envía una solicitud GET para acceder a los detalles completos del recurso.
Ejemplo de Respuesta de Notificación: Tema general:
{
"_id": "f9f08571-1f65-4c46-9e0a-c0f43faa1557e",
"resource": "/items/MLA686791111",
"user_id": 123456789,
"topic": "items",
"application_id": 2069392825111111,
"attempts": 1,
"sent": "2025-01-21T13:44:33.006Z",
"received": "2025-01-21T13:44:32.984Z"
}
Basado en el resource proporcionado, necesitas hacer una solicitud GET para obtener los detalles del recurso. Aquí está cómo se haría:
Llamada:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/items/$ITEM_ID
Respuesta:
{
"id": "MLA686791111",
"title": "Producto Ejemplo",
"price": 100.0,
"currency_id": "BRL",
"available_quantity": 10,
"sold_quantity": 2,
"status": "active"
}
Ejemplo de Respuesta de Notificación: Estructura Modelo con Subtemas
{
"id": "aaa123bbbbb",
"resource": "/vis_leads/93a14ee6-0356-4e20-b0c6-f4ad8f80bfff",
"user_id": 123456789,
"topic": "vis_leads",
"actions": ["visit_request"],
"application_id": 1111111111111111111,
"attempts": 1,
"sent": "2017-10-09T13:44:33.006Z",
"received": "2017-10-09T13:44:32.984Z"
}
Nota:
En esta estructura, vemos el detalle del filtro o tipo de novedad en el array de “actions”, demostrando a qué se refiere esta notificación dentro de una entidad/recurso.
Basado en el resource proporcionado, necesitas hacer una solicitud GET para obtener los detalles del recurso:
Llamada:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN'
'https://api.mercadolibre.com/vis/users/$USER_ID/leads'
Nota:
Con estos detalles, puedes actualizar o procesar la información según sea necesario en tu aplicación.
Prueba tus notificaciones
Puedes verificar si estás recibiendo notificaciones en tu integración, importando este enlace en Postman. Si tu URL funciona correctamente, recibirás una respuesta con el código 200 status ok, como se muestra en la imagen a continuación.
Historial de notificaciones
Importante:
La API de missed_feeds solo guarda las notificaciones perdidas de hasta 2 días atrás. Después de este plazo, las notificaciones ya no estarán disponibles.Si necesitas información más antigua, es recomendable almacenarla o registrarla antes de que expire el plazo.
Verifica el historial de notificaciones perdidas para esos temas, haciendo un GET al siguiente endpoint:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/missed_feeds?app_id=$APP_ID
Nota:
La respuesta contendrá información sobre las notificaciones que, después de ocho intentos (1 hora), no hayan recibido el código http 200, es decir, consideraremos la notificación como perdida.
Si estás utilizando algún tipo de filtro en tu aplicación, desde Mercado Libre generaremos notificaciones con las siguientes direcciones IP:
- 54.88.218.97
- 18.215.140.160
- 18.213.114.129
- 18.206.34.84
- 35.236.253.169
- 35.245.91.34
- 35.245.20.104
- 35.186.182.146
Ejemplo:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/missed_feeds?app_id=3486171129139063
Respuesta:
{
"messages": [
{
"_id": "5da8a1b24be30a49eb66c52a",
"resource": "a35cf79864a845ca9a3bf6aee59bb4d7",
"user_id": 465432224,
"topic": "messages",
"application_id": 3486171129139063,
"attempts": 5,
"sent": "2019-10-17T17:15:30.279Z",
"received": "2019-10-17T17:15:30.259Z",
"request": {
"url": "https://YOUR_URL",
"headers": {
"accept": "application/json",
"content-type": "application/json",
"content-length": 207
},
"data": "{\"resource\":\"a35cf79864a845ca9a3bf6aee59bb4d7\",\"user_id\":\"465432224\",\"topic\":\"messages\",\"application_id\":3486171129139063,\"attempts\":1,\"sent\":\"2019-10-17T17:15:30.279Z\",\"received\":\"2019-10-17T17:15:30.259Z\"}"
},
"response": {
"req_time": 260,
"http_code": 400,
"body": "[object Object]",
"headers": {
"date": "Thu, 17 Oct 2019 17:15:30 GMT",
"content-length": "141",
"content-type": "text/plain; charset=utf-8",
"connection": "close"
}
}
},
{
"_id": "5da87eea5b35b865994cfd7d",
"resource": "/items/MLA820048955",
"user_id": 468424240,
"topic": "items",
"application_id": 3486171129139063,
"attempts": 5,
"sent": "2019-10-17T14:47:06.414Z",
"received": "2019-10-17T14:47:06.375Z",
"request": {
"url": "https://YOUR_URL",
"headers": {
"accept": "application/json",
"content-type": "application/json",
"content-length": 189
},
"data": "{\"resource\":\"/items/MLA820048955\",\"user_id\":468424240,\"topic\":\"items\",\"application_id\":3486171129139063,\"attempts\":1,\"sent\":\"2019-10-17T14:47:06.414Z\",\"received\":\"2019-10-17T14:47:06.375Z\"}"
},
"response": {
"req_time": 498,
"http_code": 200,
"body": "[object Object]",
"headers": {
"content-type": "application/json; charset=utf-8",
"date": "Thu, 17 Oct 2019 14:47:06 GMT",
"content-length": "190",
"connection": "close"
}
}
}
}
Campos del recurso
resource: recurso completo, con el tema por el cual se generó la notificación.
user_id: usuario que lo generó.
topic: tema de referencia de la notificación.
request: consulta realizada a la URL de las notificaciones, junto con sus respectivas URL, encabezado y datos.
response: respuesta del servidor que está recibiendo la notificación.
http_code: código HTTP devuelto por este servidor. Para que no intente nuevamente, debes enviar un 200.
Filtro por tema
Existe la posibilidad de filtrar por tema, lo cual es muy útil cuando tienes un gran número de notificaciones.
Llamada:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/missed_feeds?app_id=$APP_ID&topic=$TOPIC
Ejemplo:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/missed_feeds?app_id=3486171129139063&topic=payments
Nota:
De forma predeterminada, solo se mostrarán 10 notificaciones, sin embargo, puedes utilizar LIMIT y OFFSET para modificar el número que deseas recibir, como se muestra a continuación:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/missed_feeds?app_id=$APP_ID&offset=1&limit=5