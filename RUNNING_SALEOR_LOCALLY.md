# Guía de Ejecución Local: Saleor Platform (Código Fuente)

Este documento describe cómo levantar **todos los servicios de Saleor** localmente.
El Backend y el Dashboard corren **desde el código fuente** (con live reload),
y la infraestructura (BD, caché, correo) corre **desde Docker**.

---

## Estructura del Proyecto

```
saleor-platform/
├── saleor/                  ← Código fuente del Backend (Python/Django/GraphQL)
├── saleor-dashboard/        ← Código fuente del Frontend (React/TypeScript)
├── docker-compose.yml       ← Infraestructura: PostgreSQL, Redis, Mailpit
└── RUNNING_SALEOR_LOCALLY.md
```

---

## Requisitos Previos

| Herramienta | Versión mínima | Verificar con |
|-------------|---------------|---------------|
| **Docker Engine** | 24+ | `docker --version` |
| **Docker Compose** | v2+ | `docker compose version` |
| **uv** (gestor Python) | 0.11+ | `uv --version` |
| **Node.js** | 22+ | `node --version` |
| **npm** | 11+ | `npm --version` |

> [!WARNING]
> En **Linux** (Fedora, Ubuntu, etc.) utiliza el **Docker Engine nativo**, no Docker Desktop.
> Docker Desktop usa una VM (QEMU) que puede quedarse sin memoria y causar crashes.
> Cambia al contexto nativo con:
> ```bash
> docker context use default
> ```

### Instalación de uv (solo la primera vez)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
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

Crear el archivo `.env` copiando el ejemplo y añadiendo las variables necesarias:

```bash
cp .env.example .env
```

Luego editar `.env` y asegurarse de que contenga estas líneas:

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

```bash
cd ../saleor-dashboard
npm install --legacy-peer-deps
npm install --legacy-peer-deps @material-ui/icons@4.11.3 @material-ui/lab@4.0.0-alpha.61
```

### 4. Levantar infraestructura y migrar la base de datos

```bash
# Desde la raíz del proyecto
cd ..
docker compose up -d db cache mailpit

# Migrar y poblar la base de datos (volver a saleor/)
cd saleor
export PATH="$HOME/.local/bin:$PATH"
uv run poe migrate
uv run poe populatedb
```

> [!NOTE]
> `populatedb` crea un usuario administrador:
> - **Correo:** `admin@example.com`
> - **Contraseña:** `admin`

---

## Encender Todos los Servicios (día a día)

Ejecuta estos comandos **en orden**, cada uno en una terminal separada:

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
export PATH="$HOME/.local/bin:$PATH"
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
# En Terminal 3 (Dashboard):   Ctrl+C
# En Terminal 2 (Backend):     Ctrl+C

# En Terminal 1 (Infraestructura):
cd saleor-platform
docker compose stop
```

---

## Troubleshooting

### `no configuration file provided: not found`
Estás ejecutando `docker compose` desde una carpeta incorrecta.
El archivo `docker-compose.yml` está en la **raíz** de `saleor-platform/`:
```bash
cd saleor-platform
docker compose up -d db cache mailpit
```

### `Address already in use` al iniciar el Backend
El puerto 8000 está ocupado por otro proceso. Identifícalo y detenlo:
```bash
# Ver qué ocupa el puerto 8000
lsof -i :8000
# O detener contenedores Docker que puedan estar usándolo
docker ps | grep 8000
docker stop <nombre-del-contenedor>
```

### `ERESOLVE` al hacer `npm install` en el Dashboard
Usa la flag `--legacy-peer-deps`:
```bash
npm install --legacy-peer-deps
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
```
Si no aparece, levántalo con:
```bash
cd saleor-platform
docker compose up -d db
```
