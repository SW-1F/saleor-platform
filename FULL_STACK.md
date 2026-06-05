# Stack completo con Docker (`docker-compose.full.yml`)

El `docker-compose.yml` por defecto solo levanta **infraestructura** (db, cache,
mailpit) y se espera correr la API y el dashboard de forma nativa.

`docker-compose.full.yml` es una alternativa que levanta **todo en Docker**
(API + worker + dashboard + infraestructura) con un solo comando. Es autónomo:
no necesita `common.env`.

## Servicios

- `db` — Postgres 15
- `cache` — Valkey 8.1 (compatible con Redis, para Celery)
- `mailpit` — captura de correos (UI: http://localhost:8025)
- `api` — Saleor Core, imagen oficial `ghcr.io/saleor/saleor:3.23` (alineada al dashboard 3.23) → http://localhost:8000/graphql/
- `worker` — Celery (tareas en segundo plano)
- `dashboard` — panel de administración (dev server de Vite) → http://localhost:9000

## Puesta en marcha

Todo se inicializa solo. Basta con:

```bash
docker compose -f docker-compose.full.yml up
```

El servicio `init` se ejecuta una vez y, antes de levantar `api`/`worker`, hace:

1. `migrate` (migraciones de la base de datos),
2. `populatedb --createsuperuser` **solo si la base está vacía** (no duplica
   datos; crea el admin `admin@example.com` / `admin`),
3. el mock de cupones (`scripts/mock_voucher_usage.py`).

El dashboard tarda 1-3 min la primera vez (Vite optimiza dependencias). Espera
a ver `VITE ... ready` en `docker compose -f docker-compose.full.yml logs -f dashboard`.

Accesos: dashboard http://localhost:9000 · API http://localhost:8000/graphql/ · Mailpit http://localhost:8025

## Mockear cupones con uso (`scripts/mock_voucher_usage.py`)

Con `docker-compose.full.yml` esto **ya corre solo** (servicio `init`). Lo de
abajo es para re-ejecutarlo manualmente, o para el compose normal con API nativa.
El mismo script sirve para ambos modos:

```bash
# Con docker-compose.full.yml (Linux/macOS o Windows con cmd/git-bash):
docker compose -f docker-compose.full.yml run --rm -T api \
  python3 manage.py shell < scripts/mock_voucher_usage.py

# Con el compose normal + API nativa (desde la carpeta saleor/):
python manage.py shell < ../scripts/mock_voucher_usage.py
```

En **PowerShell** el operador `<` no existe; usa `Get-Content` con una tubería:

```powershell
Get-Content scripts/mock_voucher_usage.py | `
  docker compose -f docker-compose.full.yml run --rm -T api python3 manage.py shell
```

(Requiere haber corrido `populatedb` antes.)

## Notas de desarrollo

- El dashboard se monta por volumen. En Docker sobre Windows, el hot-reload de
  Vite puede no detectar cambios; si editas código y no se refleja, reinicia el
  contenedor: `docker compose -f docker-compose.full.yml restart dashboard`.
- Apagar conservando datos: `docker compose -f docker-compose.full.yml stop` /
  reanudar: `... start`. Evita `down -v` salvo que quieras empezar de cero
  (borra base de datos y dependencias cacheadas).
