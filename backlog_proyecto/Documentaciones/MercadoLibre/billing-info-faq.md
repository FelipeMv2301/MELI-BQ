TITLE: Facturación / Billing info

FAQs
›
Facturación / Billing info
Facturación / Billing info
¿Sigue disponible /orders/{order_id}/billing_info para obtener datos fiscales del comprador?
El endpoint legado fue deprecado; ahora se recomienda usar el nuevo flujo: obtener
billing_info.id desde /orders y luego consultar /orders/billing-info/{site_id}/{billing_info_id}.
En la migración se está dejando funcionamiento paralelo por tiempo limitado, por lo que se
debe adaptar el consumo al nuevo endpoint.
Recomendación
Migre integraciones para obtener billing_info.id desde la orden y consultar el nuevo
endpoint /orders/billing-info/{site_id}/{billing_info_id}.
¿Por qué en algunas consultas a billing_info faltan campos como doc_type o doc_number?
En ciertos sitios o para ciertos buyers la API puede no retornar campos de dirección o
identificación por reglas locales (por ejemplo, en Perú el billing_info retornado puede no
incluir zip_code o campos completos). Además, cuando el documento fiscal está en proceso
(PROCESSING) algunos campos pueden quedar nulos hasta la autorización final.
Recomendación
Diseñe lógica que tolere campos nulos y consulte el estado del documento fiscal antes de
depender de datos como doc_type o doc_number.
¿Dónde puedo obtener de forma fiable los detalles de impuestos aplicados a una orden?
Para el detalle de impuestos y descuentos aplicados consulte los endpoints de
facturación/billing (por periodos) y el endpoint de /orders/{order_id}/discounts (según
región). En algunos flujos el breakdown debe calcularse combinando valores de listing_prices
y shipments/costs; no siempre hay un único campo que retorne el total de bonos/descuentos.
Recomendación
Use los endpoints de facturación por periodo y combine listing_prices con shipments/costs
para obtener un desglose completo cuando no exista un campo único.
¿Cuál es el flujo actual para obtener datos fiscales de un buyer (billing info)?
Extraiga billing_info.id desde /orders (buyer.billing_info.id) y luego consulte
/orders/billing-info/{site_id}/{billing_info_id}. El endpoint legacy fue deprecado y debe
migrarse al nuevo recurso.
Recomendación
Actualice integraciones para obtener billing_info a través del nuevo endpoint y evite
depender del recurso legado.
¿Por qué a veces tax_status u otros campos aparecen nulos en la respuesta de facturación?
Cuando el documento fiscal aún está en proceso (PROCESSING) o dependiente de autorización
fiscal, ciertos campos como tax_status o campos de identificación pueden quedar nulos hasta
que la factura sea procesada/authorized. En algunos sitios (ej. Perú) por reglas locales
no se retorna zip_code u otros campos.
Recomendación
Maneje estados intermedios en su lógica y consulte nuevamente cuando el documento fiscal
cambie de estado.
Después de subir una nota fiscal, ¿por qué aparece invoice_pending y la nota no se encuentra aún via API?
Puede haber demora en el procesamiento e ingestión de la factura y en la autorización fiscal
externa; además envíos con Content-Type incorrecto o XML con firma inválida son rechazados,
lo que deja el estado en pending mientras se procesa o se corrige el archivo.
Recomendación
Envíe el XML autorizado con Content-Type=application/xml y verifique la firma digital;
espere el tiempo de ingestión y revise logs de errores si el estado no cambia.
El antiguo endpoint /orders/{order_id}/billing_info devuelve 404; ¿cuál es la alternativa y cómo migrar?
El recurso tradicional fue deprecado. La alternativa es obtener billing_info.id desde la
orden (/orders => buyer.billing_info.id) y luego consultar
/orders/billing-info/{site_id}/{billing_info_id}. La migración implica ajustar consultas
para usar billing_info_id en lugar del endpoint directo anterior.
Recomendación
Cambie la integración para leer billing_info.id desde la orden y usar el nuevo endpoint;
verifique la migración en entornos de prueba.
¿Por qué el endpoint billing-info devuelve una dirección diferente a la dirección de entrega del pedido?
El endpoint /orders/billing-info/{site_id}/{billing_info_id} retorna la dirección fiscal o tributaria del comprador, utilizada para propósitos de facturación. Esta dirección puede diferir de la dirección de entrega del envío, y además puede actualizarse después de la creación del pedido — lo cual es comportamiento esperado de la plataforma. Para obtener la dirección real de entrega logística, se debe consultar el endpoint /shipments/{shipment_id}. Estas son dos fuentes de datos separadas con propósitos distintos y no deben tratarse como equivalentes.
Recomendación
Nunca uses los datos de billing-info como dirección de envío en tu ERP o flujo logístico. Obtén siempre la dirección de entrega desde el endpoint de shipments para garantizar el ruteo correcto y evitar divergencias entre los datos fiscales y los datos logísticos del pedido.