# Backlog — Módulo 2: Facturación de ventas Mercado Libre en SAP

> Estado: **Sin codear, en espera.** Ver `plan-integracion-mercadolibre.md` para arquitectura y
> spikes. Referencia técnica completa del patrón a replicar: `C:\Users\920562\Documents\proyectos\BQ-Integraciones`
> (pipelines `customers.py`, `billing.py`, `documents.py`, `notifications.py`, `orchestrator.py`).

## 1. Objetivo

Que cada venta confirmada en Mercado Libre genere automáticamente su boleta o factura en SAP, con
los datos del comprador correctos y el PDF enviado por correo — mismo resultado final que ya logra
`BQ-Integraciones` para WooCommerce, cambiando la fuente de datos del pedido.

## 2. Reuso de BQ-Integraciones (aprender de lo que ya existe)

**No reescribir el patrón de facturación.** Es el mismo chain de 5 pasos, solo cambia el origen:

- `resolve_customer()` — mismo cliente `services/sap/customers.py`, mismo modelo `SAPCustomer`
  (RUT/BP). Cambia únicamente `construir_datos_cliente()`: en vez de leer `woo_order.billing_address`,
  lee `buyer.billing_info` de la orden ML (`/orders/billing-info/{site_id}/{billing_info_id}`).
- `prepare_billing()` — mismo troceo en lotes ≤21, misma resolución de SKU/bodega contra
  Stock-Service (`_resolver_sku_bodega`). Cambia el origen de `items`: `order_items` de ML en vez de
  `line_items` de WooCommerce.
- `create_sap_invoice()` — sin cambios de fondo; solo cambia cómo se llena `doc_type_code` (ver
  HU-FM2.3, no viene de un campo directo como en Woo).
- `fetch_pdf()`/`send_email()` — **sin cambios**, se reusa tal cual `services/facele/client.py` y
  el pipeline de `notifications.py` de `BQ-Integraciones`.
- El orquestador (`orchestrator.py`: dos chains, reintentos de `FAILED` además de `PENDING`,
  escalado a `EXHAUSTED` vía `failure_tracking`) se porta igual, cambiando `WooOrder` por `MLOrder`
  como entrada de la Chain A.

## 3. Decisiones y Spikes abiertos (resolver con Felipe antes de codear lo que dependa)

| ID | Pregunta | Bloquea |
|---|---|---|
| SPK-MELI-3 | Mapeo boleta(39)/factura(33) para MLC — sin tabla publicada por ML (sí existe para MLA/MPE) y sin caso real de una orden con factura para confirmar cómo se ve `cust_type`/`billing_info` en ese caso. | HU-FM2.3 |
| SPK-MELI-9 | ¿Ingesta por notificación webhook (`orders_v2`, tiempo real) o por polling (`GET /orders/search`, más simple pero con latencia)? BQ-Integraciones usa polling para Woo — definir si acá conviene igual o vale la pena el webhook desde el inicio. | HU-FM1.1 |
| SPK-MELI-10 | ¿Cómo se determina que una orden ML ya está "pagada y lista para facturar"? En Woo es el estado `processing`. En ML hay que confirmar el `status`/`tags` equivalente (`paid`, sin `fraud_risk_detected`, sin cancelación). | HU-FM1.1 |
| SPK-MELI-11 | Comuna/región del comprador viene en `billing_info.address.state`/`city_name` como texto libre, no como código — construir la tabla de mapeo a `Municipality` de SAP (equivalente a la que ya existe por `woo_code` en BQ-Integraciones) requiere ver ejemplos reales de direcciones ML. | HU-FM2.1 |
| SPK-MELI-12 | El envío de una venta ML lo gestiona Mercado Envíos, no bioquimica.cl — ¿el costo de envío entra a la factura como línea propia (igual `_item_envio` de BQ-Integraciones) o el envío nunca es parte del monto a facturar en el caso ML? Depende de qué le llega cobrado al vendedor. | HU-FM2.2 |

## 4. Fases

1. **Fase 1 — Ingesta de órdenes**: traer ventas pagadas de ML y guardarlas como `MLOrder`.
2. **Fase 2 — Cliente y facturación**: resolver el Business Partner en SAP y crear la boleta/factura.
3. **Fase 3 — PDF y notificación**: obtener el PDF de Facele/Docele y enviarlo por correo.
4. **Fase 4 — Orquestación y operación**: chains automáticas, reintentos, panel de estado.

