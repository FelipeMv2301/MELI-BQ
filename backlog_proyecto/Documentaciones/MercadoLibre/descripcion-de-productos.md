# Descripción de productos — Mercado Libre API

Fuente: `developers.mercadolibre.cl/es_ar/descripcion-de-articulos` (leído 2026-08-20).

## Contrato — solo texto plano

```
GET  /items/$ITEM_ID/description
POST /items/$ITEM_ID/description                  # solo si el item NO tiene descripción todavía
PUT  /items/$ITEM_ID/description?api_version=2     # para editar una ya existente
```
Body: `{"plain_text": "..."}`. **Reglas:**
- Nada de HTML, negrita, tamaños ni fuentes — solo texto plano.
- Salto de línea únicamente con `\n`.
- POST sobre un item que ya tiene descripción → `bad request`, hay que usar PUT.
- Caracteres no válidos (ej. emoji) → 400 con `item.description.type.invalid` y la posición exacta
  del carácter (`plain_text[N]`) — usar `?api_version=2` en el PUT para obtener esa posición.

## Por qué esto obliga a limpiar el HTML de WooCommerce

El campo `description` de WooCommerce (confirmado contra un producto real, SKU `ML000111`) trae HTML
semántico: `<h3>`, `<table>` (specs técnicas en filas), `<ul>/<li>`, `<a href>` (a veces apuntando a
PDFs en un hosting de la plataforma anterior, Jumpseller — ya no tiene sentido para el comprador de
ML), `<em>`, entidades HTML (`&#8211;`).

**Transformación necesaria antes de publicar (WooCommerce → ML), en `catalogo_ml/services.py` o
`integraciones/woo_client.py`:**
1. Decodificar entidades HTML (`&#8211;` → `–`, etc.).
2. `<table>` → aplanar fila por fila como texto (`Largo: 180 mm\n`), no concatenar celdas sin
   separador.
3. `<li>` → `- texto\n`.
4. `<h3>`/`<p>`/`<br>` → salto de línea (`\n`), nunca dejar el tag.
5. `<a href="...">texto</a>` → conservar solo el texto visible, **descartar la URL** (un link no
   es clickeable en texto plano de ML, y varios apuntan a un hosting legacy que no debería
   exponerse).
6. Filtrar caracteres fuera del rango aceptado por ML (al menos: sin emoji) — validar con un regex
   conservador antes de mandar, para no depender de que ML devuelva el error y reintentar.
7. Límite de longitud: **no confirmado en la doc leída** — verificar empíricamente con el primer
   POST real (o buscar el límite en la guía completa de publicar un item).

## Fuente y destino de la descripción, por SKU

- WooCommerce trae **dos** campos: `description` (largo, con specs) y `short_description` (resumen
  corto). Sobre 20 productos de muestra, todos tenían ambos poblados (largo ~500-1050 caracteres,
  corto ~120-260).
- Decisión pendiente para el backlog: ¿se publica `description` completo, `short_description`, o
  una combinación? Ver HU-CM2.4 en `backlog-sync-catalogo-ml.md`.
