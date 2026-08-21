# MELI-BQ — Integración Mercado Libre (catálogo + facturación)

> Estado: **Sin codear, en planificación.** Este documento reúne el panorama completo acordado con
> Felipe (sesión 2026-08-20) antes de escribir código. Sigue el mismo criterio que
> `gestorBQ/backlog_proyecto/backlog-integracion-starken.md`: este doc define el *qué* y el *cómo*
> a alto nivel; el detalle de historias vive en `backlog-sync-catalogo-ml.md` y
> `backlog-facturacion-ml.md`; la referencia técnica cruda de la API de Mercado Libre vive en
> `Documentaciones/MercadoLibre/`.

## 1. Objetivo

Dos módulos independientes que comparten proyecto Django, catálogo base (Stock-Service) y cliente
SAP, pero que se pueden construir y desplegar por separado:

1. **Sync de catálogo hacia Mercado Libre** — UI para elegir qué productos publicar/actualizar en
   ML y qué sincronizar de cada uno (stock, precio, o ambos), individual o masivamente. La selección
   persiste y gobierna tanto la publicación inicial como las actualizaciones recurrentes.
2. **Facturación de ventas ML en SAP** — cada venta confirmada en Mercado Libre genera boleta o
   factura en SAP automáticamente, replicando el patrón ya construido en `BQ-Integraciones` para
   WooCommerce.

**No** se sincronizan los ~2000 productos del catálogo a Mercado Libre — solo los que el usuario
seleccione explícitamente. Esa es la razón de ser del Módulo 1: no es un sync total como
Stock-Service→WooCommerce, es un sync *dirigido por selección humana*.

## 2. Por qué Django (decisión tomada)

- El Módulo 1 es, en esencia, una grilla de productos con checkboxes masivos/individuales y guardado
  de configuración — el feature-set de **Django Admin** (`list_editable`, acciones en bloque,
  filtros) sin construir un frontend a mano.
- Felipe ya tiene un proyecto de referencia con el mismo stack funcionando en producción:
  `gestorBQ` (Django 5.2 + templates + HTMX + Tailwind CLI standalone, sin Node/npm). Este proyecto
  copia su estructura, no la reinventa.
- Contraparte: `Stock-Service` y `BQ-Integraciones` son FastAPI + SQLModel + Celery (async) — este
  proyecto rompe esa consistencia de stack a cambio de la velocidad de desarrollo del Admin/templates
  para una herramienta interna. Se acepta el trade-off.

**Stack decidido:**
- Django 5.2 + Django templates (sin DRF — no es API-first, es un portal interno, igual que gestorBQ)
- HTMX (vendorizado en `static/vendor/`, sin CDN) para las interacciones de la grilla de selección
- Tailwind CLI standalone (sin Node/npm, mismo binario que gestorBQ) para estilos
- Scheduler: por definir entre **APScheduler** (igual gestorBQ, con lock en DB) o **Celery**
  (igual Stock-Service/BQ-Integraciones) — ver SPK-MELI-6
- Postgres (producción) — mismo patrón `DB_SCHEMA` de Stock-Service para poder convivir en la misma
  base que otros proyectos si aplica, a confirmar con Felipe

## 3. Arquitectura y estructura de carpetas (borrador, mirror de `gestorBQ`)

```
MELI-BQ/
├── meliBQ/                      # paquete de settings (asgi.py, wsgi.py, settings.py, urls.py)
├── catalogo_ml/                 # Módulo 1 — app Django
│   ├── models.py                #   SkuSyncConfig, MLItemMap, MLSyncLog
│   ├── services.py              #   reglas de negocio: qué publicar/actualizar, regla de % precio
│   ├── views.py                 #   vistas HTMX de la grilla de selección
│   └── templates/catalogo_ml/
├── facturacion_ml/               # Módulo 2 — app Django
│   ├── models.py                #   MLOrder, SAPBillingML, SAPInvoiceML (mismo patrón BQ-Integraciones)
│   ├── services.py               #   resolve_customer, prepare_billing, create_sap_invoice
│   └── management/commands/      #   sondeos manuales / reintentos puntuales
├── integraciones/                 # paquete de clientes externos, SIN modelos (igual gestorBQ)
│   ├── ml_client.py               #   OAuth2, items, prices, orders, notifications, billing-info
│   ├── sap_client.py              #   reusar patrón de gestorBQ/integraciones/sap_client.py
│   ├── woo_client.py              #   solo lectura: fotos de producto por SKU
│   ├── stockservice_client.py     #   consumir la API de Stock-Service (catálogo/stock/precio SAP)
│   └── facele_client.py           #   fetch de PDF ya emitido (mismo patrón BQ-Integraciones)
├── templates/                     # base.html, layout compartido
├── static/
│   ├── css/tailwind-src.css → app.css (build purgado, igual gestorBQ)
│   └── vendor/htmx-<version>.js
├── manage.py
└── requirements.txt
```

