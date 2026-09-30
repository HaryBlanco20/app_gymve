# Versionado del esquema (PostgreSQL)

Hoy GymVe crea el esquema con **SQLAlchemy** de forma idempotente:

- `python scripts/init_db.py` → `Base.metadata.create_all()`
- El arranque de FastAPI también llama a `create_all` en el lifespan (solo crea lo que falta; no altera columnas existentes).

- Columnas y valores de enum nuevos en tablas existentes: `app/schema_upgrade.py`
  (`ALTER TABLE … ADD COLUMN IF NOT EXISTS`, `ALTER TYPE … ADD VALUE IF NOT EXISTS`). Lo llaman
  `init_db.py`, `seed_workouts.py` y el arranque de FastAPI; es idempotente.

## Implicaciones

- **Desarrollo familiar:** suficiente para el tamaño actual del proyecto.
- **Cambios de columnas/tablas:** hay que aplicar migraciones SQL a mano o introducir **Alembic** antes de desplegar cambios incompatibles.

## Ruta recomendada si crece el proyecto

1. `pip install alembic` y `alembic init alembic`.
2. Apuntar `sqlalchemy.url` a `DATABASE_URL`.
3. Autogenerar revisiones tras cambiar `app/models.py`.
4. En producción: **solo** `alembic upgrade head` (no depender de `create_all`).

## Orden en despliegue

1. Postgres healthy (`docker compose up -d`).
2. Migraciones (hoy: `init_db.py`; futuro: Alembic).
3. `python scripts/seed_users.py` (idempotente por email).
4. Arrancar `uvicorn`.
