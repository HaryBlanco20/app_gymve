#!/usr/bin/env python3
"""Catálogo GymVe (máquinas + ejercicios) y plan de 5 días para la usuaria principal.

Idempotente: actualiza máquinas y ejercicios por slug y reconstruye los ejercicios
de cada día por título. La usuaria principal es GYMVE_SEED_OWNER_EMAIL o, si no
está definida, el primer usuario creado.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import normalize_email
from app.db import SessionLocal, engine
from app.exercise_catalog import (
    EVERKINETIC_CREDIT,
    EXERCISES,
    MACHINES,
    PLAN_DAYS,
    PLAN_DESCRIPTION,
)
from app.models import (
    Exercise,
    Machine,
    User,
    WorkoutTemplate,
    WorkoutTemplateExercise,
)
from app.schema_upgrade import upgrade_schema

EK_DIR = ROOT / "app" / "static" / "exercises" / "everkinetic"


def upsert_machines(db) -> dict[str, Machine]:
    by_slug: dict[str, Machine] = {}
    for slug, name, eq, brand, status in MACHINES:
        row = db.query(Machine).filter(Machine.slug == slug).one_or_none()
        if row is None:
            row = Machine(slug=slug, name=name, equipment_type=eq, brand=brand,
                          brand_status=status)
            db.add(row)
        else:
            row.name = name
            row.equipment_type = eq
            # No pisar lo que la usuaria ya confirmó en la sede.
            if row.brand_status != "confirmed":
                row.brand = brand
                row.brand_status = status
        by_slug[slug] = row
    db.flush()
    return by_slug


def _image_paths(ek_id: str | None) -> tuple[str, str, str]:
    if not ek_id:
        return "", "", ""
    start = EK_DIR / f"{ek_id}-relaxation.png"
    end = EK_DIR / f"{ek_id}-tension.png"
    if not start.exists():
        return "", "", ""
    return (
        f"exercises/everkinetic/{start.name}",
        f"exercises/everkinetic/{end.name}" if end.exists() else "",
        EVERKINETIC_CREDIT,
    )


def upsert_exercises(db, machines: dict[str, Machine]) -> dict[str, Exercise]:
    by_slug: dict[str, Exercise] = {}
    for spec in EXERCISES:
        image_path, image_alt_path, credit = _image_paths(spec["ek_id"])
        values = {
            "name": spec["name"],
            "equipment_type": spec["equipment_type"],
            "muscle_group": spec["muscle_group"],
            "primary_muscles": spec["primary_muscles"],
            "secondary_muscles": spec["secondary_muscles"],
            "description": spec["description"],
            "instructions": spec["instructions"],
            "image_path": image_path,
            "image_alt_path": image_alt_path,
            "image_credit": credit,
            "machine_id": machines[spec["machine_slug"]].id if spec["machine_slug"] else None,
        }
        row = db.query(Exercise).filter(Exercise.slug == spec["slug"]).one_or_none()
        if row is None:
            row = Exercise(slug=spec["slug"], notes="", **values)
            db.add(row)
        else:
            for key, value in values.items():
                setattr(row, key, value)
        by_slug[spec["slug"]] = row
    db.flush()
    return by_slug


def resolve_owner(db) -> User | None:
    email = os.getenv("GYMVE_SEED_OWNER_EMAIL", "").strip()
    if email:
        return db.query(User).filter(User.email == normalize_email(email)).one_or_none()
    return db.query(User).order_by(User.id.asc()).first()


def ensure_plan(db, owner: User, exercises: dict[str, Exercise]) -> None:
    for day in PLAN_DAYS:
        template = (
            db.query(WorkoutTemplate)
            .filter(
                WorkoutTemplate.owner_user_id == owner.id,
                WorkoutTemplate.title == day["title"],
            )
            .one_or_none()
        )
        if template is None:
            template = WorkoutTemplate(owner_user_id=owner.id, title=day["title"])
            db.add(template)
            db.flush()
        else:
            db.query(WorkoutTemplateExercise).filter(
                WorkoutTemplateExercise.template_id == template.id
            ).delete()
        template.description = PLAN_DESCRIPTION
        template.focus = day["focus"]
        template.day_number = day["day"]
        for order, (slug, sets, reps, pct, minutes, rest) in enumerate(day["items"]):
            db.add(
                WorkoutTemplateExercise(
                    template_id=template.id,
                    exercise_id=exercises[slug].id,
                    sort_order=order,
                    default_sets=sets,
                    default_reps=reps,
                    intensity_pct=pct,
                    duration_min=minutes,
                    rest_seconds=rest,
                )
            )
        print(f"Día {day['day']}: «{day['title']}» (id={template.id}) para {owner.email}")


def main() -> None:
    upgrade_schema(engine)
    db = SessionLocal()
    try:
        machines = upsert_machines(db)
        exercises = upsert_exercises(db, machines)
        db.commit()
        owner = resolve_owner(db)
        if owner is None:
            print("No hay usuarios (o GYMVE_SEED_OWNER_EMAIL no existe); corre seed_users.py.")
            return
        ensure_plan(db, owner, exercises)
        db.commit()
        with_image = sum(1 for ex in exercises.values() if ex.image_path)
        print(
            f"Máquinas: {db.query(Machine).count()} | "
            f"Ejercicios: {db.query(Exercise).count()} ({with_image} con ilustración) | "
            f"Plantillas: {db.query(WorkoutTemplate).count()}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
