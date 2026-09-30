# GymVe

Aplicación **Python** privada para la familia (**Samsung Android** + **iPhone iOS**), sin publicación en tiendas.

| Dispositivo | Cliente |
|-------------|---------|
| **Samsung** | APK **Flet** (`client/`) — sideload |
| **iPhone** | **Safari / PWA** — mismo backend `/login` |

> [`mobile/`](mobile/) (Expo + Supabase) está **obsoleto**; el stack canónico es FastAPI + Postgres + Flet + web PWA.

**Guías**

- [Instalar en celular (Samsung + iPhone)](docs/instalar-en-celular.md)
- [Emulador Android en Ubuntu (+ notas iPhone)](docs/emulador-android-ubuntu.md)
- [Seguridad](docs/seguridad.md)

## Quick start (Ubuntu)

```bash
cp .env.example .env
# Edita secretos, POSTGRES_* y hashes bcrypt de los 4 usuarios

make dev-up          # Postgres healthy → init_db → seed (idempotente)
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- Web / iPhone: `http://127.0.0.1:8000/login` (en iPhone real usa **HTTPS** — túnel o Caddy; ver docs).
- Health: `/health`
- Catálogo y plan de 5 días: `python scripts/seed_workouts.py` (idempotente; dueña = `GYMVE_SEED_OWNER_EMAIL` o el primer usuario).

## Pantallas de entrenamiento (PWA)

| Ruta | Qué hace |
|------|----------|
| `/app/workouts` | Días del plan con anillo de progreso + invitaciones compartidas |
| `/app/workouts/{id}` | Día: ejercicios, tiempo estimado, **Comenzar** y **Compartir** |
| `/app/session/{id}/exercise/{n}` | Registro de series (kg × reps o minutos), descanso con cuenta atrás, historial |
| `/app/exercises`, `/app/exercises/{id}` | Catálogo y ficha: Info / Músculos / Historial / Progreso |
| `/app/gym` | «Mi gym»: equipo activo (filtra rutinas) y marca/modelo de cada máquina |

Cada persona solo ve sus propios registros; una rutina compartida copia la lista de ejercicios, no los pesos.
Ilustraciones y licencias: [docs/creditos-imagenes.md](docs/creditos-imagenes.md).

HTTPS local opcional: certificados en `docker/caddy/certs/` → `make dev-proxy`.

## Samsung (APK) vs iPhone (PWA)

| | Samsung | iPhone |
|---|---------|--------|
| Instalación | `flet build apk` + sideload | Safari → **Añadir a pantalla de inicio** |
| Dev en Ubuntu | Emulador Android + `adb` | **iPhone físico** + URL HTTPS (no simulador iOS) |
| Auth API | JWT (`/api/v1/login`) | Cookie de sesión web |

```bash
./scripts/build-and-install-apk.sh   # Samsung / emulador
```

## Seguridad (resumen)

- `GYMVE_ENV=production` exige secretos fuertes y `CORS_ORIGINS` explícitos.
- Rate limit en login; política de contraseña en servidor.
- `./scripts/security-check.sh`

Detalle: [docs/seguridad.md](docs/seguridad.md).

## Emulador Android

Requisitos: KVM, SDK Android, licencias aceptadas. Ver [docs/emulador-android-ubuntu.md](docs/emulador-android-ubuntu.md).

```bash
export ANDROID_AVD=Pixel_7_API_34
./scripts/run-android-emulator.sh
```

## API (cliente Flet)

```text
POST /api/v1/login   {"email","password"}  → access_token
GET  /api/v1/me      Authorization: Bearer …
POST /api/v1/workouts/{id}/start               → session_id, url
POST /api/v1/sessions/{id}/sets                {"exercise_id","weight_kg","reps"} o {"exercise_id","duration_min"}
POST /api/v1/sessions/{id}/sets/{log_id}/delete
POST /api/v1/sessions/{id}/complete
POST /api/v1/me/equipment                      {"enabled":["machine","cable","smith","dumbbell","cardio"]}
POST /api/v1/machines/{id}                     {"brand","model","confirmed"}
```

Con cookie de sesión, las peticiones POST deben ser JSON y del mismo origen (cabecera `Origin`).

## Estructura

```text
app/                 FastAPI + plantillas PWA
client/              Flet (APK Samsung)
docker/              Postgres init, Caddy
scripts/             dev-up, seed, emulador, security-check
docs/
mobile/              Legacy Expo (deprecated)
```

## Calidad

```bash
pip install ruff
make lint
make compose-config
```

## Producción (checklist)

1. `GYMVE_ENV=production`, secretos rotados, `CORS_ORIGINS` con HTTPS del túnel/dominio.
2. Postgres con contraseñas fuertes; backups del volumen `gymve_pgdata`.
3. HTTPS delante del API (Caddy, nginx o túnel).
4. Esquema: [docs/schema-versioning.md](docs/schema-versioning.md).

Licencia: uso privado familiar.
