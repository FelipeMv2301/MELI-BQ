# Precios — resumen para MELI-BQ

Fuente: guía "Precios de productos" / "Automatizaciones de precios" de
`developers.mercadolibre.com.ar` (pegada por Felipe, leída 2026-08-20). Documento condensado —
el original incluye Precios por cantidad B2C/B2B y Precios netos, **fuera de alcance** (ver
`items-y-user-products.md`, sección "Fuera de alcance").

## Cómo se sigue escribiendo el precio hoy

`price`/`base_price`/`original_price` en `/items` están en **deprecación progresiva** a favor de
`/items/$ID/prices`, pero el endpoint de edición dedicado (`POST /items/$ID/prices/standard`)
**todavía no está disponible en producción** ("Próximamente reemplazará al PUT de ítems"). Mientras
tanto se sigue escribiendo por:
```
PUT /items/$ITEM_ID
{ "price": 1000 }
```

## Gotcha crítico: automatización de precios activa

Si el item tiene **automatización de precio** activa (competencia interna/externa, tag
`dynamic_standard_price`), el comportamiento del PUT cambia **a partir del 18 de marzo de 2026**:

- PUT que solo trae `price` → **400 Bad Request**, rechazado entero:
  ```json
  {"error": "Cannot modify price on items with dynamic pricing", "code": "item.price.not_modifiable", "status": 400}
  ```
- PUT con `price` + otros campos → **200 OK**, pero el `price` se **ignora silenciosamente** y la
  respuesta trae un `warnings[]` explicando por qué.

**Implicancia obligatoria para `push_ml` (HU-CM3.3):** antes de cualquier PUT de precio, verificar
si el item trae el tag `dynamic_standard_price` (o consultar
`GET /pricing-automation/items/$ITEM_ID/automation`). Si está activo, el `MLSyncLog` de ese SKU debe
quedar `SKIPPED` con motivo explícito — nunca `COMPLETED`, porque ML pudo haber ignorado el cambio
sin devolver error.

## Identificar el modelo de precio de un item

```
GET /items/$ITEM_ID/prices
```
Devuelve `prices[]` con `type: "standard"` (precio de lista) o `type: "promotion"` (con promoción
activa), más `version` (para operaciones de escritura futuras que requieran `x-version`).

## Sugerencias de precio (fuera de alcance del MVP, mencionado por completitud)

`GET /suggestions/items/$ITEM_ID/details` da un precio de referencia vs. competencia — no es parte
del cálculo de precio de este proyecto (la regla de precio de MELI-BQ es un % sobre el precio SAP,
ver SPK-MELI-7), pero podría alimentar una alerta futura ("tu precio quedó muy por encima del
sugerido") — no priorizado hoy.