**Reparto de trabajo (mismo criterio que `gestorBQ/CLAUDE.md`, a confirmar con Felipe si aplica
igual aquí):** frontend/templates puede armarlo Claude; backend (models/views/services) lo escribe
Felipe salvo indicación explícita de "hazlo tú".

## 4. Módulo 1 — Flujo de sync de catálogo

```
Stock-Service (Postgres: SAPProduct/SAPPrice/SAPStock/WooProduct)
        │  (solo lectura — este proyecto NO escribe en la DB de Stock-Service)
        ▼
catalogo_ml.SkuSyncConfig   ← UI (grilla HTMX, selección individual/masiva)
  - sync_stock: bool
  - sync_price: bool
  - enabled: bool
        │
        ▼
   plan_sync_ml()  →  calcula delta SOLO para SKUs con SkuSyncConfig.enabled=True
        │
        ├── SKU sin MLItemMap todavía  →  buscar primero si YA existe en la cuenta ML
        │                                 (GET /items/search?sku=... y ?seller_sku=...) —
        │                                 si existe, adoptarlo; si no, POST /items (HU-CM2.2/2.6)
        └── SKU con MLItemMap          →  PUT /items (o endpoint de stock UP si aplica)
        │
        ▼
   push_ml()  →  ML API, con circuit breaker + reintentos (mismo invariante que Stock-Service:
                  nunca marcar COMPLETED sin confirmación real de la API)
```

**Fotos y descripción:** al publicar un SKU por primera vez, se traen desde la API REST de
WooCommerce (producto por SKU, ya publicado ahí) — no hay gestión de imágenes propia en este
proyecto. **Confirmado contra un producto real (2026-08-20, credenciales ya en `.env` del
proyecto):**
- `images[].src` — URL pública ya servida, se pasa directo a ML (`pictures: [{"source": src}]`).
- `description`/`short_description` — HTML de WordPress/WooCommerce (tablas de specs, listas,
  links). **La API de ML solo acepta texto plano** (`plain_text`, endpoint
  `POST`/`PUT /items/$ID/description`) — hay que limpiar el HTML antes de publicar (ver
  `Documentaciones/MercadoLibre/descripcion-de-productos.md` y HU-CM2.4 del backlog de Módulo 1).

**Regla de precio:** ajuste por porcentaje sobre el precio SAP (bruto, con impuesto ya calculado por
Stock-Service) antes de mandarlo a ML. Configuración: **SPK-MELI-7 resuelto 2026-08-21** — un solo
% global, editable desde la propia UI del catálogo (`ConfiguracionSyncML`, fila única), no por
categoría ni por producto. Implementado en `services.py::calcular_precio_ml`/`guardar_porcentaje_ajuste`.

## 5. Módulo 2 — Flujo de facturación (mismo patrón que `BQ-Integraciones`)

```
ML orders_v2 (notificación webhook o polling) → MLOrder (snapshot, igual que WooOrder)
        │
        ▼
resolve_customer()  — RUT desde buyer.billing_info (vía /orders/billing-info/{site}/{id}),
                       NO desde billing checkout de Woo — arma/actualiza el Business Partner en SAP
        │
        ▼
prepare_billing()   — trocea line_items en lotes ≤21 (mismo límite SAP que BQ-Integraciones),
                       resuelve SKU/bodega contra Stock-Service igual que hoy
        │
        ▼
decidir_doc_type()  — boleta (39) vs factura (33): INFERIDO, no viene explícito en la API de ML
                       (ver spike SPK-MELI-3)
        │
        ▼
create_sap_invoice() — POST a SAP, idempotente (adopta si SAP ya la tiene por crash previo)
        │
        ▼
fetch_pdf()          — Facele/Docele SOAP, reusando integraciones/facele_client.py de BQ-Integraciones
        │
        ▼
send_email()         — al comprador, con el PDF adjunto
```

