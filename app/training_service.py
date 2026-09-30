"""Lógica de días, sesiones, registros de series y progreso por usuaria."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone

from sqlalchemy.orm import Session, joinedload

from app.exercise_catalog import (
    BRAND_STATUS_LABELS,
    EQUIPMENT_LABELS,
    EVERKINETIC_CREDIT,
    MUSCLE_GROUPS,
)
from app.models import (
    EquipmentType,
    Exercise,
    Machine,
    SharedWorkout,
    UserEquipmentPref,
    UserExerciseLog,
    WorkoutSession,
    WorkoutTemplate,
    WorkoutTemplateExercise,
)

# Colombia no usa horario de verano.
BOGOTA_TZ = timezone(timedelta(hours=-5), "America/Bogota")
SESSION_REUSE_HOURS = 12
SECONDS_PER_REP = 4
SETUP_SECONDS = 60
EQUIPMENT_KEYS = tuple(EQUIPMENT_LABELS.keys())


def equipment_key(eq: EquipmentType | str) -> str:
    value = eq.value if isinstance(eq, EquipmentType) else str(eq)
    return "machine" if value == EquipmentType.nautilus_machine.value else value


def is_cardio(exercise: Exercise) -> bool:
    return equipment_key(exercise.equipment_type) == "cardio"


def to_local(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(BOGOTA_TZ)


def format_day(dt: datetime) -> str:
    months = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    local = to_local(dt)
    return f"{local.day} {months[local.month - 1]} {local.year}"


def format_kg(value: float) -> str:
    return f"{value:g}"


# ------------------------------------------------------------------ Mi gym
def enabled_equipment(db: Session, user_id: int) -> set[str]:
    disabled = {
        row.equipment_type
        for row in db.query(UserEquipmentPref).filter(
            UserEquipmentPref.user_id == user_id,
            UserEquipmentPref.enabled.is_(False),
        )
    }
    return {key for key in EQUIPMENT_KEYS if key not in disabled}


def set_enabled_equipment(db: Session, user_id: int, enabled: set[str]) -> None:
    existing = {
        row.equipment_type: row
        for row in db.query(UserEquipmentPref).filter(UserEquipmentPref.user_id == user_id)
    }
    for key in EQUIPMENT_KEYS:
        row = existing.get(key)
        if row is None:
            row = UserEquipmentPref(user_id=user_id, equipment_type=key)
            db.add(row)
        row.enabled = key in enabled


# ------------------------------------------------------------------ plantillas
def load_owned_template(db: Session, user_id: int, template_id: int) -> WorkoutTemplate | None:
    return (
        db.query(WorkoutTemplate)
        .options(
            joinedload(WorkoutTemplate.items)
            .joinedload(WorkoutTemplateExercise.exercise)
            .joinedload(Exercise.machine)
        )
        .filter(WorkoutTemplate.id == template_id, WorkoutTemplate.owner_user_id == user_id)
        .one_or_none()
    )


def visible_items(
    template: WorkoutTemplate, enabled: set[str]
) -> list[WorkoutTemplateExercise]:
    return [
        item
        for item in sorted(template.items, key=lambda i: i.sort_order)
        if item.exercise and equipment_key(item.exercise.equipment_type) in enabled
    ]


@dataclass
class RoutineItems:
    items: list[WorkoutTemplateExercise]
    hidden_count: int
    # Rutina compartida cuyo equipo no está en Mi gym: se muestra completa en vez de vacía.
    showing_all: bool = False


def routine_items(template: WorkoutTemplate, enabled: set[str], shared: bool) -> RoutineItems:
    items = visible_items(template, enabled)
    if items or not shared:
        return RoutineItems(items, len(template.items) - len(items))
    everything = [i for i in sorted(template.items, key=lambda i: i.sort_order) if i.exercise]
    return RoutineItems(everything, 0, showing_all=bool(everything))


def shared_for_clone(db: Session, template_id: int) -> SharedWorkout | None:
    return (
        db.query(SharedWorkout)
        .options(joinedload(SharedWorkout.from_user))
        .filter(SharedWorkout.cloned_template_id == template_id)
        .one_or_none()
    )


def prescription(item: WorkoutTemplateExercise) -> str:
    if is_cardio(item.exercise):
        return f"{item.duration_min or 5} min"
    base = f"{item.default_sets}x{item.default_reps}"
    if item.intensity_pct:
        return f"{base} · {item.intensity_pct}% del peso máximo"
    return base


def planned_units(item: WorkoutTemplateExercise) -> int:
    """Series planeadas, o minutos planeados para cardio."""
    if is_cardio(item.exercise):
        return item.duration_min or 5
    return max(item.default_sets, 1)


def estimated_minutes(items: list[WorkoutTemplateExercise]) -> int:
    total = 0
    for item in items:
        if is_cardio(item.exercise):
            total += (item.duration_min or 5) * 60 + SETUP_SECONDS
        else:
            per_set = item.default_reps * SECONDS_PER_REP + item.rest_seconds
            total += item.default_sets * per_set + SETUP_SECONDS
    return max(1, round(total / 60))


def format_duration(minutes: int) -> str:
    if minutes < 60:
        return f"~ {minutes} min"
    return f"~ {minutes // 60} h {minutes % 60:02d} min"


def image_url(exercise: Exercise, alt: bool = False) -> str:
    path = exercise.image_alt_path if alt else exercise.image_path
    if path:
        return f"/static/{path}"
    group = exercise.muscle_group if exercise.muscle_group in MUSCLE_GROUPS else "general"
    return f"/static/exercises/groups/{group}.svg"


def has_illustration(exercise: Exercise) -> bool:
    return bool(exercise.image_path)


def machine_label(machine: Machine | None) -> str:
    if machine is None:
        return ""
    if not machine.brand:
        return machine.name
    brand = machine.brand
    if machine.model:
        brand = f"{brand} {machine.model}"
    status = BRAND_STATUS_LABELS.get(machine.brand_status, machine.brand_status)
    if machine.brand_status == "confirmed":
        return f"{machine.name} · {brand}"
    return f"{machine.name} · {brand} ({status})"


# ------------------------------------------------------------------ sesiones
def latest_session(db: Session, user_id: int, template_id: int) -> WorkoutSession | None:
    return (
        db.query(WorkoutSession)
        .filter(WorkoutSession.user_id == user_id, WorkoutSession.template_id == template_id)
        .order_by(WorkoutSession.started_at.desc())
        .first()
    )


def start_or_resume_session(db: Session, user_id: int, template: WorkoutTemplate) -> WorkoutSession:
    current = latest_session(db, user_id, template.id)
    cutoff = datetime.now(UTC) - timedelta(hours=SESSION_REUSE_HOURS)
    if current and current.completed_at is None and to_local(current.started_at) >= to_local(
        cutoff
    ):
        return current
    shared = shared_for_clone(db, template.id)
    session = WorkoutSession(
        user_id=user_id,
        template_id=template.id,
        shared_workout_id=shared.id if shared else None,
    )
    db.add(session)
    db.flush()
    return session


def load_owned_session(db: Session, user_id: int, session_id: int) -> WorkoutSession | None:
    return (
        db.query(WorkoutSession)
        .filter(WorkoutSession.id == session_id, WorkoutSession.user_id == user_id)
        .one_or_none()
    )


def session_logs(db: Session, session_id: int, user_id: int) -> list[UserExerciseLog]:
    return (
        db.query(UserExerciseLog)
        .filter(UserExerciseLog.session_id == session_id, UserExerciseLog.user_id == user_id)
        .order_by(UserExerciseLog.exercise_id, UserExerciseLog.set_number)
        .all()
    )


def done_units(item: WorkoutTemplateExercise, logs: list[UserExerciseLog]) -> float:
    mine = [log for log in logs if log.exercise_id == item.exercise_id]
    if is_cardio(item.exercise):
        return sum(log.duration_min or 0 for log in mine)
    return float(len(mine))


def progress_percent(items: list[WorkoutTemplateExercise], logs: list[UserExerciseLog]) -> int:
    planned = sum(planned_units(item) for item in items)
    if not planned:
        return 0
    done = sum(min(done_units(item, logs), planned_units(item)) for item in items)
    return round(100 * done / planned)


def template_progress(db: Session, user_id: int, template: WorkoutTemplate,
                      items: list[WorkoutTemplateExercise]) -> tuple[int, WorkoutSession | None]:
    session = latest_session(db, user_id, template.id)
    if session is None:
        return 0, None
    return progress_percent(items, session_logs(db, session.id, user_id)), session


def next_set_number(db: Session, session_id: int, exercise_id: int) -> int:
    last = (
        db.query(UserExerciseLog.set_number)
        .filter(UserExerciseLog.session_id == session_id, UserExerciseLog.exercise_id == exercise_id)
        .order_by(UserExerciseLog.set_number.desc())
        .first()
    )
    return (last[0] if last else 0) + 1


# ------------------------------------------------------------------ historial y progreso
def estimated_one_rep_max(weight_kg: float, reps: int) -> float:
    """Fórmula de Epley; solo orientativa."""
    if weight_kg <= 0 or reps <= 0:
        return 0.0
    if reps == 1:
        return weight_kg
    return weight_kg * (1 + reps / 30)


@dataclass
class HistoryDay:
    label: str
    session_id: int
    sets: list[UserExerciseLog] = field(default_factory=list)
    best_1rm: float = 0.0
    max_weight: float = 0.0
    total_minutes: float = 0.0


def exercise_history(
    db: Session, user_id: int, exercise_id: int, exclude_session_id: int | None = None,
    limit_days: int = 20,
) -> list[HistoryDay]:
    query = (
        db.query(UserExerciseLog, WorkoutSession.started_at)
        .join(WorkoutSession, WorkoutSession.id == UserExerciseLog.session_id)
        .filter(UserExerciseLog.user_id == user_id, UserExerciseLog.exercise_id == exercise_id)
    )
    if exclude_session_id is not None:
        query = query.filter(UserExerciseLog.session_id != exclude_session_id)
    rows = query.order_by(WorkoutSession.started_at.desc(), UserExerciseLog.set_number.asc()).all()
    days: dict[int, HistoryDay] = {}
    for log, started_at in rows:
        day = days.get(log.session_id)
        if day is None:
            if len(days) >= limit_days:
                continue
            day = HistoryDay(label=format_day(started_at), session_id=log.session_id)
            days[log.session_id] = day
        day.sets.append(log)
        day.best_1rm = max(day.best_1rm, estimated_one_rep_max(log.weight_kg, log.reps))
        day.max_weight = max(day.max_weight, log.weight_kg)
        day.total_minutes += log.duration_min or 0
    return list(days.values())


def best_one_rep_max(history: list[HistoryDay]) -> float:
    return max((day.best_1rm for day in history), default=0.0)


def recommended_kg(one_rm: float, pct: int | None) -> float | None:
    if not one_rm or not pct:
        return None
    return round(one_rm * pct / 100 / 2.5) * 2.5


@dataclass
class ProgressChart:
    width: int
    height: int
    points: str
    dots: list[tuple[float, float, str]]
    y_min_label: str
    y_max_label: str
    x_first_label: str
    x_last_label: str
    metric_label: str


def progress_chart(history: list[HistoryDay], cardio: bool) -> ProgressChart | None:
    ordered = list(reversed(history))
    if cardio:
        values = [day.total_minutes for day in ordered]
        metric = "Minutos por sesión"
        unit = "min"
    else:
        values = [round(day.best_1rm, 1) for day in ordered]
        metric = "Peso máximo estimado (kg)"
        unit = "kg"
    pairs = [(day, v) for day, v in zip(ordered, values, strict=True) if v > 0]
    if not pairs:
        return None
    width, height, pad_x, pad_y = 320, 160, 28, 18
    lo = min(v for _, v in pairs)
    hi = max(v for _, v in pairs)
    if hi == lo:
        lo, hi = lo * 0.9, hi * 1.1 or 1
    span_x = max(len(pairs) - 1, 1)
    coords: list[tuple[float, float, str]] = []
    for idx, (day, value) in enumerate(pairs):
        x = pad_x + (width - 2 * pad_x) * (idx / span_x if len(pairs) > 1 else 0.5)
        y = height - pad_y - (height - 2 * pad_y) * (value - lo) / (hi - lo)
        coords.append((round(x, 1), round(y, 1), f"{day.label}: {value:g} {unit}"))
    return ProgressChart(
        width=width,
        height=height,
        points=" ".join(f"{x},{y}" for x, y, _ in coords),
        dots=coords,
        y_min_label=f"{lo:.0f}",
        y_max_label=f"{hi:.0f}",
        x_first_label=pairs[0][0].label,
        x_last_label=pairs[-1][0].label,
        metric_label=metric,
    )


def image_credit_line(exercise: Exercise) -> bool:
    return exercise.image_credit == EVERKINETIC_CREDIT
