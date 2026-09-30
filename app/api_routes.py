from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app.auth import authenticate_user
from app.config import password_meets_policy
from app.db import get_db
from app.models import SharedWorkout, SharedWorkoutStatus, User, WorkoutTemplate
from app.rate_limit import limiter, login_rate_limit
from app.schemas import (
    LoginRequest,
    LoginResponse,
    SharedStatusSchema,
    SharedWorkoutItem,
    SharedWorkoutListResponse,
    ShareWorkoutRequest,
    ShareWorkoutResponse,
    UserProfile,
)
from app.security import (
    create_access_token,
    get_current_api_user,
    get_current_user_hybrid,
    get_user_by_email,
)
from app.workout_service import accept_shared_workout, user_owns_template

router = APIRouter(prefix="/api/v1", tags=["api"])


@router.post("/login", response_model=LoginResponse)
@limiter.limit(login_rate_limit())
def api_login(
    request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    ok, policy_msg = password_meets_policy(body.password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=policy_msg)
    user = authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        )
    token = create_access_token(user.email)
    return LoginResponse(
        access_token=token,
        email=user.email,
        display_name=user.display_name,
    )


@router.get("/me", response_model=UserProfile)
def api_me(current: User = Depends(get_current_api_user)) -> UserProfile:
    return UserProfile(email=current.email, display_name=current.display_name)


@router.post("/logout")
def api_logout(_current: User = Depends(get_current_api_user)) -> dict[str, str]:
    return {"status": "ok", "message": "Cierra sesión en el cliente eliminando el token."}


def _resolve_recipient(db: Session, body: ShareWorkoutRequest) -> User:
    if body.to_user_id is not None:
        user = db.query(User).filter(User.id == body.to_user_id).one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario destino no encontrado.")
        return user
    if body.to_email:
        user = get_user_by_email(db, body.to_email)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario destino no encontrado.")
        return user
    raise HTTPException(
        status_code=400,
        detail="Indica to_user_id o to_email.",
    )


@router.post("/workouts/share", response_model=ShareWorkoutResponse)
def share_workout(
    body: ShareWorkoutRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user_hybrid),
) -> ShareWorkoutResponse:
    if not user_owns_template(db, current.id, body.template_id):
        raise HTTPException(
            status_code=403,
            detail="Solo puedes compartir plantillas que te pertenecen.",
        )
    recipient = _resolve_recipient(db, body)
    if recipient.id == current.id:
        raise HTTPException(status_code=400, detail="No puedes compartir contigo mismo.")

    template = db.query(WorkoutTemplate).filter(WorkoutTemplate.id == body.template_id).one()
    shared = SharedWorkout(
        source_template_id=template.id,
        from_user_id=current.id,
        to_user_id=recipient.id,
        status=SharedWorkoutStatus.pending,
        message=body.message.strip(),
    )
    db.add(shared)
    db.commit()
    db.refresh(shared)
    return ShareWorkoutResponse(
        id=shared.id,
        status=SharedStatusSchema(shared.status.value),
        to_user_id=recipient.id,
        source_template_id=template.id,
    )


def _shared_item(shared: SharedWorkout, viewer_id: int) -> SharedWorkoutItem:
    direction = "received" if shared.to_user_id == viewer_id else "sent"
    return SharedWorkoutItem(
        id=shared.id,
        status=SharedStatusSchema(shared.status.value),
        message=shared.message,
        created_at=shared.created_at,
        accepted_at=shared.accepted_at,
        from_user_id=shared.from_user_id,
        from_display_name=shared.from_user.display_name if shared.from_user else "",
        to_user_id=shared.to_user_id,
        source_template_id=shared.source_template_id,
        source_template_title=(
            shared.source_template.title if shared.source_template else ""
        ),
        cloned_template_id=shared.cloned_template_id,
        direction=direction,
    )


@router.get("/workouts/shared", response_model=SharedWorkoutListResponse)
def list_shared_workouts(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user_hybrid),
) -> SharedWorkoutListResponse:
    rows = (
        db.query(SharedWorkout)
        .options(
            joinedload(SharedWorkout.from_user),
            joinedload(SharedWorkout.source_template),
        )
        .filter(
            (SharedWorkout.to_user_id == current.id) | (SharedWorkout.from_user_id == current.id)
        )
        .order_by(SharedWorkout.created_at.desc())
        .all()
    )
    return SharedWorkoutListResponse(items=[_shared_item(row, current.id) for row in rows])


@router.post("/workouts/shared/{shared_id}/accept", response_model=ShareWorkoutResponse)
def accept_share(
    shared_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user_hybrid),
) -> ShareWorkoutResponse:
    shared = (
        db.query(SharedWorkout)
        .filter(SharedWorkout.id == shared_id, SharedWorkout.to_user_id == current.id)
        .one_or_none()
    )
    if not shared:
        raise HTTPException(status_code=404, detail="Invitación no encontrada.")
    if shared.status != SharedWorkoutStatus.pending:
        raise HTTPException(status_code=400, detail="Esta invitación ya fue procesada.")
    accept_shared_workout(db, shared)
    db.commit()
    db.refresh(shared)
    return ShareWorkoutResponse(
        id=shared.id,
        status=SharedStatusSchema(shared.status.value),
        to_user_id=shared.to_user_id,
        source_template_id=shared.source_template_id,
    )