**Diferencia clave con BQ-Integraciones a tener en cuenta en el diseño:**
- La dirección de `billing_info` es **fiscal**, no la de envío — la dirección de entrega (si algún
  día se necesitara) sale de `/shipments/{shipment_id}`, nunca de `billing_info` (documentado
  explícito por ML).
- El campo que antes decidía boleta/factura (`invoice_type`) fue **removido** de la API — hoy se
  infiere de `identification.type` + `attributes.cust_type` (`CO`=persona física, `BU`=persona
  jurídica). Para MLC específicamente no hay tabla de mapeo publicada por ML (sí para MLA y MPE) —
  es el spike SPK-MELI-3.

## 6. Modelo de datos (borrador — a refinar cuando Felipe empiece a codear)

**Módulo 1:**
- `SkuSyncConfig` — sku (FK lógica a Stock-Service, no hay FK real entre bases), sync_stock,
  sync_price, enabled, updated_at, updated_by
- `MLItemMap` — sku, ml_item_id, ml_site_id, status (mirror del estado publicado en ML)
- `MLSyncLog` — igual rol que `ProductSyncLog` de Stock-Service: una fila por intento de cambio,
  con status/attempts/reason, nunca se sobreescribe silenciosamente

**Módulo 2:**
- `MLOrder` — snapshot inmutable de la orden ML (igual rol que `WooOrder` en BQ-Integraciones)
- `SAPBillingML` — lote a facturar en SAP (igual rol que `SAPBilling`)
- `SAPInvoiceML` — factura/boleta con folio + PDF (igual rol que `SAPInvoice`)
- Tablas de mapeo nuevas (equivalente a `Municipality`/`DeliveryMethod`/`BillDocumentType` de
  BQ-Integraciones, pero indexadas por lo que entrega `billing_info` de ML en vez de `woo_code`)

## 7. Invariantes de seguridad (mismo criterio que Stock-Service/BQ-Integraciones)

- Nunca marcar `COMPLETED` sin confirmación explícita de la API externa (ML o SAP) — un fallo a
  mitad de camino queda `FAILED`/`PENDING`, jamás se asume éxito.
- Circuit breaker en el push a ML: si el plan afecta más de X% de los SKUs seleccionados o deja
  varios en stock 0 de golpe, se aborta antes de escribir (igual que `CIRCUIT_BREAKER_MAX_CHANGE_PCT`
  de Stock-Service).
- Idempotencia por chunk en `prepare_billing`/`create_sap_invoice` (igual que BQ-Integraciones —
  reintentar no debe duplicar facturas en SAP).
- Reintentos con tope (`attempts` → `EXHAUSTED`), nunca reintento infinito silencioso.

## 8. Decisiones tomadas

| Decisión | Detalle |
|---|---|
| Framework | Django 5.2, templates + HTMX + Tailwind CLI standalone (sin DRF, sin Node) |
| Fuente de catálogo/stock/precio | Se lee de Stock-Service (Postgres o su API), no se re-implementa el sync SAP→DB |
| Selección de sync | Persistente en DB propia (`SkuSyncConfig`), controlada desde la UI, no es un flag efímero por corrida |
| Fotos | Se obtienen de la API REST de WooCommerce por SKU, no hay upload manual |
| Boleta/factura | Se infiere de `billing_info` de la orden ML (no hay campo explícito) |
| Referencia de estructura | `gestorBQ` (apps de dominio + paquete `integraciones/` sin modelos) |
| Referencia de patrón de facturación | `BQ-Integraciones` (chain WooOrder→SAP→Facele→email) |
| Login | Google OAuth vía `django-allauth`, portado de `gestorBQ/cuentas/adapters.py` (`BioquimicaSocialAccountAdapter`) — restringido a `@bioquimica.cl`, `SOCIALACCOUNT_ONLY=True` (sin login por contraseña). Implementado 2026-08-20. |

## 9. Spikes abiertos (resolver con Felipe antes de codear lo que dependa)

