# Guía de Ejecución Local: Saleor Platform (Código Fuente)

Este documento describe cómo levantar **todos los servicios de Saleor** localmente.
El Backend y el Dashboard corren **desde el código fuente** (con live reload),
y la infraestructura (BD, caché, correo) corre **desde Docker**.

---

## Estructura del Proyecto

```
saleor-platform/             ← raíz del repositorio
├── saleor/                  ← Código fuente del Backend (Python/Django/GraphQL)
├── saleor-dashboard/        ← Código fuente del Frontend (React/TypeScript)
├── docker-compose.yml       ← Infraestructura: PostgreSQL, Redis, Mailpit
└── RUNNING_SALEOR_LOCALLY.md
```

---

## Requisitos Previos

| Herramienta | Versión mínima | Verificar con |
|-------------|---------------|---------------|
| **Docker Engine / Desktop** | 24+ | `docker --version` |
| **Docker Compose** | v2+ | `docker compose version` |
| **uv** (gestor Python) | 0.11+ | `uv --version` |
| **Node.js** | 22+ | `node --version` |
| **npm** | 11+ | `npm --version` |

> [!NOTE]
> **Recomendación para Windows:** Se recomienda utilizar **Git Bash** como tu terminal para poder ejecutar la mayoría de comandos de tipo bash directamente. Asegúrate de instalar **Docker Desktop** y activar la integración con **WSL 2**.

> [!WARNING]
> En **Linux** (Fedora, Ubuntu, etc.) utiliza el **Docker Engine nativo**, no Docker Desktop.
> Docker Desktop usa una VM (QEMU) que puede quedarse sin memoria y causar crashes.
> Cambia al contexto nativo con:
> ```bash
> docker context use default
> ```

### Instalación de uv (solo la primera vez)

- **Linux / macOS (Bash/Zsh):**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
  Para que `uv` funcione permanentemente, agrega esta línea al final de tu `~/.bashrc` o `~/.zshrc`:
  ```bash
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
  source ~/.zshrc
  ```

- **Windows (PowerShell):**
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
  *Nota: Reinicia la terminal después de la instalación para que reconozca el comando `uv`.*

- **Windows (Alternativa con winget):**
  ```cmd
  winget install astral-uv
  ```

---

## Primer Setup (solo una vez)

### 1. Clonar el repositorio

```bash
git clone git@github.com:SW-1F/saleor-platform.git
cd saleor-platform
```

### 2. Instalar dependencias del Backend

```bash
cd saleor
uv python install 3.12
uv sync
```

Crear el archivo `.env`:

- **Linux / macOS (o Git Bash):**
  ```bash
  cp .env.example .env
  ```
- **Windows (PowerShell / CMD):**
  ```cmd
  copy .env.example .env
  ```

Editar `.env` y asegurarse de que contenga estas líneas (añadir las que falten):

```env
CACHE_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
DATABASE_URL=postgres://saleor:saleor@localhost:5432/saleor
DEFAULT_FROM_EMAIL=noreply@example.com
EMAIL_URL=smtp://localhost:1025
SECRET_KEY=changeme
HTTP_IP_FILTER_ALLOW_LOOPBACK_IPS=True
DASHBOARD_URL=http://localhost:9000/
ALLOWED_HOSTS=localhost,127.0.0.1
DEBUG=True
```

### 3. Instalar dependencias del Frontend

Desde la raíz del repo (`saleor-platform/`), ve a la carpeta del dashboard e instala las dependencias:

- **Linux / macOS (o Git Bash en Windows):**
  ```bash
  cd ../saleor-dashboard
  HUSKY=0 npm install --legacy-peer-deps
  ```
- **Windows (PowerShell):**
  ```powershell
  cd ../saleor-dashboard
  $env:HUSKY=0
  npm install --legacy-peer-deps
  ```
- **Windows (CMD):**
  ```cmd
  cd ../saleor-dashboard
  set HUSKY=0
  npm install --legacy-peer-deps
  ```