## 5. Backlog

| ID | Épica | Tipo | Rol | Título | Como (rol) | Quiero | Para | Criterios de aceptación | Fase | Prioridad | Estado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| HU-FM1.1 | F1 - Ingesta | Historia técnica | Equipo de desarrollo | Traer órdenes pagadas de ML | equipo de desarrollo | crear `ml_client.py::obtener_ordenes_pagadas()` sobre `GET /orders/search` (o el webhook `orders_v2`, según SPK-MELI-9) | tener el universo de ventas a facturar, deduplicado contra `MLOrder` existente | • Filtra por el criterio resuelto en SPK-MELI-10 (status "lista para facturar").<br>• Dedup por `code` (id de ML), mismo criterio que `poll_woo_orders` de BQ-Integraciones.<br>• Circuit breaker de volumen (I3 de BQ-Integraciones): si el lote de nuevas órdenes supera un umbral, alerta pero no aborta. | F1 | Alta | Por hacer |
| HU-FM1.2 | F1 - Ingesta | Historia técnica | Equipo de desarrollo | Modelo `MLOrder` | equipo de desarrollo | persistir snapshot inmutable de la orden (`code`, `total`, `paid_at`, `order_items`, `billing_info_id`, `shipping_id`, tags) | tener la misma base de auditoría que `WooOrder` — de qué pedido salió cada factura | • JSON crudo de `order_items` y `billing_info` (no normalizado, igual criterio que `WooOrder.items`/`billing_address`).<br>• `SyncStatusMixin` igual que el resto de tablas de trabajo del proyecto (status/attempts/status_message). | F1 | Alta | Por hacer |
| HU-FM2.1 | F2 - Cliente y facturación | Historia técnica | Equipo de desarrollo | `construir_datos_cliente()` desde `billing_info` de ML | equipo de desarrollo | armar el dict que espera `resolve_customer()` a partir de `buyer.billing_info` en vez de `woo_order.billing_address` | reusar `resolve_customer()` sin modificarlo — solo cambia el adaptador de entrada | • RUT desde `identification.number` (site MLC).<br>• Nombre: `name` (razón social si `cust_type=BU`) o `name + last_name` (si `CO`) — mismo criterio que Woo (nunca ambos).<br>• Comuna/región resuelta contra la tabla de mapeo de SPK-MELI-11 — sin mapeo, `PermanentError` explícito (no inventar un valor). | F2 | Alta | Por hacer |
| HU-FM2.2 | F2 - Cliente y facturación | Historia técnica | Equipo de desarrollo | `prepare_billing()` desde `order_items` de ML | equipo de desarrollo | trocear `order_items` en lotes ≤21, resolviendo SKU/bodega contra Stock-Service igual que hoy | tener el `SAPBillingML` listo para facturar, con el mismo control de discrepancia de totales que BQ-Integraciones | • Reusa `_resolver_sku_bodega`/`_trocear` de BQ-Integraciones tal cual (mismo `Stock-Service`).<br>• Envío: según SPK-MELI-12, o se agrega como línea (`_item_envio`) o se excluye del total a facturar. | F2 | Alta | Por hacer |
| HU-FM2.3 | F2 - Cliente y facturación | Historia técnica | Equipo de desarrollo | `decidir_doc_type()` — boleta vs factura | equipo de desarrollo | inferir `doc_type_code` (33/39) a partir de `billing_info` presente/ausente + `attributes.cust_type` | que `create_sap_invoice()` reciba el mismo `doc_type_code` que ya sabe consumir (sin tocar esa función) | • Sin `billing_info` en la orden → boleta (39).<br>• Con `billing_info` y `cust_type=BU` → factura (33).<br>• Con `billing_info` y `cust_type=CO` → **depende de SPK-MELI-3**, no cerrar esta historia sin resolverlo — placeholder por defecto: boleta (39), documentado como supuesto a validar. | F2 | Alta | Por hacer |
| HU-FM2.4 | F2 - Cliente y facturación | Historia técnica | Equipo de desarrollo | `create_sap_invoice()` para `SAPBillingML` | equipo de desarrollo | reusar la lógica de `BillingPayload.build`/`create_sap_invoice` de `services/sap/billing.py`, apuntando a `SAPBillingML` en vez de `SAPBilling` | no duplicar la integración con SAP — solo el modelo de origen cambia | • Idempotente igual que BQ-Integraciones: si SAP ya tiene la factura para ese `order_num`/total/`doc_type_code`, la adopta en vez de duplicar.<br>• `pay_auth_code`: usar el `id` del pago de ML (`payments[].id`) en vez de `transaction_id` de Woo. | F2 | Alta | Por hacer |
| HU-FM3.1 | F3 - PDF y notificación | Historia técnica | Equipo de desarrollo | `fetch_pdf()` para `SAPInvoiceML` | equipo de desarrollo | reusar `services/facele/client.py` tal cual, sin cambios | obtener el PDF de la boleta/factura ya emitida | • Cero cambios de código respecto a BQ-Integraciones — el cliente Facele/Docele no sabe ni le importa si el origen fue Woo o ML. | F3 | Alta | Por hacer |
| HU-FM3.2 | F3 - PDF y notificación | Historia técnica | Equipo de desarrollo | Envío de correo al comprador ML | equipo de desarrollo | adaptar `notifications.py::prepare_email`/`send_email` para tomar el email del comprador desde `billing_info.attributes`/datos de la orden ML | que el comprador reciba su boleta/factura igual que un cliente de la tienda web | • Mismo comportamiento en `ENVIRONMENT=development` (redirige a `ALERT_EMAILS` con `[PRUEBA]`) que ya tiene BQ-Integraciones — no mandar correos de prueba a compradores reales. | F3 | Media | Por hacer |
| HU-FM4.1 | F4 - Orquestación | Historia técnica | Equipo de desarrollo | Orquestador Chain A (orden → SAP) | equipo de desarrollo | portar `procesar_pedidos_pendientes`/`_procesar_pedido` de BQ-Integraciones reemplazando `WooOrder` por `MLOrder` | tener el mismo ciclo automático (Beat/scheduler) que ya funciona para Woo | • Reintenta `FAILED` además de `PENDING` (mismo criterio I6).<br>• Escala a `EXHAUSTED` vía `failure_tracking` al agotar intentos — deja de reintentarse solo. | F4 | Alta | Por hacer |
| HU-FM4.2 | F4 - Orquestación | Historia técnica | Equipo de desarrollo | Orquestador Chain B (folio → PDF → email) | equipo de desarrollo | portar `procesar_facturas_pendientes`/`_procesar_factura` sin cambios de lógica, solo de modelo (`SAPInvoiceML`) | separar el ciclo de "ya facturado, falta PDF/correo" del ciclo de "falta facturar" | • Mismo criterio de dos grupos que BQ-Integraciones (sin PDF vs con PDF pero sin correo). | F4 | Alta | Por hacer |
| HU-FM4.3 | F4 - Orquestación | Historia | Logística | Endpoint/vista de sync manual de una orden puntual | Logística | forzar la facturación de una orden ML específica para pruebas dirigidas o corrección de un caso puntual | no depender del ciclo automático para un caso urgente | • Mismo rol que `POST /pipeline/sync-order/{code}` de BQ-Integraciones, adaptado a vista Django.<br>• Nunca devuelve un error opaco — cualquier falla queda descrita en la respuesta, igual criterio que el original. | F4 | Media | Por hacer |
| HU-FM4.4 | F4 - Orquestación | Historia | Logística | Panel de estado y reintento manual | Logística | ver órdenes ML pendientes/falladas de facturar y reintentar una puntual | operar el módulo sin acceso directo a la base de datos | • Mismo rol que `/status` + `/retry/{tabla}/{id}` de BQ-Integraciones. | F4 | Baja | Por hacer |

## 6. Notas

- MVP realista: HU-FM1.1/1.2 (ingesta) + HU-FM2.1 a HU-FM2.4 (cliente + facturación) + HU-FM3.1/3.2
  (PDF + correo). Fase 4 (orquestación automática + panel) puede diferirse usando el endpoint manual
  de HU-FM4.3 como puente mientras se valida el flujo con órdenes reales.
- **HU-FM2.3 es la historia de mayor riesgo** — depende de un spike sin resolver (SPK-MELI-3) por
  falta de un caso real. No cerrar esta historia con un supuesto sin dejarlo documentado y visible
  (log/alerta) para que el primer caso real de factura en MLC se detecte y valide a mano.
- Los spikes SPK-MELI-3/9/10/11/12 se resuelven **antes** de codear la historia que dependa de ellos
  — mismo criterio que el backlog de Starken en `gestorBQ`.
