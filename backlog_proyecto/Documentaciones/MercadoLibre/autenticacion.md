# Autenticación y Autorización — Mercado Libre API

Fuente: `developers.mercadolibre.com.ar/es_ar/autenticacion-y-autorizacion` (leído 2026-08-20, ver
`ml_docs_access_technique` en memoria de Claude para cómo se accedió — WebFetch da 403, se usó curl
con User-Agent de navegador).

## Flujo: Authorization Code (Server Side)

1. **Redirigir al usuario** a la página de autorización:
   ```
   https://auth.mercadolibre.com.ar/authorization?response_type=code&client_id=$APP_ID&redirect_uri=$YOUR_URL&code_challenge=$CODE_CHALLENGE&code_challenge_method=$CODE_METHOD
   ```
   - Cambiar `.com.ar` por el dominio del site correspondiente (Chile: `.cl`... a confirmar el
     dominio exacto de auth para MLC, probablemente `auth.mercadolibre.cl`).
   - `redirect_uri` debe ser **exacto** al configurado en la app, sin información variable.
   - `state` recomendado para seguridad (CSRF).
   - `code_challenge`/`code_challenge_method` solo si la app tiene PKCE habilitado — si está
     habilitado, es **obligatorio** enviarlos.
   - Nota: el usuario que loguea debe ser **administrador** de la cuenta ML, no colaborador/operador
     — si no, error `invalid_operator_user_id`.

2. **Callback** — ML redirige a `redirect_uri` con `?code=$AUTHORIZATION_CODE`.

3. **Canjear el code por un access_token:**
   ```
   POST https://api.mercadolibre.com/oauth/token
   Content-Type: application/x-www-form-urlencoded

   grant_type=authorization_code
   client_id=$APP_ID
   client_secret=$SECRET_KEY
   code=$SERVER_GENERATED_AUTHORIZATION_CODE
   redirect_uri=$REDIRECT_URI
   code_verifier=$CODE_VERIFIER   # solo si PKCE
   ```
   Respuesta:
   ```json
   {
       "access_token": "APP_USR-...",
       "token_type": "bearer",
       "expires_in": 10800,
       "scope": "offline_access read write",
       "user_id": 1234567,
       "refresh_token": "TG-..."
   }
   ```
   `expires_in` = 10800s = **6 horas**.

4. **Usar el token** — header obligatorio en toda llamada:
   ```
   Authorization: Bearer APP_USR-...
   ```

## Refresh token

```
POST https://api.mercadolibre.com/oauth/token
grant_type=refresh_token
client_id=$APP_ID
client_secret=$SECRET_KEY
refresh_token=$REFRESH_TOKEN
```
Devuelve un access_token nuevo **y un refresh_token nuevo** — hay que persistir el nuevo cada vez.

**Reglas críticas de persistencia:**
- El `refresh_token` es de **un solo uso** — al usarlo queda inválido.
- Expira a los **6 meses** si no se usa.
- Solo el `client_id` con el que se generó puede usarlo.

## Qué invalida un access_token antes de tiempo

- Cambio de contraseña del usuario.
- Rotación del Client Secret de la app.
- Revocación de permisos por parte del usuario.
- 4 meses sin ninguna llamada a `api.mercadolibre.com`.

## Errores comunes

| Error | Causa |
|---|---|
| `invalid_client` | `client_id`/`client_secret` inválido |
| `invalid_grant` | code/refresh_token inválido, expirado, ya usado, o `redirect_uri` no coincide |
| `invalid_scope` | scope inválido (válidos: `offline_access`, `write`, `read`) |
| `invalid_request` | falta parámetro obligatorio o mal formado |
| `unsupported_grant_type` | `grant_type` distinto de `authorization_code`/`refresh_token` |
| `forbidden` (403) | token de otro usuario, IP bloqueada, o faltan scopes |
| `local_rate_limited` (429) | rate limit — reintentar con backoff |
| `unauthorized_client` | app sin autorización para ese usuario/scope |
| `unauthorized_application` | app bloqueada |

## Implicancia de diseño para MELI-BQ

`integraciones/ml_client.py` necesita persistir `access_token`/`refresh_token`/`expires_at` en DB
(no en memoria de proceso — con Django multi-worker, dos procesos no pueden pisarse el refresh).
Refrescar **proactivamente** antes de expirar, no solo reactivo a un 401, para evitar que dos
requests concurrentes intenten refrescar al mismo tiempo y uno pierda el `refresh_token` de un solo
uso del otro.