Luego, instala los iconos e interfaz de Material-UI (aplica para cualquier plataforma):
```bash
npm install --legacy-peer-deps @material-ui/icons@4.11.3 @material-ui/lab@4.0.0-alpha.61
```

> [!NOTE]
> `HUSKY=0` desactiva los git hooks de Husky durante la instalación.
> Es necesario porque `saleor-dashboard` ya no tiene su propio repositorio git independiente.

### 4. Levantar infraestructura y migrar la base de datos

```bash
# Desde la raíz del repo (saleor-platform/)
cd ..
docker compose up -d db cache mailpit

# Migrar y poblar la base de datos
cd saleor
uv run poe migrate
uv run poe populatedb
```

> [!NOTE]
> `populatedb` crea un usuario administrador:
> - **Correo:** `admin@example.com`
> - **Contraseña:** `admin`

---

## Encender Todos los Servicios (día a día)

Cada vez que quieras trabajar, abre **3 terminales** y ejecuta:

### Terminal 1 — Infraestructura (Docker)

```bash
cd saleor-platform
docker compose up -d db cache mailpit
```

Levanta:
- **PostgreSQL** en `localhost:5432`
- **Redis** en `localhost:6379`
- **Mailpit** en http://localhost:8025

### Terminal 2 — Backend (API GraphQL)

```bash
cd saleor-platform/saleor
uv run poe start
```

Espera a ver:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

✅ API disponible en **http://localhost:8000/graphql/**

### Terminal 3 — Frontend (Dashboard)

```bash
cd saleor-platform/saleor-dashboard
npm run dev
```

Espera a ver:
```
VITE ready in XXX ms
  ➜  Local:   http://localhost:9000/
```

✅ Dashboard disponible en **http://localhost:9000/**

---

## Resumen de URLs

| Servicio | URL | Tipo |
|----------|-----|------|
| **Dashboard** | http://localhost:9000 | Frontend (código fuente, live reload) |
| **API GraphQL** | http://localhost:8000/graphql/ | Backend (código fuente, live reload) |
| **Mailpit** | http://localhost:8025 | Docker |

**Credenciales de administrador:** `admin@example.com` / `admin`

---

## Apagar Todo

```bash
# Terminal 3 (Dashboard):   Ctrl+C
# Terminal 2 (Backend):     Ctrl+C

# Terminal 1 (Infraestructura):
cd saleor-platform
docker compose stop
```

---

## Troubleshooting

### `error: Failed to spawn: 'poe'`
El binario `uv` no está en el PATH. Ejecútalo directamente con su ruta o agrega al PATH:
```bash
export PATH="$HOME/.local/bin:$PATH"
uv run poe start
```
Para no repetirlo cada vez, agrégalo permanentemente a `~/.zshrc` o `~/.bashrc`:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

### `husky - .git can't be found`
Usa la variable `HUSKY=0` al instalar:
```bash
HUSKY=0 npm install --legacy-peer-deps
```

### `no configuration file provided: not found`
El `docker-compose.yml` está en la **raíz** de `saleor-platform/`.
Asegúrate de estar ahí antes de ejecutar docker compose:
```bash
cd saleor-platform
docker compose up -d db cache mailpit
```

### `Address already in use` al iniciar el Backend
El puerto 8000 está ocupado. Detén los contenedores que puedan usarlo:
```bash
docker ps | grep 8000
docker stop <nombre-del-contenedor>
```

### `ERESOLVE` al hacer `npm install`
Usa `--legacy-peer-deps`:
```bash
HUSKY=0 npm install --legacy-peer-deps
```

### `signal: aborted (core dumped)` en Docker (Linux)
Docker Desktop se quedó sin memoria. Cambia al Docker Engine nativo:
```bash
docker context use default
```

### El Backend no encuentra la base de datos
Verifica que el contenedor de PostgreSQL está corriendo:
```bash
docker ps | grep db
# Si no aparece:
cd saleor-platform && docker compose up -d db
```
