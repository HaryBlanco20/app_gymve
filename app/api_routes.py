from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app.auth import authenticate_user
from app.config import password_meets_policy
from app.db import get_db
from app.models import (
    Machine,
    SharedWorkout,
    SharedWorkoutStatus,
    User,
    UserExerciseLog,
    WorkoutTemplate,
)
from app.rate_limit import limiter, login_rate_limit
from app.schemas import (
    EquipmentPrefsRequest,
    LoginRequest,
    LoginResponse,
    LogSetRequest,
    LogSetResponse,
    MachineUpdateRequest,
    SharedStatusSchema,
    SharedWorkoutItem,
    SharedWorkoutListResponse,
    ShareWorkoutRequest,
    ShareWorkoutResponse,
    StartSessionResponse,
    UserProfile,
)
from app.security import (
    create_access_token,
    get_current_api_user,
    get_current_user_hybrid,
    get_user_by_email,
)
from app.training_service import (
    enabled_equipment,
    is_cardio,
    load_owned_session,
    load_owned_template,
    next_set_number,
    set_enabled_equipment,
    start_or_resume_session,
    visible_items,
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


@router.post("/workouts/{template_id}/start", response_model=StartSessionResponse)
def start_workout(
    template_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user_hybrid),
) -> StartSessionResponse:
    template = load_owned_template(db, current.id, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Rutina no encontrada.")
    if not visible_items(template, enabled_equipment(db, current.id)):
        raise HTTPException(
            status_code=400,
            detail="Ningún ejercicio coincide con el equipo activo en Mi gym.",
        )
    session = start_or_resume_session(db, current.id, template)
    db.commit()
    return StartSessionResponse(
        session_id=session.id,
        url=f"/app/session/{session.id}/exercise/1",
    )


def _owned_session_or_404(db: Session, user: User, session_id: int):
    session = load_owned_session(db, user.id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    return session


@router.post("/sessions/{session_id}/sets", response_model=LogSetResponse)
def log_set(
    session_id: int,
    body: LogSetRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user_hybrid),
) -> LogSetResponse:
    session = _owned_session_or_404(db, current, session_id)
    template = load_owned_template(db, current.id, session.template_id)
    item = next(
        (i for i in (template.items if template else []) if i.exercise_id == body.exercise_id),
        None,
    )
    if item is None:
        raise HTTPException(status_code=400, detail="El ejercicio no pertenece a esta rutina.")
    if is_cardio(item.exercise):
        if not body.duration_min:
            raise HTTPException(status_code=400, detail="Indica los minutos.")
        weight, reps, minutes = 0.0, 0, body.duration_min
    else:
        if body.reps < 1:
            raise HTTPException(status_code=400, detail="Indica las repeticiones.")
        weight, reps, minutes = body.weight_kg, body.reps, None
    log = UserExerciseLog(
        session_id=session.id,
        user_id=current.id,
        exercise_id=item.exercise_id,
        set_number=next_set_number(db, session.id, item.exercise_id),
        weight_kg=weight,
        reps=reps,
        duration_min=minutes,
    )
    db.add(log)
    session.completed_at = None
    db.commit()
    db.refresh(log)
    return LogSetResponse(
        id=log.id,
        set_number=log.set_number,
        weight_kg=log.weight_kg,
        reps=log.reps,
        duration_min=log.duration_min,
    )


@router.post("/sessions/{session_id}/sets/{log_id}/delete")
def delete_set(
    session_id: int,
    log_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user_hybrid),
) -> dict[str, str]:
    session = _owned_session_or_404(db, current, session_id)
    deleted = (
        db.query(UserExerciseLog)
        .filter(
            UserExerciseLog.id == log_id,
            UserExerciseLog.session_id == session.id,
            UserExerciseLog.user_id == current.id,
        )
        .delete()
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Serie no encontrada.")
    db.commit()
    return {"status": "ok"}


@router.post("/sessions/{session_id}/complete")
def complete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user_hybrid),
) -> dict[str, str]:
    session = _owned_session_or_404(db, current, session_id)
    session.completed_at = datetime.now(UTC)
    db.commit()
    return {"status": "ok", "url": f"/app/workouts/{session.template_id}"}


@router.post("/me/equipment")
def update_equipment(
    body: EquipmentPrefsRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user_hybrid),
) -> dict[str, list[str]]:
    enabled = {item.value for item in body.enabled}
    set_enabled_equipment(db, current.id, enabled)
    db.commit()
    return {"enabled": sorted(enabled)}


@router.post("/machines/{machine_id}")
def update_machine(
    machine_id: int,
    body: MachineUpdateRequest,
    db: Session = Depends(get_db),
    _current: User = Depends(get_current_user_hybrid),
) -> dict[str, str | None]:
    machine = db.query(Machine).filter(Machine.id == machine_id).one_or_none()
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina no encontrada.")
    machine.brand = body.brand.strip() or None
    machine.model = body.model.strip() or None
    if not machine.brand:
        machine.brand_status = "unknown"
    else:
        machine.brand_status = "confirmed" if body.confirmed else "probable"
    db.commit()
    return {
        "brand": machine.brand,
        "model": machine.model,
        "brand_status": machine.brand_status,
    }
