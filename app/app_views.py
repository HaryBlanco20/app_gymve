from dataclasses import dataclass

from sqlalchemy.orm import Session, joinedload

from app.exercise_catalog import (
    BRAND_STATUS_LABELS,
    EQUIPMENT_ICONS,
    EQUIPMENT_LABELS,
    MUSCLE_GROUPS,
)
from app.models import (
    Exercise,
    Machine,
    SharedWorkout,
    SharedWorkoutStatus,
    User,
    WorkoutTemplate,
    WorkoutTemplateExercise,
)
from app.training_service import (
    best_one_rep_max,
    enabled_equipment,
    equipment_key,
    estimated_minutes,
    exercise_history,
    format_duration,
    format_kg,
    has_illustration,
    image_credit_line,
    image_url,
    is_cardio,
    load_owned_template,
    machine_label,
    planned_units,
    prescription,
    progress_chart,
    recommended_kg,
    session_logs,
    template_progress,
    visible_items,
)


@dataclass
class TemplateCard:
    id: int
    title: str
    focus: str
    exercise_count: int
    exercise_names: list[str]
    day_number: int | None
    progress: int
    hidden_count: int


@dataclass
class SharedCardView:
    id: int
    status: str
    status_label: str
    template_title: str
    from_name: str
    to_name: str
    message: str
    direction_label: str
    can_accept: bool


def _user_ctx(user: User) -> dict:
    return {"email": user.email, "display_name": user.display_name}


def _template_cards(db: Session, user_id: int) -> list[TemplateCard]:
    templates = (
        db.query(WorkoutTemplate)
        .options(
            joinedload(WorkoutTemplate.items).joinedload(WorkoutTemplateExercise.exercise)
        )
        .filter(WorkoutTemplate.owner_user_id == user_id)
        .all()
    )
    templates.sort(
        key=lambda t: (t.day_number is None, t.day_number or 0, -t.created_at.timestamp())
    )
    enabled = enabled_equipment(db, user_id)
    cards: list[TemplateCard] = []
    for tpl in templates:
        items = visible_items(tpl, enabled)
        progress, _ = template_progress(db, user_id, tpl, items)
        cards.append(
            TemplateCard(
                id=tpl.id,
                title=tpl.title,
                focus=tpl.focus or "general",
                exercise_count=len(items),
                exercise_names=[item.exercise.name for item in items],
                day_number=tpl.day_number,
                progress=progress,
                hidden_count=len(tpl.items) - len(items),
            )
        )
    return cards


def _family_users(db: Session, user: User) -> list[User]:
    return db.query(User).filter(User.id != user.id).order_by(User.display_name.asc()).all()


def build_workouts_context(db: Session, user: User) -> dict:
    templates = _template_cards(db, user.id)
    shared_rows = (
        db.query(SharedWorkout)
        .options(
            joinedload(SharedWorkout.from_user),
            joinedload(SharedWorkout.to_user),
            joinedload(SharedWorkout.source_template),
        )
        .filter(
            (SharedWorkout.to_user_id == user.id) | (SharedWorkout.from_user_id == user.id)
        )
        .order_by(SharedWorkout.created_at.desc())
        .limit(20)
        .all()
    )
    status_labels = {
        "pending": "Pendiente",
        "accepted": "Aceptada",
        "declined": "Rechazada",
    }
    shared_items: list[SharedCardView] = []
    for row in shared_rows:
        direction_label = "Recibida" if row.to_user_id == user.id else "Enviada"
        shared_items.append(
            SharedCardView(
                id=row.id,
                status=row.status.value,
                status_label=status_labels.get(row.status.value, row.status.value),
                template_title=row.source_template.title if row.source_template else "",
                from_name=row.from_user.display_name if row.from_user else "",
                to_name=row.to_user.display_name if row.to_user else "",
                message=row.message,
                direction_label=direction_label,
                can_accept=(
                    row.to_user_id == user.id and row.status == SharedWorkoutStatus.pending
                ),
            )
        )
    return {
        "user": _user_ctx(user),
        "templates": templates,
        "shared_items": shared_items,
        "family_users": _family_users(db, user),
        "active_tab": "workouts",
    }


