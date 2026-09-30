from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app.api_routes import router as api_router
from app.app_views import (
    build_catalog_context,
    build_dashboard_context,
    build_day_context,
    build_exercise_info_context,
    build_gym_context,
    build_session_exercise_context,
    build_workouts_context,
)
from app.auth import authenticate_user
from app.config import (
    get_app_host,
    get_app_port,
    get_cors_origins,
    get_session_secret,
    normalize_email,
    password_meets_policy,
    session_https_only,
    validate_security_config,
)
from app.db import engine, get_db
from app.middleware_security import SecurityHeadersMiddleware
from app.models import User
from app.rate_limit import limiter, login_rate_limit
from app.schema_upgrade import upgrade_schema
from app.training_service import load_owned_session

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_security_config()
    upgrade_schema(engine)
    yield


app = FastAPI(title="GymVe", docs_url=None, redoc_url=None, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=get_session_secret(),
    https_only=session_https_only(),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(api_router)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def _session_user(request: Request, db: Session) -> dict | None:
    email = request.session.get("email")
    if not email:
        return None
    user = db.query(User).filter(User.email == normalize_email(email)).one_or_none()
    if not user:
        request.session.clear()
        return None
    return {"email": user.email, "display_name": user.display_name}


def _require_user(request: Request, db: Session) -> User | None:
    email = request.session.get("email")
    if not email:
        return None
    return db.query(User).filter(User.email == normalize_email(email)).one_or_none()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    if _session_user(request, db):
        return RedirectResponse(url="/app/dashboard", status_code=303)
    return RedirectResponse(url="/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    if _session_user(request, db):
        return RedirectResponse(url="/app/dashboard", status_code=303)
    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": None, "user": None},
    )


@app.post("/login", response_class=HTMLResponse)
@limiter.limit(login_rate_limit())
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    ok, policy_msg = password_meets_policy(password)
    if not ok:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": policy_msg, "user": None, "email": email},
            status_code=400,
        )
    user = authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "error": "Correo o contraseña incorrectos.",
                "user": None,
                "email": email,
            },
            status_code=401,
        )
    request.session["email"] = user.email
    return RedirectResponse(url="/app/dashboard", status_code=303)


@app.get("/inicio", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    if not _session_user(request, db):
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url="/app/dashboard", status_code=303)


@app.get("/app/dashboard", response_class=HTMLResponse)
async def app_dashboard(request: Request, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    ctx = build_dashboard_context(db, user)
    return templates.TemplateResponse(request, "dashboard.html", ctx)


@app.get("/app/workouts", response_class=HTMLResponse)
async def app_workouts(request: Request, aceptada: int = 0, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    ctx = build_workouts_context(db, user, just_accepted=aceptada)
    return templates.TemplateResponse(request, "workouts.html", ctx)


def _login_redirect() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=303)


def _safe_back(value: str | None, default: str) -> str:
    if value and value.startswith("/app/") and "//" not in value and "\\" not in value:
        return value
    return default


@app.get("/app/workouts/{template_id}", response_class=HTMLResponse)
async def app_workout_day(template_id: int, request: Request, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if not user:
        return _login_redirect()
    ctx = build_day_context(db, user, template_id)
    if ctx is None:
        return RedirectResponse(url="/app/workouts", status_code=303)
    return templates.TemplateResponse(request, "workout_day.html", ctx)


@app.get("/app/session/{session_id}/exercise/{n}", response_class=HTMLResponse)
async def app_session_exercise(
    session_id: int, n: int, request: Request, db: Session = Depends(get_db)
):
    user = _require_user(request, db)
    if not user:
        return _login_redirect()
    session = load_owned_session(db, user.id, session_id)
    if session is None:
        return RedirectResponse(url="/app/workouts", status_code=303)
    ctx = build_session_exercise_context(db, user, session, n)
    if ctx is None:
        return RedirectResponse(url=f"/app/workouts/{session.template_id}", status_code=303)
    return templates.TemplateResponse(request, "session_exercise.html", ctx)


@app.get("/app/exercises", response_class=HTMLResponse)
async def app_exercises(request: Request, todo: int = 0, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if not user:
        return _login_redirect()
    ctx = build_catalog_context(db, user, show_all=bool(todo))
    return templates.TemplateResponse(request, "exercises.html", ctx)


@app.get("/app/exercises/{exercise_id}", response_class=HTMLResponse)
async def app_exercise_info(
    exercise_id: int,
    request: Request,
    tab: str = "info",
    back: str | None = None,
    db: Session = Depends(get_db),
):
    user = _require_user(request, db)
    if not user:
        return _login_redirect()
    ctx = build_exercise_info_context(
        db, user, exercise_id, tab, _safe_back(back, "/app/exercises")
    )
    if ctx is None:
        return RedirectResponse(url="/app/exercises", status_code=303)
    return templates.TemplateResponse(request, "exercise_info.html", ctx)


@app.get("/app/gym", response_class=HTMLResponse)
async def app_gym(request: Request, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if not user:
        return _login_redirect()
    return templates.TemplateResponse(request, "gym.html", build_gym_context(db, user))


@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/manifest.webmanifest")
async def manifest():
    return RedirectResponse(url="/static/manifest.webmanifest", status_code=307)


@app.get("/health")
async def health():
    return {"status": "ok"}


def run():
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=get_app_host(),
        port=get_app_port(),
        reload=False,
    )


if __name__ == "__main__":
    run()
