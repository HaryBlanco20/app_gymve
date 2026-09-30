"""Plantillas compartidas: copia por receptora que refleja la original de la dueña.

La receptora tiene su propia plantilla (sesiones y registros cuelgan de ella), pero
su contenido es un espejo de la original. `sync_shared_copy` la reconcilia cada vez
que se lee comparando una firma de la original, así que cualquier vía de edición
(API, `seed_workouts.py`, SQL) se refleja. Los registros no dependen de las filas de
la plantilla sino de sesión + ejercicio, por lo que quitar un ejercicio no los toca.
Si la dueña borra la original, la copia deja de sincronizarse y queda fija.
"""

from datetime import UTC, datetime
from types import SimpleNamespace

from sqlalchemy.orm import Session, joinedload

from app.models import (
    SharedWorkout,
    SharedWorkoutStatus,
    WorkoutTemplate,
    WorkoutTemplateExercise,
)

HEADER_FIELDS = ("title", "description", "focus", "day_number")
ITEM_FIELDS = (
    "default_sets", "default_reps", "intensity_pct", "duration_min", "rest_seconds", "note",
)


def _ordered(template: WorkoutTemplate) -> list[WorkoutTemplateExercise]:
    return sorted(template.items, key=lambda i: (i.sort_order, i.id or 0))


def _signature(template: WorkoutTemplate) -> tuple:
    return (
        tuple(getattr(template, f) for f in HEADER_FIELDS),
        tuple(
            (i.exercise_id, i.sort_order, *(getattr(i, f) for f in ITEM_FIELDS))
            for i in _ordered(template)
        ),
    )


def _copy_items(source: WorkoutTemplate, target: WorkoutTemplate) -> None:
    wanted = _ordered(source)
    keep = {i.exercise_id for i in wanted}
    for item in list(target.items):
        if item.exercise_id not in keep:
            target.items.remove(item)
    existing = {i.exercise_id: i for i in target.items}
    for src in wanted:
        dst = existing.get(src.exercise_id)
        if dst is None:
            dst = WorkoutTemplateExercise(exercise_id=src.exercise_id)
            target.items.append(dst)
        dst.sort_order = src.sort_order
        for f in ITEM_FIELDS:
            setattr(dst, f, getattr(src, f))
    for f in HEADER_FIELDS:
        setattr(target, f, getattr(source, f))


def clone_template(db: Session, source: WorkoutTemplate, new_owner_id: int) -> WorkoutTemplate:
    clone = WorkoutTemplate(owner_user_id=new_owner_id, title=source.title)
    db.add(clone)
    _copy_items(source, clone)
    db.flush()
    return clone


def sync_shared_copy(db: Session, share: SharedWorkout) -> bool:
    """Alinea la copia de la receptora con la original. Devuelve True si cambió."""
    if share.status != SharedWorkoutStatus.accepted or share.cloned_template_id is None:
        return False
    source = db.get(WorkoutTemplate, share.source_template_id)
    clone = db.get(WorkoutTemplate, share.cloned_template_id)
    if source is None or clone is None or source.deleted_at or clone.deleted_at:
        return False
    if _signature(source) == _signature(clone):
        return False
    # Evita que dos peticiones simultáneas reconcilien la misma copia a la vez.
    db.query(SharedWorkout).filter(SharedWorkout.id == share.id).with_for_update().one()
    db.expire(source)
    db.expire(clone)
    if _signature(source) == _signature(clone):
        db.commit()
        return False
    _copy_items(source, clone)
    share.source_updated_at = datetime.now(UTC)
    db.commit()
    return True


def sync_copy_of_template(db: Session, template_id: int) -> None:
    share = (
        db.query(SharedWorkout)
        .filter(SharedWorkout.cloned_template_id == template_id)
        .one_or_none()
    )
    if share is not None:
        sync_shared_copy(db, share)


def sync_copies_of_source(db: Session, source_id: int) -> int:
    shares = (
        db.query(SharedWorkout)
        .filter(
            SharedWorkout.source_template_id == source_id,
            SharedWorkout.status == SharedWorkoutStatus.accepted,
        )
        .all()
    )
    return sum(1 for share in shares if sync_shared_copy(db, share))


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


def received_shares(db: Session, user_id: int) -> list[SharedWorkout]:
    """Pendientes y aceptadas de la usuaria, con la copia ya reconciliada."""
    rows = (
        db.query(SharedWorkout)
        .options(
            joinedload(SharedWorkout.from_user),
            joinedload(SharedWorkout.source_template).joinedload(WorkoutTemplate.items),
        )
        .filter(
            SharedWorkout.to_user_id == user_id,
            SharedWorkout.status.in_(
                [SharedWorkoutStatus.pending, SharedWorkoutStatus.accepted]
            ),
        )
        .order_by(SharedWorkout.created_at.desc())
        .all()
    )
    result: list[SharedWorkout] = []
    for row in rows:
        source_deleted = bool(row.source_template and row.source_template.deleted_at)
        if row.status == SharedWorkoutStatus.pending:
            if not source_deleted:
                result.append(row)
            continue
        if row.cloned_template_id is None and not source_deleted:
            row.cloned_template_id = clone_template(db, row.source_template, user_id).id
            db.commit()
        else:
            sync_shared_copy(db, row)
        result.append(row)
    return result


def shared_clone_ids(db: Session, user_id: int) -> set[int]:
    return {
        row[0]
        for row in db.query(SharedWorkout.cloned_template_id).filter(
            SharedWorkout.to_user_id == user_id,
            SharedWorkout.cloned_template_id.is_not(None),
        )
    }


def is_shared_copy(db: Session, template_id: int) -> bool:
    return (
        db.query(SharedWorkout.id)
        .filter(SharedWorkout.cloned_template_id == template_id)
        .first()
        is not None
    )


def replace_template_items(
    db: Session, template: WorkoutTemplate, items: list[dict], title: str | None = None
) -> None:
    """Reemplaza la lista de ejercicios (el orden de `items` es el nuevo orden)."""
    draft = SimpleNamespace(
        title=title or template.title,
        description=template.description,
        focus=template.focus,
        day_number=template.day_number,
        items=[SimpleNamespace(id=None, sort_order=idx, **spec) for idx, spec in enumerate(items)],
    )
    _copy_items(draft, template)
    db.flush()


def create_template(
    db: Session, owner_id: int, title: str, items: list[dict], focus: str = ""
) -> WorkoutTemplate:
    template = WorkoutTemplate(owner_user_id=owner_id, title=title, focus=focus, description="")
    db.add(template)
    replace_template_items(db, template, items, title)
    return template


def duplicate_template(db: Session, source: WorkoutTemplate, owner_id: int) -> WorkoutTemplate:
    copy = clone_template(db, source, owner_id)
    copy.title = f"{source.title} (copia)"[:160]
    copy.day_number = None
    return copy


def accepted_copies_count(db: Session, source_id: int) -> int:
    return (
        db.query(SharedWorkout)
        .filter(
            SharedWorkout.source_template_id == source_id,
            SharedWorkout.status == SharedWorkoutStatus.accepted,
        )
        .count()
    )


def soft_delete_template(db: Session, template: WorkoutTemplate) -> None:
    template.deleted_at = datetime.now(UTC)


def user_owns_template(db: Session, user_id: int, template_id: int) -> bool:
    tpl = (
        db.query(WorkoutTemplate)
        .filter(
            WorkoutTemplate.id == template_id,
            WorkoutTemplate.owner_user_id == user_id,
            WorkoutTemplate.deleted_at.is_(None),
        )
        .one_or_none()
    )
    return tpl is not None
