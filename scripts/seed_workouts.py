#!/usr/bin/env python3
"""Catálogo de ejercicios Nautilus/mancuernas y plantilla «Día piernas»."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db import Base, SessionLocal, engine
from app.models import (
    EquipmentType,
    Exercise,
    User,
    WorkoutTemplate,
    WorkoutTemplateExercise,
)

EXERCISES = [
    {
        "slug": "prensa-inclinada",
        "name": "Prensa inclinada",
        "equipment_type": EquipmentType.nautilus_machine,
        "muscle_group": "piernas",
        "notes": "Máquina selectorizada, rango cómodo de rodilla.",
    },
    {
        "slug": "extension-cuadriceps",
        "name": "Extensión de cuádriceps",
        "equipment_type": EquipmentType.nautilus_machine,
        "muscle_group": "piernas",
        "notes": "Control en la bajada, sin bloqueo brusco.",
    },
    {
        "slug": "curl-femoral-sentado",
        "name": "Curl femoral sentado",
        "equipment_type": EquipmentType.nautilus_machine,
        "muscle_group": "piernas",
        "notes": "Isquios; evitar despegar la cadera.",
    },
    {
        "slug": "abduccion-cadera-maquina",
        "name": "Abducción de cadera en máquina",
        "equipment_type": EquipmentType.nautilus_machine,
        "muscle_group": "piernas",
        "notes": "Glúteo medio; pausa breve arriba.",
    },
    {
        "slug": "gemelos-prensa",
        "name": "Gemelos en prensa",
        "equipment_type": EquipmentType.nautilus_machine,
        "muscle_group": "piernas",
        "notes": "Rango completo, sin rebote.",
    },
    {
        "slug": "sentadilla-goblet",
        "name": "Sentadilla goblet con mancuerna",
        "equipment_type": EquipmentType.dumbbell,
        "muscle_group": "piernas",
        "notes": "Complemento libre; profundidad controlada.",
    },
    {
        "slug": "peso-muerto-rumano-mancuernas",
        "name": "Peso muerto rumano con mancuernas",
        "equipment_type": EquipmentType.dumbbell,
        "muscle_group": "piernas",
        "notes": "Isquios y glúteos; espalda neutra.",
    },
    {
        "slug": "zancadas-mancuernas",
        "name": "Zancadas con mancuernas",
        "equipment_type": EquipmentType.dumbbell,
        "muscle_group": "piernas",
        "notes": "Alternar piernas por serie o por repetición.",
    },
]

LEG_DAY_SLUGS = [
    "prensa-inclinada",
    "extension-cuadriceps",
    "curl-femoral-sentado",
    "abduccion-cadera-maquina",
    "gemelos-prensa",
    "sentadilla-goblet",
]

TEMPLATE_TITLE = "Día piernas — Nautilus + mancuernas"
TEMPLATE_FOCUS = "piernas"
TEMPLATE_DESCRIPTION = (
    "Rutina base GymVe para Fitness 24 Seven Bogotá (San José de Bavaria). "
    "Máquinas tipo Nautilus y mancuernas; editable desde el panel."
)


def upsert_exercise(db, spec: dict) -> Exercise:
    row = db.query(Exercise).filter(Exercise.slug == spec["slug"]).one_or_none()
    if row:
        row.name = spec["name"]
        row.equipment_type = spec["equipment_type"]
        row.muscle_group = spec["muscle_group"]
        row.notes = spec["notes"]
        return row
    row = Exercise(**spec)
    db.add(row)
    db.flush()
    return row


def ensure_leg_template(db) -> None:
    owner = db.query(User).order_by(User.id.asc()).first()
    if not owner:
        print("No hay usuarios; ejecuta scripts/seed_users.py primero.")
        return

    existing = (
        db.query(WorkoutTemplate)
        .filter(
            WorkoutTemplate.owner_user_id == owner.id,
            WorkoutTemplate.title == TEMPLATE_TITLE,
        )
        .one_or_none()
    )
    if existing:
        template = existing
        db.query(WorkoutTemplateExercise).filter(
            WorkoutTemplateExercise.template_id == template.id
        ).delete()
    else:
        template = WorkoutTemplate(
            owner_user_id=owner.id,
            title=TEMPLATE_TITLE,
            description=TEMPLATE_DESCRIPTION,
            focus=TEMPLATE_FOCUS,
        )
        db.add(template)
        db.flush()

    slug_to_ex = {ex.slug: ex for ex in db.query(Exercise).all()}
    for order, slug in enumerate(LEG_DAY_SLUGS):
        ex = slug_to_ex.get(slug)
        if not ex:
            continue
        db.add(
            WorkoutTemplateExercise(
                template_id=template.id,
                exercise_id=ex.id,
                sort_order=order,
                default_sets=3,
                default_reps=12 if "gemelos" not in slug else 15,
            )
        )
    print(f"Plantilla «{TEMPLATE_TITLE}» (id={template.id}) para {owner.email}")


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for spec in EXERCISES:
            upsert_exercise(db, spec)
        db.commit()
        ensure_leg_template(db)
        db.commit()
        print(
            f"Ejercicios en catálogo: {db.query(Exercise).count()} | "
            f"Plantillas: {db.query(WorkoutTemplate).count()}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
