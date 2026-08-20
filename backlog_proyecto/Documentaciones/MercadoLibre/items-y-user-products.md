# Items, User Products y Stock — Mercado Libre API

Fuente: guías "User Products" / "Stock distribuido" / "Stock Multi Origen" de
`developers.mercadolibre.com.ar` (pegadas por Felipe, leídas 2026-08-20).

## Dos modelos de item coexisten

**Legacy** (la mayoría de sellers hoy): un item tiene `price`, `available_quantity` y un array
`variations[]` con el detalle de cada variante.

**User Products (UP)** — modelo nuevo, se activa por seller con el tag `user_product_seller` en
`GET /users/$USER_ID`:
- El array `variations` **deja de existir** — cada variante es un `item_id` propio.
- Cada item tiene un `user_product_id` (UP) — representa el producto físico.
- Varios `user_product_id` con las mismas características "padre" (marca/modelo/etc., los atributos
  `PARENT_PK`) forman una **familia** (`family_id`/`family_name`).
- El **precio sigue siendo a nivel de item** (condición de venta) — no cambia respecto al legacy.
- El **título** del item ya no lo define el vendedor — ML lo genera a partir de `family_name` +
  atributos.

**Detección necesaria antes de publicar/actualizar (HU-CM0.3):**
```
GET /users/$USER_ID  →  tags: [..., "user_product_seller", "warehouse_management", "multiwarehouse"]
```

## Publicación (legacy, caso simple sin multiorigen)

```
POST /items
{
  "title": "...", "category_id": "...", "price": 1000, "currency_id": "CLP",
  "available_quantity": 10, "buying_mode": "buy_it_now", "listing_type_id": "gold_special",
  "condition": "new", "pictures": [...], "attributes": [...]
}
```

## Actualización de stock/precio — TRES escenarios distintos

1. **Sin multiorigen (caso probable de bioquimica.cl para el MVP):**
   ```
   PUT /items/$ITEM_ID
   { "available_quantity": 6 }        # stock
   { "price": 1000 }                  # precio
   ```
   Si el seller ya está en modelo User Products, ML replica el cambio de forma asíncrona a todos
   los items del mismo `user_product_id` — no hay que hacerlo manualmente.

2. **Full/Flex con stock distribuido, sin multiorigen (MLA/MLC):**
   ```
   PUT /user-products/$USER_PRODUCT_ID/stock/type/selling_address
   Header: x-version: <valor obtenido de un GET previo>
   ```

3. **Multiorigen activo** (tags `warehouse_management` + `multiwarehouse`):
   ```
   GET /user-products/$USER_PRODUCT_ID/stock   → devuelve locations[] + header x-version
   PUT /user-products/$USER_PRODUCT_ID/stock/type/seller_warehouse
   Header: x-version: <el mismo valor recién leído>
   { "locations": [{"store_id": "...", "network_node_id": "...", "quantity": 10}, ...] }
   ```
   - `x-version` es **obligatorio** — sin él, 400. Si quedó desactualizado, 409 (`Version mismatch`)
     → hay que volver a hacer `GET` y reintentar con el valor nuevo.
   - Un seller con **un solo depósito** no puede operar sobre más de un `network_node_id` a la vez
     en el mismo request (error 400 explícito si se mezclan).

**Para el MVP de MELI-BQ:** lo más probable es que bioquimica.cl esté en el escenario 1 (legacy o
UP sin multiorigen) — confirmar con el resultado real de HU-CM0.3 antes de asumirlo.

## Comportamiento automático a favor (no hay que replicarlo)

- Una publicación se **pausa sola** cuando `available_quantity`/stock llega a 0.
- Se **reactiva sola** al recibir una cantidad > 0.
- No hay que gestionar `status: paused/active` manualmente por causa de stock.

## Notificaciones relevantes para este módulo

- Topic `items` — cualquier cambio en un item publicado (incluye cambios de precio).
- Topic `stock-location` — cambios en las ubicaciones de stock de un `user_product` (modelo
  multiorigen): `resource: "/user-products/$USER_PRODUCT_ID/stock"`.

## Fuera de alcance para MELI-BQ (no confundir, no implementar)

- **Precio por cantidad B2C/B2B** (`price_per_quantity`, dominio neumóticos/mayorista) — no aplica
  al catálogo de bioquímica.cl (reactivos/equipos de laboratorio).
- **Precios netos por cantidad** — exclusivo Brasil, régimen tributario normal.
- **UPtin / migración de ítems con variaciones al modelo UP** — no es algo que este proyecto dispare,
  es una migración que hace el propio seller/ML; el proyecto solo debe *detectar* en qué modelo está
  el seller (HU-CM0.3), no migrarlo.
