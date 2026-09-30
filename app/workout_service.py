from datetime import UTC, datetime

from sqlalchemy.orm import Session, joinedload

from app.models import (
    SharedWorkout,
    SharedWorkoutStatus,
    WorkoutTemplate,
    WorkoutTemplateExercise,
)


def clone_template(db: Session, source: WorkoutTemplate, new_owner_id: int) -> WorkoutTemplate:
    clone = WorkoutTemplate(
        owner_user_id=new_owner_id,
        title=source.title,
        description=source.description,
        focus=source.focus,
        day_number=source.day_number,
    )
    db.add(clone)
    db.flush()
    for item in sorted(source.items, key=lambda x: x.sort_order):
        db.add(
            WorkoutTemplateExercise(
                template_id=clone.id,
                exercise_id=item.exercise_id,
                sort_order=item.sort_order,
                default_sets=item.default_sets,
                default_reps=item.default_reps,
                intensity_pct=item.intensity_pct,
                duration_min=item.duration_min,
                rest_seconds=item.rest_seconds,
            )
        )
    db.flush()
    return clone


def accept_shared_workout(db: Session, shared: SharedWorkout) -> WorkoutTemplate:
    source = (
        db.query(WorkoutTemplate)
        .options(joinedload(WorkoutTemplate.items))
        .filter(WorkoutTemplate.id == shared.source_template_id)
        .one()
    )
    clone = clone_template(db, source, shared.to_user_id)
    shared.status = SharedWorkoutStatus.accepted
    shared.cloned_template_id = clone.id
    shared.accepted_at = datetime.now(UTC)
    return clone


def user_owns_template(db: Session, user_id: int, template_id: int) -> bool:
    tpl = (
        db.query(WorkoutTemplate)
        .filter(WorkoutTemplate.id == template_id, WorkoutTemplate.owner_user_id == user_id)
        .one_or_none()
    )
    return tpl is not None
