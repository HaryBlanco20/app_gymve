"""Cambios de esquema idempotentes para bases creadas con versiones anteriores.

`Base.metadata.create_all` solo crea tablas nuevas; aquí se agregan columnas y
valores de enum que faltan en tablas ya existentes (PostgreSQL).
"""

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db import Base

NEW_ENUM_VALUES = ("machine", "cable", "smith", "cardio")

ADD_COLUMNS = (
    "ALTER TABLE exercises ADD COLUMN IF NOT EXISTS description TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE exercises ADD COLUMN IF NOT EXISTS instructions TEXT NOT NULL DEFAULT ''",
    (
        "ALTER TABLE exercises ADD COLUMN IF NOT EXISTS primary_muscles VARCHAR(240) "
        "NOT NULL DEFAULT ''"
    ),
    (
        "ALTER TABLE exercises ADD COLUMN IF NOT EXISTS secondary_muscles VARCHAR(240) "
        "NOT NULL DEFAULT ''"
    ),
    "ALTER TABLE exercises ADD COLUMN IF NOT EXISTS image_path VARCHAR(200) NOT NULL DEFAULT ''",
    (
        "ALTER TABLE exercises ADD COLUMN IF NOT EXISTS image_alt_path VARCHAR(200) "
        "NOT NULL DEFAULT ''"
    ),
    "ALTER TABLE exercises ADD COLUMN IF NOT EXISTS image_credit VARCHAR(40) NOT NULL DEFAULT ''",
    "ALTER TABLE exercises ADD COLUMN IF NOT EXISTS machine_id INTEGER REFERENCES machines(id)",
    "ALTER TABLE workout_templates ADD COLUMN IF NOT EXISTS day_number INTEGER",
    "ALTER TABLE workout_template_exercises ADD COLUMN IF NOT EXISTS intensity_pct INTEGER",
    "ALTER TABLE workout_template_exercises ADD COLUMN IF NOT EXISTS duration_min INTEGER",
    (
        "ALTER TABLE workout_template_exercises ADD COLUMN IF NOT EXISTS rest_seconds INTEGER "
        "NOT NULL DEFAULT 90"
    ),
    "ALTER TABLE user_exercise_logs ADD COLUMN IF NOT EXISTS duration_min DOUBLE PRECISION",
    "ALTER TABLE workout_templates ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ",
    "ALTER TABLE shared_workouts ADD COLUMN IF NOT EXISTS source_updated_at TIMESTAMPTZ",
)


def upgrade_schema(engine: Engine) -> None:
    import app.models  # noqa: F401 — registra todas las tablas

    Base.metadata.create_all(bind=engine)
    if engine.dialect.name != "postgresql":
        return

    # ALTER TYPE ... ADD VALUE debe confirmarse antes de usar el valor nuevo.
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_type WHERE typname = 'equipment_type_enum'")
        ).first()
        if exists:
            for value in NEW_ENUM_VALUES:
                conn.execute(
                    text(f"ALTER TYPE equipment_type_enum ADD VALUE IF NOT EXISTS '{value}'")
                )

    with engine.begin() as conn:
        for stmt in ADD_COLUMNS:
            conn.execute(text(stmt))
        conn.execute(
            text(
                "UPDATE exercises SET equipment_type = 'machine' "
                "WHERE equipment_type = 'nautilus_machine'"
            )
        )