def build_dashboard_context(db: Session, user: User) -> dict:
    templates = _template_cards(db, user.id)
    featured = next((t for t in templates if t.progress < 100), templates[0] if templates else None)
    pending = (
        db.query(SharedWorkout)
        .filter(
            SharedWorkout.to_user_id == user.id,
            SharedWorkout.status == SharedWorkoutStatus.pending,
        )
        .count()
    )
    week_days = [t for t in templates if t.day_number]
    week_progress = (
        round(sum(t.progress for t in week_days) / len(week_days)) if week_days else 0
    )
    enabled = enabled_equipment(db, user.id)
    return {
        "user": _user_ctx(user),
        "featured_template": featured,
        "templates_count": len(templates),
        "pending_shares": pending,
        "week_progress": week_progress,
        "day_progress": featured.progress if featured else 0,
        "equipment": [
            {"label": EQUIPMENT_LABELS[k], "icon": EQUIPMENT_ICONS[k]}
            for k in EQUIPMENT_LABELS
            if k in enabled
        ],
        "active_tab": "dashboard",
    }


# ------------------------------------------------------------------ día de entrenamiento
def build_day_context(db: Session, user: User, template_id: int) -> dict | None:
    template = load_owned_template(db, user.id, template_id)
    if template is None:
        return None
    enabled = enabled_equipment(db, user.id)
    items = visible_items(template, enabled)
    progress, session = template_progress(db, user.id, template, items)
    logs = session_logs(db, session.id, user.id) if session else []
    rows = []
    for idx, item in enumerate(items, start=1):
        done = sum(1 for log in logs if log.exercise_id == item.exercise_id)
        rows.append(
            {
                "n": idx,
                "exercise": item.exercise,
                "image": image_url(item.exercise),
                "illustrated": has_illustration(item.exercise),
                "prescription": prescription(item),
                "done": done if not is_cardio(item.exercise) else None,
                "planned": planned_units(item),
            }
        )
    shared_from = (
        db.query(SharedWorkout)
        .options(joinedload(SharedWorkout.from_user))
        .filter(SharedWorkout.cloned_template_id == template.id)
        .one_or_none()
    )
    session_open = bool(session and session.completed_at is None and 0 < progress)
    return {
        "user": _user_ctx(user),
        "template": template,
        "rows": rows,
        "hidden_count": len(template.items) - len(items),
        "progress": progress,
        "estimated": format_duration(estimated_minutes(items)),
        "session_open": session_open,
        "resume_url": f"/app/session/{session.id}/exercise/1" if session_open else "",
        "family_users": _family_users(db, user),
        "shared_from": shared_from.from_user.display_name if shared_from else "",
        "active_tab": "workouts",
    }


# ------------------------------------------------------------------ registro de series
def build_session_exercise_context(db: Session, user: User, session, n: int) -> dict | None:
    template = load_owned_template(db, user.id, session.template_id)
    if template is None:
        return None
    items = visible_items(template, enabled_equipment(db, user.id))
    if not items or n < 1 or n > len(items):
        return None
    item = items[n - 1]
    exercise = item.exercise
    cardio = is_cardio(exercise)
    logs = session_logs(db, session.id, user.id)
    today_sets = [log for log in logs if log.exercise_id == exercise.id]
    history = exercise_history(db, user.id, exercise.id, exclude_session_id=session.id,
                               limit_days=5)
    all_history = exercise_history(db, user.id, exercise.id)
    one_rm = best_one_rep_max(all_history)
    suggestion = recommended_kg(one_rm, item.intensity_pct)
    last = today_sets[-1] if today_sets else (history[0].sets[-1] if history else None)
    planned = planned_units(item)
    done = (
        sum(log.duration_min or 0 for log in today_sets) if cardio else len(today_sets)
    )
    return {
        "user": _user_ctx(user),
        "session": session,
        "template": template,
        "item": item,
        "exercise": exercise,
        "group_label": MUSCLE_GROUPS.get(exercise.muscle_group, exercise.muscle_group),
        "image": image_url(exercise),
        "illustrated": has_illustration(exercise),
        "cardio": cardio,
        "n": n,
        "total": len(items),
        "planned": planned,
        "done": format_kg(done) if cardio else done,
        "done_ratio": min(float(done) / planned, 1.0) if planned else 0.0,
        "today_sets": today_sets,
        "history": history,
        "suggested_kg": format_kg(suggestion) if suggestion else "",
        "prefill_kg": format_kg(last.weight_kg) if last and not cardio else "",
        "prefill_reps": last.reps if last and not cardio else item.default_reps,
        "prefill_min": item.duration_min or 5,
        "machine": machine_label(exercise.machine),
        "prev_url": f"/app/session/{session.id}/exercise/{n - 1}" if n > 1 else "",
        "next_url": f"/app/session/{session.id}/exercise/{n + 1}" if n < len(items) else "",
        "day_url": f"/app/workouts/{template.id}",
        "format_kg": format_kg,
        "active_tab": "workouts",
    }


