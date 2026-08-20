TITLE: Envío de Datos Fiscales

Envío de Datos Fiscales
Importante:
Esta funcionalidad está disponible solo en Chile.
Para la facturación automática de los ítems por Mercado Libre, primero el vendedor debe enviar los datos fiscales de los productos.
Enviar datos fiscales
Primero, debes crear las configuraciones fiscales antes de hacer la vinculación con un ítem.
Llamada:
curl -X POST -H 'Authorization: Bearer $ACCESS_TOKEN' -H "Content-Type: application/json" -d
{
"query": "mutation createFiscalInformationMLC($input: CreateFiscalInformationMLCInput!) {\n    createFiscalInformationMLC(input: $input) {\n        sku\n        iva\n        description\n        ila\n\t\tretention\n\t\ttaxCode\n    }\n}",
"variables": {
"input": {
"sku": "String",
"iva": "19",
"description": "String",
"ila": "",
"retention": "14",
"taxCode": "14"
}
}
}
https://api.mercadolibre.com/fiscal_information/graphql
Ejemplo:
curl -X POST -H 'Authorization: Bearer $ACCESS_TOKEN' -H "Content-Type: application/json" -d
{
"query": "mutation createFiscalInformationMLC($input: CreateFiscalInformationMLCInput!) {\n    createFiscalInformationMLC(input: $input) {\n        sku\n        iva\n        description\n        ila\n\t\tretention\n\t\ttaxCode\n    }\n}",
"variables": {
"input": {
"sku": "DOCMLC1",
"iva": "19",
"description": "Tacho De Basura Set De 2, Piezas De12 Litros Marca Begonia",
"ila": "",
"retention": "14",
"taxCode": "14"
}
}
}
https://api.mercadolibre.com/fiscal_information/graphql
Respuesta:
{
"data": {
"createFiscalInformationMLC": {
"sku": "DOCMLC1",
"iva": "19",
"description": "Tacho De Basura Set De 2, Piezas De12 Litros Marca Begonia",
"ila": "",
"retention": "14",
"taxCode": "14"
}
}
}
Configurar datos fiscales por producto/variación
Después de informar los datos fiscales, vincula el ítem a través del SKU:
Llamada:
curl -X POST -H 'Authorization: Bearer $ACCESS_TOKEN' -H "Content-Type: application/json" -d
{
"query": "mutation createFiscalInformationLinkToItem($input: CreateFiscalInformationLinkToItemInput!) {\n    createFiscalInformationLinkToItem(input: $input) {\n        itemId\n        variationId\n        type\n        components {\n            sku\n            quantity\n            percentageShare\n        }\n    }\n}",
"variables": {
"input": {
"itemId": "String",
"variationId": "String",
"components": [
{
"sku": "String",
"quantity": 1,
"percentageShare": 100
}
]
}
}
}
https://api.mercadolibre.com/fiscal_information/graphql
Ejemplo:
curl -X POST -H 'Authorization: Bearer $ACCESS_TOKEN' -H "Content-Type: application/json" -d
{
"query": "mutation createFiscalInformationLinkToItem($input: CreateFiscalInformationLinkToItemInput!) {\n    createFiscalInformationLinkToItem(input: $input) {\n        itemId\n        variationId\n        type\n        components {\n            sku\n            quantity\n            percentageShare\n        }\n    }\n}",
"variables": {
"input": {
"itemId": "MLC1056231867",
"variationId": "175219804700",
"components": [
{
"sku": "DOCMLC1",
"quantity": 1,
"percentageShare": 100
}
]
}
}
}
https://api.mercadolibre.com/fiscal_information/graphql
Respuesta:
{
"data": {
"createFiscalInformationLinkToItem": {
"itemId": "MLC1056231867",
"variationId": "175219804700",
"components": [
{
"sku": "DOCMLC1",
"quantity": 1,
"percentageShare": 100
}
]
}
}
}
Cuando el ítem sea único, el campo variation_id será null.
Enviar y configurar datos fiscales por producto/variación
También se puede hacer el envío de los datos fiscales y vincular al ítem/variación en una llamada única:
Llamada:
curl -X POST -H 'Authorization: Bearer $ACCESS_TOKEN' -H "Content-Type: application/json" -d
{
"query": "mutation($input: CreateOrUpdateFiscalInformationMLCAndLinkToItemInput!) {\n  createOrUpdateFiscalInformationMLCAndLinkToItem(input: $input) {\n    itemId\n    variationId\n    type\n    components {\n      quantity\n      percentageShare\n      fiscalInformation {\n        ... on FiscalInformationMLC {\n          sku\n          iva\n          description\n          ila\n          retention\n          taxCode\n          taxDescription\n        }\n      }\n    }\n  }\n}\n",
"variables": {
"input": {
"itemId": "String",
"variationId": "String",
"components": [
{
"quantity": 1,
"percentageShare": 100,
"sku": "String",
"iva": "19",
"description": "String",
"ila": "",
"retention": "14",
"taxCode": "14"
}
]
}
}
}
https://api.mercadolibre.com/fiscal_information/graphql
Ejemplo:
curl -X POST -H 'Authorization: Bearer $ACCESS_TOKEN' -H "Content-Type: application/json" -d
{
"query": "mutation($input: CreateOrUpdateFiscalInformationMLCAndLinkToItemInput!) {\n  createOrUpdateFiscalInformationMLCAndLinkToItem(input: $input) {\n    itemId\n    variationId\n    type\n    components {\n      quantity\n      percentageShare\n      fiscalInformation {\n        ... on FiscalInformationMLC {\n          sku\n          iva\n          description\n          ila\n          retention\n          taxCode\n          taxDescription\n        }\n      }\n    }\n  }\n}\n",
"variables": {
"input": {
"itemId": "MLC1056231867",
"variationId": "175219804700",
"components": [
{
"quantity": 1,
"percentageShare": 100,
"sku": "DOCMLC1",
"iva": "19",
"description": "Tacho De Basura Set De 2, Piezas De12 Litros Marca Begonia",
"ila": "",
"retention": "14",
"taxCode": "14"
}
]
}
}
}
https://api.mercadolibre.com/fiscal_information/graphql
Respuesta:
{
"data": {
"createOrUpdateFiscalInformationMLCAndLinkToItem": {
"itemId": "MLC1056231867",
"variationId": "175219804700",
"type": "SINGLE",
"components": [
{
"quantity": 1,
"percentageShare": 100,
"fiscalInformation": {
"sku": "DOCMLC1",
"iva": "19",
"description": "Tacho De Basura Set De 2, Piezas De12 Litros Marca Begonia",
"ila": "",
"retention": "14",
"taxCode": "14"
}
}
]
}
}
}
Consultar todos los ítems asociados al SKU
Llamada:
curl -X POST -H 'Authorization: Bearer $ACCESS_TOKEN' -H "Content-Type: application/json" -d
{
"query": "query getAllItemsLinkedBySku($sku: String!) {\n  getAllItemsLinkedBySku(sku: $sku) {\n    itemId\n    variationId\n  }\n}",
"variables": {
"sku": "teste2"
}
}
https://api.mercadolibre.com/fiscal_information/graphql
Ejemplo:
curl -X POST -H 'Authorization: Bearer $ACCESS_TOKEN' -H "Content-Type: application/json" -d
{
"query": "query getAllItemsLinkedBySku($sku: String!) {\n  getAllItemsLinkedBySku(sku: $sku) {\n    itemId\n    variationId\n  }\n}",
"variables": {
"sku": "DOCMLC1"
}
}
https://api.mercadolibre.com/fiscal_information/graphql
Respuesta:
{
"data": {
"getAllItemsLinkedBySku": [
{
"itemId": "MLC1056231867",
"variationId": "175219804700"
}
]
}
}
Consultar datos fiscales por ítem/variación
También puedes buscar las informaciones vinculadas a una publicación en Mercado Libre:
Llamada:
curl -X POST -H 'Authorization: Bearer $ACCESS_TOKEN' -H "Content-Type: application/json" -d
{
"query": "query getFiscalInformationsByItem($itemId: String!, $defaultDataIfNotExists: Boolean, $allVariations: Boolean) {\n    getFiscalInformationsByItem(itemId: $itemId, allVariations: $allVariations, defaultDataIfNotExists: $defaultDataIfNotExists) {\n        itemId\n        variationId\n        type\n        components {\n            sku\n            quantity\n            percentageShare\n            fiscalInformation {\n            ... on FiscalInformationMLC {\n                    sku\n                    iva\n                    description\n                    ila\n                    retention\n                    taxCode\n                    taxDescription\n                }\n            }\n        }\n    }\n}",
"variables": {
"itemId": "String",
"allVariations": true,
"defaultDataIfNotExists": true
}
}
https://api.mercadolibre.com/fiscal_information/graphql
Ejemplo:
curl -X POST -H 'Authorization: Bearer $ACCESS_TOKEN' -H "Content-Type: application/json" -d
{
"query": "query getFiscalInformationsByItem($itemId: String!, $defaultDataIfNotExists: Boolean, $allVariations: Boolean) {\n    getFiscalInformationsByItem(itemId: $itemId, allVariations: $allVariations, defaultDataIfNotExists: $defaultDataIfNotExists) {\n        itemId\n        variationId\n        type\n        components {\n            sku\n            quantity\n            percentageShare\n            fiscalInformation {\n            ... on FiscalInformationMLC {\n                    sku\n                    iva\n                    description\n                    ila\n                    retention\n                    taxCode\n                    taxDescription\n                }\n            }\n        }\n    }\n}",
"variables": {
"itemId": "MLC1056231867",
"allVariations": true,
"defaultDataIfNotExists": true
}
}
https://api.mercadolibre.com/fiscal_information/graphql
Respuesta:
{
"data": {
"getFiscalInformationsByItem": [
{
"itemId": "MLC1056231867",
"variationId": "175219804700",
"type": "SINGLE",
"components": [
{
"sku": "DOCMLC1",
"quantity": 1,
"percentageShare": 100,
"fiscalInformation": {
"sku": "DOCMLC1",
"iva": "19",
"description": "Tacho De Basura Set De 2, Piezas De12 Litros Marca Begonia",
"ila": "",
"retention": "14",
"taxCode": "14",
"taxDescription": "Para Facturas de venta del contribuyente."
}
}
]
}
]
}
}
Estas son las posibles formas de hacer la búsqueda:
- itemId: cuando la publicación no tiene variación.
- itemId + variationId: cuando la publicación tiene variación, para obtener los datos sólo de las variaciones solicitadas.
- itemId + allVariations: cuando la publicación tiene variación, para obtener los datos de todas las variaciones de esta publicación.
Actualizar datos fiscales
El recurso permite la actualización completa o parcial de los datos fiscales de una publicación:
Llamada:
curl -X POST -H 'Authorization: Bearer $ACCESS_TOKEN' -H "Content-Type: application/json" -d
{
"query": "mutation updateFiscalInformationMLC(\n    $where: UpdateFiscalInformationMLCWhere!\n    $input: UpdateFiscalInformationMLCInput!\n) {\n    updateFiscalInformationMLC(where: $where, input: $input) {\n        sku\n        iva\n        description\n        retention\n        ila\n        taxCode\n    }\n}",
"variables": {
"where": {
"sku": "String"
},
"input": {
"iva": "19",
"description": "String",
"retention": "14",
"ila": "",
"taxCode": "14"
}
}
}
https://api.mercadolibre.com/fiscal_information/graphql
Ejemplo:
curl -X POST -H 'Authorization: Bearer $ACCESS_TOKEN' -H "Content-Type: application/json" -d
{
"query": mutation updateFiscalInformationMLC(
$where: UpdateFiscalInformationMLCWhere!
$input: UpdateFiscalInformationMLCInput!) {
updateFiscalInformationMLC(where: $where, input: $input) {
sku
iva
description
ila
retention
taxCode
}
}
"variables": {
"where": {
"sku": "String"
},
"input": {
"iva": "19",
"description": "New description",
"ila": "",
"retention": "14",
"taxCode": "14"
}
}
{
"query": "mutation updateFiscalInformationMLC(\n    $where: UpdateFiscalInformationMLCWhere!\n    $input: UpdateFiscalInformationMLCInput!\n) {\n    updateFiscalInformationMLC(where: $where, input: $input) {\n        sku\n        iva\n        description\n        retention\n        ila\n        taxCode\n    }\n}",
"variables": {
"where": {
"sku": "DOCMLC1"
},
"input": {
"iva": "19",
"description": "New description",
"retention": "14",
"ila": "",
"taxCode": "14"
}
}
}
https://api.mercadolibre.com/fiscal_information/graphql
Respuesta:
{
"data": {
"updateFiscalInformationMLC": {
"sku": "DOCMLC1",
"iva": "19",
"description": "New description",
"ila": "",
"retention": "14",
"taxCode": "14"
}
}
}
Para actualizar parcialmente los datos fiscales, es necesario enviar solamente los campos necesarios en las variables después del input.
Consultar si una publicación puede ser facturada
Este recurso permite identificar si una determinada publicación tiene todos los datos necesarios para que nuestro facturador pueda emitir la factura de venta. Puedes realizar la búsqueda por publicación o por variaciones:
Consulta por publicación:
Llamada:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/can_invoice/items/$ITEM_ID
Ejemplo:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/can_invoice/items/MLC1984512046
Respuesta:
{
"item_id": "MLC1984512046",
"seller_id": "809726122",
"variation_id": "",
"status": true
}
Nota:
Si busca una publicación con variaciones, sólo tendrá el status = true cuando todas las variaciones sean adecuadas. De lo contrario, debe identificar qué variación no tiene datos fiscales o tiene datos incorrectos y cambiarla.
Consulta por variación:
Llamada:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/can_invoice/items/$ITEM_ID/variations/$VARIATION_ID
Ejemplo:
curl -X GET -H 'Authorization: Bearer $ACCESS_TOKEN' https://api.mercadolibre.com/can_invoice/items/MLB1398143045/variations/$VARIATION_ID
Respuesta:
{
"item_id": "MLC1984512046",
"seller_id": "809726122",
"variation_id": "94754627308",
"status": true
}
El campo de estado indica si la publicación está lista para ser facturada.