| ID | Pregunta | Bloquea |
|---|---|---|
| SPK-MELI-1 | ~~App ML~~ **RESUELTO 2026-08-20** — app creada en developers.mercadolibre.cl, `ML_APP_ID`/`ML_APP_SECRET` en `.env`. `ML_REDIRECT_URI` fijado (`.../catalogo/ml/callback/`, HTTPS obligatorio confirmado en la doc oficial — por eso el deploy a `meli-dev.bioquimica.cl` en curso, ver sección 12). Falta solo el código que lo consume: HU-CM0.2 (`ml_client.py::obtener_access_token`, todavía `NotImplementedError`). | HU-CM0.2 (auth real de ambos módulos) |
| SPK-MELI-13 | ~~Login de operadores~~ **RESUELTO 2026-08-20** — Google OAuth vía `django-allauth`, credenciales ya en `.env` (`GOOGLE_CLIENT_ID`/`SECRET`). Falta un paso externo (no código): registrar el `redirect_uri` en Google Cloud Console → credencial OAuth. Confirmado por smoke test el valor exacto que pide Django: **dev** `http://127.0.0.1:8000/accounts/google/login/callback/`; **prod**, el mismo path sobre el dominio real (`https://<dominio>/accounts/google/login/callback/`) — agregar ambos a la lista de "Authorized redirect URIs" de la credencial. | Probar el login real end-to-end (el flujo ya redirige correcto a Google hasta ese punto) |
| SPK-MELI-2 | Tags reales del seller ML de bioquimica.cl (`user_product_seller`, `warehouse_management`, `multiwarehouse`) — determinan qué endpoint de stock usar. Solo se sabe consultando `/users/$USER_ID` con un token real. | Módulo 1, endpoint de stock a implementar |
| SPK-MELI-3 | Mapeo boleta(39)/factura(33) para MLC: ¿`cust_type=CO` con `billing_info` presente es boleta nominada o puede pedir factura? Sin caso real disponible hoy — Felipe no tiene una orden histórica con factura en ML para revisar. | Módulo 2, `decidir_doc_type()` |
| SPK-MELI-4 | ~~Credenciales/acceso a la API REST de WooCommerce~~ | **RESUELTO 2026-08-20** — `WOO_URL`/`WOO_KEY`/`WOO_SECRET` en `.env` del proyecto. Confirmado contra un producto real: `images[].src`, `description`, `short_description`, `sku` (coincide con SAP). La descripción viene en HTML y necesita limpieza a texto plano (ver HU-CM2.4) — la API de ML no acepta HTML. |
| SPK-MELI-5 | ~~¿DB directa o API REST de Stock-Service?~~ **RESUELTO 2026-08-20 — API REST.** Mismo patrón que ya usa `BQ-Integraciones` en producción (decisión D2 de su `plan.md`). La Postgres real de Stock-Service vive en DigitalOcean compartida con otro proyecto vía `DB_SCHEMA` — acceder directo ahí acopla MELI-BQ a un esquema interno no versionado. La API (`https://stock-sap-bq-production.up.railway.app`, dominio público, auth `X-API-Key` global) ya expone `GET /api/v1/stock/catalog` (paginado + búsqueda, exactamente lo que pide HU-CM1.1) y `GET /api/v1/stock/products/{sku}`. Implementado en `integraciones/stockservice_client.py::obtener_catalogo()`/`obtener_producto()`, con tests mockeados en `integraciones/tests.py`. Sin caché (Redis) todavía — BQ-Integraciones sí cachea; evaluar si hace falta cuando la grilla esté conectada de verdad. | — resuelto |
| SPK-MELI-6 | ~~Scheduler~~ **RESUELTO 2026-08-21 — APScheduler, mismo patrón que `pedidos/scheduler.py` de gestorBQ** (in-process, lock en DB con supervisor cada minuto que roba el lock a un dueño muerto — evita el incidente real de 3 días sin sync que tuvo gestorBQ en agosto 2026). No Celery/Redis: no hay necesidad real de infra nueva. Automático cada 30-60 min + botón manual "Sincronizar ahora" en la UI (decisión de Felipe). | E0 de ambos módulos | — resuelto |
| SPK-MELI-7 | ~~Regla de ajuste de precio por porcentaje~~ **RESUELTO 2026-08-21 — un solo % global, editable desde el frontend.** Decisión de Felipe: no por categoría ni por producto. `ConfiguracionSyncML` (fila única) + `services.py::calcular_precio_ml`/`guardar_porcentaje_ajuste`, form en `catalogo_ml/index.html`. | Módulo 1, `services.py::calcular_precio_ml` | — resuelto |
| SPK-MELI-8 | ~~Despliegue~~ **RESUELTO 2026-08-20** — mismo servidor on-prem que `gestorBQ` (152.230.53.151 / LAN oficina), Docker + Caddy compartido con `mirastock` + túnel Cloudflare existente. Motivo inmediato: ML exige HTTPS en el `redirect_uri` incluso para probar en dev — necesitábamos una URL real ya. Ver sección 12. | — resuelto |

