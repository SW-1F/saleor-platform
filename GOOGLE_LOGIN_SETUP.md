# Login con Google — Guía de configuración

Esta guía deja funcionando el botón **"Google"** en el login del Dashboard, para
que cualquier usuario inicie sesión con su cuenta de Google y entre a la
plataforma.

El código ya está cableado:

- **Backend:** plugin `saleor/saleor/plugins/google_oidc/plugin.py`, registrado en
  `saleor/saleor/settings.py` cuando existen las variables de entorno de Google.
- **Dashboard:** la pantalla de login ya muestra automáticamente un botón por cada
  método de autenticación externa disponible (no hay que tocar el frontend).
- **Docker:** `docker-compose.full.yml` ahora **construye la API desde `./saleor`**
  (imagen `saleor-local:dev`) para incluir el plugin, y lee las credenciales del
  archivo `.env`.

Lo único que falta es **crear las credenciales gratuitas de Google** y pegarlas en
`.env`. Toma unos 5 minutos y no requiere tarjeta ni facturación.

---

## Paso 1 — Crear las credenciales en Google Cloud Console

1. Entra a https://console.cloud.google.com/ con tu cuenta de Google.
2. Arriba, crea (o elige) un proyecto. Cualquier nombre sirve, p. ej. `saleor-lab`.
3. Menú ☰ → **APIs y servicios** → **Pantalla de consentimiento de OAuth**
   (*OAuth consent screen*):
   - Tipo de usuario: **External** → **Crear**.
   - Nombre de la app: `Saleor Lab`; correo de soporte: el tuyo; correo del
     desarrollador: el tuyo. Guarda y continúa.
   - En **Usuarios de prueba** (*Test users*), agrega los correos de Google con los
     que vas a iniciar sesión (si dejas la app en modo "Testing", solo esos correos
     podrán entrar; es lo normal para un laboratorio).
4. Menú ☰ → **APIs y servicios** → **Credenciales** → **Crear credenciales** →
   **ID de cliente de OAuth** (*OAuth client ID*):
   - Tipo de aplicación: **Aplicación web** (*Web application*).
   - Nombre: `Saleor Dashboard`.
   - **Orígenes de JavaScript autorizados** (*Authorized JavaScript origins*):

     ```
     http://localhost:9000
     ```

   - **URIs de redirección autorizados** (*Authorized redirect URIs*) — copia exacto:

     ```
     http://localhost:9000/login/callback/
     ```

     > Importante: debe terminar con la barra final `/`. Este es exactamente el
     > callback que usa el Dashboard (`window.location.origin` + `/login/callback/`).

   - **Crear**. Google te mostrará el **Client ID** y el **Client Secret**: cópialos.

---

## Paso 2 — Pegar las credenciales en `.env`

En la raíz del repo (misma carpeta que `docker-compose.full.yml`):

```bash
cp .env.example .env      # Windows CMD:  copy .env.example .env
```

Edita `.env` y rellena:

```dotenv
GOOGLE_OIDC_CLIENT_ID=123456789-abcdef.apps.googleusercontent.com
GOOGLE_OIDC_CLIENT_SECRET=GOCSPX-tu_secreto

# Tu correo entra como administrador del dashboard:
GOOGLE_OIDC_STAFF_EMAILS=tu_correo@gmail.com
# (opcional, demo) cualquier cuenta de estos dominios entra como admin:
GOOGLE_OIDC_STAFF_DOMAINS=
```

- **Para entrar tú** (y compañeros concretos): pon sus correos en
  `GOOGLE_OIDC_STAFF_EMAILS`, separados por coma.
- **Para que entre cualquiera con Gmail** (solo demo): pon
  `GOOGLE_OIDC_STAFF_DOMAINS=gmail.com`. ⚠️ Esto da permisos de administrador a
  cualquier cuenta Gmail; úsalo únicamente en el laboratorio.

---

## Paso 3 — Levantar el stack

```bash
docker compose -f docker-compose.full.yml up --build
```

La primera vez construye la imagen `saleor-local:dev` desde `./saleor` (tarda unos
minutos) e instala dependencias del dashboard. Cuando veas `VITE ... ready`:

- Dashboard: http://localhost:9000
- API GraphQL: http://localhost:8000/graphql/

---

## Paso 4 — Probar el login

1. Abre http://localhost:9000
2. En la pantalla de login verás el botón **"Google"** (debajo del formulario de
   correo/contraseña).
3. Púlsalo → te redirige a Google → eliges tu cuenta → vuelves al Dashboard
   autenticado.
4. Si tu correo está en `GOOGLE_OIDC_STAFF_EMAILS` (o su dominio en
   `GOOGLE_OIDC_STAFF_DOMAINS`), entrarás como administrador.

---

## Cómo funciona (resumen del flujo)

```
Dashboard (localhost:9000)
   │  1) clic en "Google"  → mutation externalAuthenticationUrl(pluginId, redirectUri)
   ▼
Saleor API (GoogleOIDCPlugin)  → arma la URL de autorización de Google
   │
   ▼
accounts.google.com  → el usuario inicia sesión y autoriza
   │  2) redirige a  http://localhost:9000/login/callback/?code=...&state=...
   ▼
Dashboard  → mutation externalObtainAccessTokens(code, state)
   │
   ▼
Saleor API  → intercambia el code con Google, valida el id_token, crea/vincula
              el usuario por su correo y, si está permitido, lo marca como staff.
```

---

## Solución de problemas

- **No aparece el botón "Google":** revisa que `GOOGLE_OIDC_CLIENT_ID` y
  `GOOGLE_OIDC_CLIENT_SECRET` estén en `.env` y que reconstruiste con `--build`.
  El registro del plugin en `settings.py` es condicional a esas dos variables.
- **`redirect_uri_mismatch`:** el URI en Google Cloud debe ser exactamente
  `http://localhost:9000/login/callback/` (con la barra final).
- **Entras pero el dashboard sale vacío / sin permisos:** tu correo no está en
  `GOOGLE_OIDC_STAFF_EMAILS` ni su dominio en `GOOGLE_OIDC_STAFF_DOMAINS`.
- **`access_blocked` / app no verificada:** agrega tu correo en *Test users* de la
  pantalla de consentimiento, o mantén la app en modo *Testing*.

---

## Nota de seguridad (coherente con el informe de la Parte 3)

El plugin concede **todos** los permisos de administrador a los correos/dominios
permitidos (`_grant_full_permissions_if_allowed` → `get_permissions()`). Para un
entorno real conviene asignar un **rol acotado** en lugar de todos los permisos, y
preferir `GOOGLE_OIDC_STAFF_EMAILS` (lista cerrada) sobre dominios abiertos.
