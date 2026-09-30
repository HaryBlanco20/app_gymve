from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import get_jwt_secret, normalize_email
from app.db import get_db
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7


def create_access_token(email: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": normalize_email(email),
        "iat": now,
        "exp": now + timedelta(days=JWT_EXPIRE_DAYS),
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        sub = payload.get("sub")
        return normalize_email(str(sub)) if sub else None
    except jwt.PyJWTError:
        return None


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == normalize_email(email)).one_or_none()


def get_current_api_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado.",
        )
    email = decode_access_token(credentials.credentials)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida o expirada.",
        )
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado.",
        )
    return user


SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def ensure_same_origin(request: Request) -> None:
    """Defensa CSRF para peticiones con cookie de sesión (además de SameSite=Lax)."""
    if request.method in SAFE_METHODS:
        return
    source = request.headers.get("origin") or request.headers.get("referer")
    if not source:
        return
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    if urlparse(source).netloc != host.split(",")[0].strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Origen no permitido.",
        )


def get_current_user_hybrid(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    session_email = request.session.get("email")
    if session_email:
        user = get_user_by_email(db, str(session_email))
        if user:
            ensure_same_origin(request)
            return user
    if credentials and credentials.scheme.lower() == "bearer":
        email = decode_access_token(credentials.credentials)
        if email:
            user = get_user_by_email(db, email)
            if user:
                return user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado.",
    )