## 10. Integraciones externas — resumen de contratos

| Sistema | Uso en este proyecto | Referencia |
|---|---|---|
| Mercado Libre API | OAuth2, items/prices (Módulo 1), orders/billing-info/notifications (Módulo 2) | `Documentaciones/MercadoLibre/` |
| Stock-Service | Fuente de catálogo, stock y precio SAP ya calculado (solo lectura) | `C:\Users\920562\Documents\proyectos\Stock-Service` |
| WooCommerce REST API | Solo lectura — fotos de producto por SKU | pendiente credenciales (SPK-MELI-4) |
| SAP Business One (Service Layer) | Creación de Business Partner + facturación, vía Token-SAP-BQ (sesión compartida) | mismo patrón que `gestorBQ`/`BQ-Integraciones` |
| Facele/Docele | Obtención de PDF de boleta/factura ya emitida (SOAP) | mismo cliente que `BQ-Integraciones/app/services/facele/client.py` |

## 11. Orden de implementación sugerido

1. Resolver spikes de infraestructura (SPK-MELI-1, 5, 6, 8) — condicionan la estructura del proyecto.
2. Bootstrap Django (settings, apps vacías, Tailwind/HTMX vendorizado) — sin lógica todavía.
3. `integraciones/stockservice_client.py` + `integraciones/ml_client.py` (auth + items/prices) —
   base de la que depende todo el Módulo 1.
4. Módulo 1 completo (UI de selección → plan → push) antes de tocar Módulo 2 — es el de menor
   dependencia externa nueva (SAP/Facele no entran aquí).
5. Módulo 2: `integraciones/ml_client.py` (orders/billing-info/notifications) + reusar
   `sap_client.py`/`facele_client.py` ya validados en `BQ-Integraciones`/`gestorBQ` — resolver
   SPK-MELI-3 antes de cerrar `decidir_doc_type()`.

## 12. Despliegue — en curso (2026-08-20)

Disparado por SPK-MELI-1: ML exige HTTPS en el `redirect_uri` incluso para probar en desarrollo, así
que no alcanzaba con `http://127.0.0.1:8000` — hacía falta una URL real ya. Se decidió resolver
SPK-MELI-8 al mismo tiempo en vez de parchar con un túnel (ngrok) temporal.

**Decisiones tomadas:**
- **Servidor:** el mismo que ya usa `gestorBQ` (152.230.53.151, LAN de la oficina) — confirmado por
  SSH (solo lectura) que es la misma máquina (`Ubuntu 24.04`, usuario `gestorbq` presente, Docker
  29.6, 1.7TB libres). Se reusa Caddy (comparte contenedor con `mirastock`) y el túnel Cloudflare
  existente — mismo patrón exacto que `gestorBQ/backlog_proyecto/Completado/runbook-despliegue-servidor-bq.md`
  (ya ejecutado y probado ahí, con todas las vueltas reales ya resueltas — ufw, quirks de Caddy/túnel).
- **Hostname:** `meli-dev.bioquimica.cl` — un solo ambiente por ahora (no test/prod separados, el
  proyecto recién arranca, no se justifica la separación que sí necesitó gestorBQ en producción real).
- **Base de datos:** SQLite (no Postgres) — para este primer deploy el objetivo es solo tener una URL
  HTTPS real para probar el login de ML; Postgres se evalúa cuando haya uso real. Evita tocar
  `pg_hba.conf`/`ufw` del Postgres compartido por ahora.
- **Repo:** `https://github.com/FelipeMv2301/MELI-BQ.git`.
- **Puerto:** `8005` (8002 gestor, 8003 gestor-test, 8004 resultó estar tomado por otro proyecto no
  documentado hasta ahora, `grafico_bq` — primer puerto libre real confirmado contra el server).
