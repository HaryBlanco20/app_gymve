# `.env` y Docker — problemas frecuentes

## Docker: `The "xxx" variable is not set`

Docker Compose interpreta `$` en el `.env`. Contraseñas con `$` deben:

- evitarse en `POSTGRES_PASSWORD` y `GYMVE_APP_DB_PASSWORD`, **o**
- escribirse con `$$` por cada `$` en esas líneas; en `DATABASE_URL`, `$` → `%24`.

## `unexpected character` en `.env`

Solo líneas `CLAVE=valor`. Nombres en `GYMVE_USER_N_NAME=`, hashes en `GYMVE_USER_N_PASSWORD_HASH=$2b$...`.

## `password authentication failed for user "gymve_app"`

Tras cambiar contraseñas o un `make dev-up` fallido, reinicia el volumen (solo desarrollo, sin datos importantes):

```bash
docker compose down -v
make dev-up
```
