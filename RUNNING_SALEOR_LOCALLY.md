# Guía de Ejecución Local: Saleor Platform (Código Fuente)

Este documento describe cómo levantar **todos los servicios de Saleor** localmente,
ejecutando el Backend y el Dashboard **desde el código fuente** (con live reload)
y la infraestructura (BD, caché, correo) **desde Docker**.

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
> Cambia al contexto nativo con: `docker context use default`

### Instalación de herramientas (solo la primera vez)

```bash
# Instalar uv (gestor de Python)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

---

## Estructura del Proyecto

```
Calidad_de_Software/
├── saleor-platform/       # Orquestador Docker (docker-compose.yml)
    ├── saleor/                # Código fuente del Backend (Python/Django)
    └── saleor-dashboard/      # Código fuente del Frontend (React/TypeScript)
```

---

## Primer Setup (solo una vez)

### 1. Clonar los repositorios

```bash
git clone git@github.com:SW-1F/saleor-platform.git
```

### 2. Instalar dependencias del Backend

```bash
cd saleor
uv python install 3.12
uv sync
cp .env.example .env
```

Editar el archivo `.env` y agregar estas líneas adicionales:

```env
DATABASE_URL=postgres://saleor:saleor@localhost:5432/saleor
ALLOWED_HOSTS=localhost,127.0.0.1
DEBUG=True
```

### 3. Instalar dependencias del Frontend

```bash
cd saleor-dashboard
npm install --legacy-peer-deps
npm install --legacy-peer-deps @material-ui/icons@4.11.3 @material-ui/lab@4.0.0-alpha.61
```

### 4. Levantar infraestructura y migrar la BD

```bash
# Levantar PostgreSQL, Redis y Mailpit
cd saleor-platform
docker compose up -d db cache mailpit

# Migrar y poblar la base de datos
cd ../saleor
uv run poe migrate
uv run poe populatedb
```

> [!NOTE]
> `populatedb` crea un usuario administrador:
> - **Correo:** `admin@example.com`
> - **Contraseña:** `admin`

---

## Encender Todos los Servicios (día a día)

Cada vez que quieras trabajar con el proyecto, ejecuta estos comandos en orden:

### Paso 1 — Infraestructura (Docker)

```bash
cd saleor-platform
docker compose up -d db cache mailpit
```

Esto levanta:
- **PostgreSQL** en `localhost:5432`
- **Redis** en `localhost:6379`
- **Mailpit** en `http://localhost:8025`

### Paso 2 — Backend (API GraphQL)

Abre una **terminal nueva** y ejecuta:

```bash
cd saleor
export PATH="$HOME/.local/bin:$PATH"
uv run poe start
```

Espera a ver el mensaje:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

✅ API disponible en **http://localhost:8000/graphql/**

### Paso 3 — Frontend (Dashboard)

Abre **otra terminal nueva** y ejecuta:

```bash
cd saleor-dashboard
npm run dev
```

Espera a ver el mensaje:
```
VITE ready in XXX ms

  ➜  Local:   http://localhost:9000/
```

✅ Dashboard disponible en **http://localhost:9000/**

---

## Resumen de URLs

| Servicio | URL | Tipo |
|----------|-----|------|
| **Dashboard** | http://localhost:9000 | Frontend (código fuente) |
| **API GraphQL** | http://localhost:8000/graphql/ | Backend (código fuente) |
| **Mailpit** | http://localhost:8025 | Docker |

**Credenciales de administrador:** `admin@example.com` / `admin`

---

## Apagar Todo

```bash
# En la terminal del Dashboard: presiona Ctrl+C
# En la terminal del Backend: presiona Ctrl+C

# Detener la infraestructura Docker:
cd saleor-platform
docker compose stop
```

---

## Troubleshooting

### Error `Address already in use` al iniciar el Backend
Los contenedores pre-compilados de `api` o `dashboard` siguen corriendo. Detenlos:
```bash
docker stop saleor-platform-api-1 saleor-platform-worker-1 saleor-platform-dashboard-1
```

### Error `ERESOLVE` al hacer `npm install` en el Dashboard
Usa la flag `--legacy-peer-deps`:
```bash
npm install --legacy-peer-deps
```

### Error `signal: aborted (core dumped)` en Docker (Linux)
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
cd saleor-platform && docker compose up -d db
```