- **Auto-deploy:** GitHub Actions con runner self-hosted, instalado y corriendo como servicio
  systemd bajo el usuario `bioquimicacl` (no se creó un usuario dedicado tipo `gestorbq` — decisión
  de alcance para este primer pase, se puede migrar después si hace falta más aislamiento).

**Diferencia clave vs. el runbook de gestorBQ (que usa Postgres):** sin `extra_hosts:
host.docker.internal` en el `docker-compose.yml` — no hace falta, SQLite no vive en el host, vive en
el propio contenedor (con volumen bind-mount para persistir entre rebuilds).

**✅ Ejecutado end-to-end (2026-08-20):**
- Runner registrado y activo (`actions.runner.FelipeMv2301-MELI-BQ.meli-bq-runner.service`).
- Gotcha real encontrado (no estaba en el runbook de gestorBQ porque ahí sí se creó un usuario
  dedicado en el grupo `docker` desde el principio): el primer deploy automático falló en 12s —
  `bioquimicacl` no estaba en el grupo `docker`. Se agregó (`usermod -aG docker`) y se reinició el
  servicio del runner para que tomara el grupo nuevo.
- `.env` de este ambiente subido al server (`/home/bioquimicacl/meli-bq-dev/.env`, `chmod 600`,
  nunca versionado) — `DEBUG=False`, `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS=meli-dev.bioquimica.cl`,
  `ML_REDIRECT_URI=https://meli-dev.bioquimica.cl/catalogo/ml/callback/`, `SECRET_KEY` propio
  (nunca el de dev local).
- Build + migrate + smoke test manual: `curl` con `Host: meli-dev.bioquimica.cl` contra el
  contenedor → 302 a `/accounts/login/`, como corresponde (un `curl` directo a la IP sin ese header
  da 400 `DisallowedHost` — comportamiento esperado de Django, no un bug).
- Bloque de Caddy agregado a `/home/bioquimicacl/mirastock/Caddyfile` (mismo Caddyfile compartido
  que ya usan mirastock/gestor/gestor-test/graficos) — `reverse_proxy host.docker.internal:8005`
  (no `127.0.0.1`, ese es justo el patrón real ya usado ahí), `header_up X-Forwarded-Proto https`
  fijo (el túnel entrega siempre HTTP interno). `caddy reload` aplicado sin bajar el contenedor.
- Regla de `ingress` agregada a `/home/bioquimicacl/mirastock/cloudflared/config.yml` (túnel
  `3ab9328f-e315-42c0-974b-1519a2aa01ff`, mismo que ya usan los demás hostnames) + `docker compose
  restart cloudflared` — reconectado limpio.
- Verificado enrutamiento completo de punta a punta DENTRO del server (`docker exec
  mirastock-caddy-1 wget --header='Host: meli-dev.bioquimica.cl' ...` → 302 → sigue redirect → 200
  la pantalla de login) — todo lo que no depende de DNS público ya funciona.

**Pendiente — acción de Felipe, no hay más código/SSH que hacer para esto:**
1. Cloudflare dashboard → DNS → registro **CNAME**, nombre `meli-dev`, target
   `3ab9328f-e315-42c0-974b-1519a2aa01ff.cfargotunnel.com` (mismo túnel, solo falta el DNS).
2. Una vez propagado el DNS: registrar `https://meli-dev.bioquimica.cl/catalogo/ml/callback/` como
   redirect URI en la app de Mercado Libre (developers.mercadolibre.cl → Mis aplicaciones) — el
   `http://127.0.0.1` nunca se pudo guardar (ML exige HTTPS), así que este es el primero real.
3. Agregar también `https://meli-dev.bioquimica.cl/accounts/google/login/callback/` a los redirect
   URIs autorizados en Google Cloud Console (se suma a la lista, no reemplaza el de `127.0.0.1`).

## 13. Ver también

- `backlog-sync-catalogo-ml.md` — historias de usuario, Módulo 1
- `backlog-facturacion-ml.md` — historias de usuario, Módulo 2
- `Documentaciones/MercadoLibre/` — referencia técnica cruda de la API (auth, items/User Products,
  precios, órdenes, notificaciones, facturación/billing-info)
