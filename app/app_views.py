from dataclasses import dataclass

from sqlalchemy.orm import Session, joinedload

from app.models import (
    SharedWorkout,
    SharedWorkoutStatus,
    User,
    WorkoutTemplate,
    WorkoutTemplateExercise,
)


@dataclass
class TemplateCard:
    id: int
    title: str
    focus: str
    exercise_count: int
    exercise_names: list[str]


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


def _template_cards(db: Session, user_id: int) -> list[TemplateCard]:
    templates = (
        db.query(WorkoutTemplate)
        .options(
            joinedload(WorkoutTemplate.items).joinedload(WorkoutTemplateExercise.exercise)
        )
        .filter(WorkoutTemplate.owner_user_id == user_id)
        .order_by(WorkoutTemplate.created_at.desc())
        .all()
    )
    cards: list[TemplateCard] = []
    for tpl in templates:
        names = [item.exercise.name for item in tpl.items if item.exercise]
        cards.append(
            TemplateCard(
                id=tpl.id,
                title=tpl.title,
                focus=tpl.focus or "general",
                exercise_count=len(tpl.items),
                exercise_names=names,
            )
        )
    return cards


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
    family_users = (
        db.query(User)
        .filter(User.id != user.id)
        .order_by(User.display_name.asc())
        .all()
    )
    return {
        "user": {"email": user.email, "display_name": user.display_name},
        "templates": templates,
        "shared_items": shared_items,
        "family_users": family_users,
        "active_tab": "workouts",
    }


def build_dashboard_context(db: Session, user: User) -> dict:
    templates = _template_cards(db, user.id)
    featured = templates[0] if templates else None
    pending = (
        db.query(SharedWorkout)
        .filter(
            SharedWorkout.to_user_id == user.id,
            SharedWorkout.status == SharedWorkoutStatus.pending,
        )
        .count()
    )
    return {
        "user": {"email": user.email, "display_name": user.display_name},
        "featured_template": featured,
        "templates_count": len(templates),
        "pending_shares": pending,
        "week_progress": 35,
        "day_progress": 0,
        "active_tab": "dashboard",
    }