# ------------------------------------------------------------------ ficha del ejercicio
EXERCISE_TABS = ("info", "musculos", "historial", "progreso")


def build_exercise_info_context(db: Session, user: User, exercise_id: int, tab: str,
                                back: str) -> dict | None:
    exercise = (
        db.query(Exercise)
        .options(joinedload(Exercise.machine))
        .filter(Exercise.id == exercise_id)
        .one_or_none()
    )
    if exercise is None:
        return None
    if tab not in EXERCISE_TABS:
        tab = "info"
    cardio = is_cardio(exercise)
    history = exercise_history(db, user.id, exercise.id)
    return {
        "user": _user_ctx(user),
        "exercise": exercise,
        "group_label": MUSCLE_GROUPS.get(exercise.muscle_group, exercise.muscle_group),
        "equipment_label": EQUIPMENT_LABELS.get(equipment_key(exercise.equipment_type), ""),
        "machine": machine_label(exercise.machine),
        "image": image_url(exercise),
        "image_end": image_url(exercise, alt=True) if exercise.image_alt_path else "",
        "illustrated": has_illustration(exercise),
        "credit_everkinetic": image_credit_line(exercise),
        "steps": [s for s in exercise.instructions.splitlines() if s.strip()],
        "primary": [m.strip() for m in exercise.primary_muscles.split(",") if m.strip()],
        "secondary": [m.strip() for m in exercise.secondary_muscles.split(",") if m.strip()],
        "tab": tab,
        "tabs": [
            ("info", "Info"),
            ("musculos", "Músculos"),
            ("historial", "Historial"),
            ("progreso", "Progreso"),
        ],
        "cardio": cardio,
        "history": history,
        "chart": progress_chart(history, cardio),
        "one_rm": format_kg(round(best_one_rep_max(history), 1)),
        "back": back,
        "format_kg": format_kg,
        "active_tab": "exercises",
    }


def build_catalog_context(db: Session, user: User, show_all: bool) -> dict:
    enabled = enabled_equipment(db, user.id)
    exercises = db.query(Exercise).order_by(Exercise.name.asc()).all()
    groups = []
    hidden = 0
    for key, label in MUSCLE_GROUPS.items():
        rows = []
        for ex in exercises:
            if ex.muscle_group != key:
                continue
            if not show_all and equipment_key(ex.equipment_type) not in enabled:
                hidden += 1
                continue
            rows.append({"exercise": ex, "image": image_url(ex),
                         "illustrated": has_illustration(ex),
                         "equipment": EQUIPMENT_LABELS.get(equipment_key(ex.equipment_type), "")})
        if rows:
            groups.append({"key": key, "label": label, "rows": rows})
    return {
        "user": _user_ctx(user),
        "groups": groups,
        "hidden": hidden,
        "show_all": show_all,
        "active_tab": "exercises",
    }


# ------------------------------------------------------------------ Mi gym
def build_gym_context(db: Session, user: User) -> dict:
    enabled = enabled_equipment(db, user.id)
    machines = db.query(Machine).order_by(Machine.equipment_type, Machine.name).all()
    by_type: dict[str, list[Machine]] = {}
    for machine in machines:
        by_type.setdefault(equipment_key(machine.equipment_type), []).append(machine)
    return {
        "user": _user_ctx(user),
        "equipment": [
            {
                "key": key,
                "label": label,
                "icon": EQUIPMENT_ICONS[key],
                "enabled": key in enabled,
                "machines": by_type.get(key, []),
            }
            for key, label in EQUIPMENT_LABELS.items()
        ],
        "status_labels": BRAND_STATUS_LABELS,
        "active_tab": "gym",
    }
