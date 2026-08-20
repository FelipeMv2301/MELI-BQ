TITLE: Datos de Facturación

Datos de Facturación
Para realizar el facturamiento de una venta, es necesario obtener los datos fiscales del comprador a través de la API /orders/billing-info/$SITE_ID/$BILLING_INFO.ID
Obteniendo o BILLING_INFO_ID
Obtén el billing_info_id disponibilizado en el pedido utilizando la API /orders/$ORDER_ID
Llamada:
curl -X GET \
-H 'Authorization: Bearer $ACCESS_TOKEN' \
https://api.mercadolibre.com/orders/$ORDER_ID
Ejemplo:
curl -X GET \
-H 'Authorization: Bearer $ACCESS_TOKEN' \
https://api.mercadolibre.com/orders/2000010733434062
Respuesta:
{
"id": 2000010733434062,
...
"buyer": {
"id": 2212631646,
"billing_info": {
"id": "677487519924852462"
}
}
...
}
Consultar los datos para facturación
Obtén los datos fiscales del comprador para emisión de la nota fiscal.
Llamada:
curl -X GET \
-H 'Authorization: Bearer $ACCESS_TOKEN' \
https://api.mercadolibre.com/orders/billing-info/$SITE_ID/$BILLING_INFO.ID
Ejemplo:
curl -X GET \
-H 'Authorization: Bearer $ACCESS_TOKEN' \ https://api.mercadolibre.com/orders/billing-info/MLB/677487519924852462
Respuesta con los ejemplos de persona física y jurídica
MLA - Persona Física
{
"site_id":"MLA",
"buyer":{
"cust_id": 123123123,
"billing_info":{
"name":"Juan Soares",
"last_name":"Sanchez",
"identification":{
"type":"DNI" / "CUIL",
"number":"307722738"
},
"taxes": {
"taxpayer_type": {
"id": "01",
"description": "Consumidor Final"
}
},
"address":{
"street_name":"Aysen",
"street_number":"30",
"city_name":"Buenos Aires",
"state":{
"code": "01",
"name": "Buenos Aires"
},
"zip_code":"5000",
"country_id":"AR"
},
"attributes": {
"vat_discriminated_billing": "true",
"doc_type_number": "123123123",
"is_normalized": true,
"cust_type": "CO"
}
}
},
"seller":{
"cust_id": 0,
}
}
MLA - Persona Jurídica
{
"site_id":"MLA",
"buyer":{
"cust_id": 123123123,
"billing_info":{
"name":"Apple Argentina",
"identification":{
"type":"CUIT",
"number":"307722738"
},
"taxes": {
"taxpayer_type": {
"description": "IVA Responsable Inscripto"
},
"iibb_number": "901-123456-7"
},
"address":{
"street_name":"Aysen",
"street_number":"30",
"city_name":"Buenos Aires",
"state":{
"code": "01",
"name": "Buenos Aires"
},
"zip_code":"5000",
"country_id":"AR"
},
"attributes": {
"vat_discriminated_billing": "true",
"doc_type_number": "123123123",
"is_normalized": true,
"cust_type": "BU"
}
}
},
"seller":{
"cust_id": 0,
}
}
Nota:
- El campo iibb_number (Ingresos Brutos) es exclusivo de MLA y solo está presente en la respuesta cuando el comprador posee documento CUIT y proporcionó el dato en el checkout. Si el comprador no informó el valor, el campo estará ausente de la respuesta.
Importante:
- El campo invoice_type fue oficialmente removido de las respuestas de la API de Billing Info. La determinación del tipo de factura ahora es responsabilidad total de la lógica del integrador, basada en el documento de identidad del comprador.
- Mapeo obligatorio para MLA: Documento CUIT → Emitir Factura A | Documento DNI → Emitir Factura B.
- Si aún posees lógica dependiente del campo invoice_type, actualiza tu implementación para utilizar el mapeo directo descrito arriba.
- El comprador ya realiza la elección del documento en el checkout según su necesidad fiscal. No es necesario realizar contacto manual para validar el tipo de facturación.
MLB - Persona Física
{
"site_id": "MLB",
"buyer": {
"cust_id": 234343545,
"billing_info": {
"name": "María Lupita",
"last_name": "Gomez Blanco",
"identification": {
"type": "CPF",
"number": "32659430"
},
"address": {
"street_name": "Nicolau de Marcos",
"street_number": "05",
"city_name": "Bom Jardim",
"comment": "7b",
"neighborhood": "Jardim Ornelas",
"state": {
"name": "Rio de Janeiro"
},
"zip_code": "28660000",
"country_id": "BR"
},
"attributes": {
"is_normalized": true,
"cust_type": "CO"
}
}
},
"seller": {
"cust_id": 34345454,
}
}
MLB - Persona Jurídica
{
"site_id": "MLB",
"buyer": {
"cust_id": 234343545,
"billing_info": {
"name": "Apple Brasil",
"identification": {
"type": "CNPJ",
"number": "326594309119203"
},
"taxes": {
"inscriptions":
{
"state_registration": "30703088534",
}
,
"taxpayer_type": {
"description": "Contribuinte"
}
},
"address": {
"street_name": "Nicolau de Marcos",
"street_number": "05",
"city_name": "Bom Jardim",
"comment": "7b",
"neighborhood": "Jardim Ornelas",
"state": {
"name": "Rio de Janeiro"
},
"zip_code": "28660000",
"country_id": "BR"
},
"attributes": {
"is_normalized": true,
"cust_type": "BU"
}
}
},
"seller": {
"cust_id": 34345454,
}
}
MLM - Persona Física
{
"site_id": "MLM",
"buyer": {
"cust_id": 234343545,
"billing_info": {
"name": "Juan Soraes",
"last_name": "Sanchez",
"identification": {
"type": "RFC",
"number": "CUPU800825569"
},
"taxes": {
"contributor": "PERSONA FÍSICA",
"taxpayer_type": {
"id": "606",
"description": "Arrendamiento"
},
"cfdi": {
"id": "G03",
"description": "Gastos en general"
}
},
"address": {
"street_name": "Calle 134A #18A",
"street_number": "05",
"city_name": "Alvaro Obregón",
"state": {
"code": "DIF",
"name": "Distrito Federal"
},
"zip_code": "01040",
"country_id": "MX"
},
"attributes": {
"vat_discriminated_billing": "true",
"birth_date": "2000/02/03",
"is_normalized": true,
"customer_type": "CO"
}
}
},
"seller": {
"cust_id": 34345454
}
}
MLM - Persona Jurídica
{
"site_id": "MLM",
"buyer": {
"cust_id": 234343545,
"billing_info": {
"name": "SALVADO HNOS S A",
"identification": {
"type": "RFC",
"number": "CUPU800825569"
},
"taxes": {
"contributor": "PERSONA MORAL",
"taxpayer_type": {
"id": "606",
"description": "Arrendamiento"
},
"cfdi": {
"id": "G03",
"description": "Gastos en general"
}
},
"address": {
"street_name": "Calle 134A #18A",
"street_number": "05",
"city_name": "Alvaro Obregón",
"state": {
"code": "DIF",
"name": "Distrito Federal"
},
"zip_code": "01040",
"country_id": "MX"
},
"attributes": {
"vat_discriminated_billing": "true",
"birth_date": "2000/02/03",
"is_normalized": true,
"customer_type": "BU"
}
}
},
"seller": {
"cust_id": 34345454,
}
}
Nota:
- Cuando los datos de facturación del comprador indiquen el RFC genérico XAXX010101000, eso significa que el comprador no solicitó una factura nominal. En ese caso, el vendedor tendrá la libertad de decidir si emitirá una factura genérica o una factura global.
MLC - Persona Física
{
"site_id": "MLC",
"buyer": {
"cust_id": 234343545,
"billing_info": {
"name": "Tamara nicolt",
"last_name": "larenas reyes",
"identification": {
"type": "RUT",
"number": "159321126"
},
"address": {
"street_name": "Pasaje Beethoven",
"street_number": "56",
"city_name": "Maipú",
"comment": "73",
"neighborhood": "Maipú",
"state": {
"name": "RM (Metropolitana)"
},
"country_id": "CL"
},
"attributes": {
"is_normalized": true,
"cust_type": "CO"
}
}
},
"seller": {
"cust_id": 34345454,
}
}
MLC - Persona Jurídica
{
"site_id": "MLC",
"buyer": {
"cust_id": 234343545,
"billing_info": {
"name": "Apple",
"identification": {
"type": "RUT",
"number": "159321126"
},
"taxes": {
"economic_activity": "Vta.y arrdo artcls Electrónico",
},
"address": {
"street_name": "Pasaje Beethoven",
"street_number": "56",
"city_name": "Maipú",
"comment": "73",
"neighborhood": "Maipú",
"state": {
"name": "RM (Metropolitana)"
},
"country_id": "CL"
},
"attributes": {
"is_normalized": true,
"cust_type": "BU"
}
}
},
"seller": {
"cust_id": 34345454,
}
}
MCO - Persona Física
{
"site_id": "MCO",
"buyer": {
"cust_id": 234343545,
"billing_info": {
"name": "Adrian",
"last_name": "Garces",
"identification": {
"type": "CC",
"number": "73160000"
},
"address": {
"street_name": "Pasaje Beethoven",
"street_number": "#10-11",
"city_name": "La Candelaria",
"comment": "73",
"neighborhood": "Candelaria",
"state": {
"name": "RM (Metropolitana)",
"code": "CO-DC"
},
"country_id": "CO"
}
}
},
"seller": {
"cust_id": 34345454
}
}
MCO - Persona Jurídica
{
"site_id": "MCO",
"buyer": {
"cust_id": 234343545,
"billing_info": {
"name": "Apple",
"identification": {
"type": "CC",
"number": "73160000"
},
"address": {
"street_name": "Pasaje Beethoven",
"street_number": "#10-11",
"city_name": "La Candelaria",
"comment": "73",
"neighborhood": "Candelaria",
"state": {
"name": "RM (Metropolitana)",
"code": "CO-DC"
},
"country_id": "CO"
},
"attributes": {
"is_normalized": true
}
}
},
"seller": {
"cust_id": 34345454,
}
}
MEC - Persona Física
{
"site_id": "MEC",
"buyer": {
"cust_id": 234343545,
"billing_info": {
"name": "Adrian",
"last_name": "Garces",
"identification": {
"type": "RUC" / "CI",
"number": "1711168979001"
},
"address": {
"country_id": "EC"
},
"attributes": {
"is_normalized": true,
"email": "test_user_937841642@testuser.com"
}
}
},
"seller": {
"cust_id": 34345454,
}
}
MEC - Persona Jurídica
{
"site_id": "MEC",
"buyer": {
"cust_id": 234343545,
"billing_info": {
"name": "Apple",
"identification": {
"type": "RUC",
"number": "1711168979001"
},
"address": {
"country_id": "EC"
},
"attributes": {
"is_normalized": true,
"email": "test_user_937841642@testuser.com"
}
}
},
"seller": {
"cust_id": 34345454,
}
}
MPE - Boleta
{
"buyer": {
"cust_id": "325999999",
"billing_info": {
"name": "Adrian",
"last_name": "Garces",
"identification": {
"type": "DNI || CE",
"number": "70999999"
},
"attributes": {
"normalized": "false",
"is_vat_discriminated_billing": false,
"is_new_billing_info": false,
"cust_type": "CO"
}
}
},
"seller": {
"cust_id": "1469999999"
},
"buyer_id": 325999999,
"seller_id": 1469999999,
"is_order_origin": false
}
MPE - Factura
{
"buyer": {
"cust_id": "325999999",
"billing_info": {
"name": "APPLE",
"identification": {
"type": "RUC",
"number": "01234567891"
},
"attributes": {
"normalized": "false",
"is_vat_discriminated_billing": false,
"is_new_billing_info": false,
"cust_type": "BU"
}
}
},
"seller": {
"cust_id": "1469999999"
},
"buyer_id": 325999999,
"seller_id": 1469999999,
"is_order_origin": false
}
MLU - Persona Física
{
"buyer": {
"cust_id": "1921961891",
"billing_info": {
"name": "Name",
"last_name": "Last",
"identification": {
"type": "CI",
"number": "64856596"
},
"attributes": {
"normalized": "false",
"is_vat_discriminated_billing": false,
"is_new_billing_info": false
},
"address": {
"city": "City Name",
"street_name": "Calle",
"street_number": "123",
"state": {
"name": "Canelones",
"code": "UY-CA"
}
}
}
},
"seller": {
"cust_id": "293733309"
},
"buyer_id": 1921961891,
"seller_id": 293733309,
"is_order_origin": false
}
MLU - Persona Jurídica
{
"buyer": {
"cust_id": "1921961891",
"billing_info": {
"name": "Name",
"identification": {
"type": "RUT",
"number": "215191230015"
},
"attributes": {
"normalized": "false",
"is_vat_discriminated_billing": false,
"is_new_billing_info": false
},
"address": {
"city": "City Name",
"street_name": "Calle",
"street_number": "123",
"state": {
"name": "Canelones",
"code": "UY-CA"
}
}
}
},
"seller": {
"cust_id": "293733309"
},
"buyer_id": 1921961891,
"seller_id": 293733309,
"is_order_origin": false
}
Descripción de los campos de la API
Persona física
- site_id: ID del sitio
- buyer:
- cust_id: ID del comprador
- billing_info:
- name: nombre del comprador
- last_name: apellido del comprador
- identification:
- type: tipo de documento del comprador
- number: número del documento del comprador
- taxes:
- taxpayer_type:
- id: identificador de la situación fiscal
- description: descripción de la situación fiscal del comprador
- inscriptions (MLB):
- state_registration: inscripción estatal del comprador
- iibb_number (MLA): número de Ingresos Brutos del comprador. Presente solo cuando el comprador posee documento CUIT y proporcionó el dato en el checkout
- economic_activity (MLC): actividad económica del comprador
- contributor (MLM): tipo de contribuyente (PERSONA FÍSICA / PERSONA MORAL)
- cfdi (MLM):
- id: código del uso de CFDI
- description: descripción del uso de CFDI
- address:
- street_name: nombre de la calle del comprador
- street_number: número de la dirección del comprador. Valores posibles: cadena, SN para dirección sin número
- city_name: nombre de la ciudad del comprador
- city (MLU): nombre de la ciudad del comprador
- neighborhood: nombre del barrio del comprador
- comment: información adicional sobre la dirección del comprador
- zip_code: código postal del comprador
- state:
- code: código del estado o provincia
- name: nombre del estado o provincia
- country_id: ID del país
- attributes:
- cust_type: tipo de cliente (CO = persona física / BU = persona jurídica)
- customer_type (MLM): tipo de cliente (CO = persona física / BU = persona jurídica)
- is_normalized: indica si la dirección fue normalizada
- normalized (MPE, MLU): indica si la dirección fue normalizada
- vat_discriminated_billing (MLA, MLM): indica si el comprador solicita factura con IVA discriminado
- is_vat_discriminated_billing (MPE, MLU): indica si el comprador solicita factura con IVA discriminado
- doc_type_number (MLA): número del documento del comprador
- birth_date (MLM): fecha de nacimiento del comprador
- email (MEC): correo electrónico del comprador
- is_new_billing_info (MPE, MLU): indica si se trata del nuevo formato de billing info
- seller:
- cust_id: ID del vendedor
- buyer_id (MPE, MLU): ID del comprador a nivel raíz
- seller_id (MPE, MLU): ID del vendedor a nivel raíz
- is_order_origin (MPE, MLU): indica si la solicitud proviene de un pedido
Persona jurídica
La respuesta de persona jurídica comparte la misma estructura que persona física, con las siguientes diferencias:
- name: razón social de la empresa compradora (no se devuelve last_name)
- identification.type: tipo de documento según el sitio:
- MLA: CUIT
- MLB: CNPJ
- MLC / MLU: RUT
- MCO: NIT
- MLM: RFC
- MEC / MPE: RUC
- taxes.taxpayer_type.description: situación fiscal de la entidad. Valores posibles según sitio:
- MLA: Monotributo / IVA Responsable Inscripto / IVA Exento
- MLB: Contribuinte / Não contribuinte
- taxes.inscriptions.state_registration (MLB): inscripción estatal de la empresa
- taxes.economic_activity (MLC): actividad económica de la empresa
- attributes.cust_type: valor BU para persona jurídica
Valores posibles de identification.type:
- Brasil (MLB):
- Persona física: CPF, RG
- Persona jurídica: CNPJ
- Argentina (MLA):
- Persona física: DNI, CUIL
- Persona jurídica: CUIT
- Chile (MLC):
- Persona física: RUT
- Persona jurídica: RUT
- Colombia (MCO):
- Persona física: CC, CE
- Persona jurídica: NIT
- México (MLM):
- Persona física: RFC, CURP
- Persona jurídica: RFC
- Ecuador (MEC):
- Persona física: CI
- Persona jurídica: RUC
- Uruguay (MLU):
- Persona física: CI
- Persona jurídica: RUT
- Perú (MPE):
- Boleta: DNI, CE
- Factura: RUC