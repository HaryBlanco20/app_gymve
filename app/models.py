import enum
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")


class EquipmentType(str, enum.Enum):
    machine = "machine"
    cable = "cable"
    smith = "smith"
    dumbbell = "dumbbell"
    cardio = "cardio"
    # Valor heredado del MVP; existe en el enum de Postgres y se migra a `machine`.
    nautilus_machine = "nautilus_machine"


class Machine(Base):
    """Tipo de máquina de la sede; marca/modelo son opcionales y se confirman en el gym."""

    __tablename__ = "machines"
    __table_args__ = (UniqueConstraint("slug", name="uq_machines_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    equipment_type: Mapped[EquipmentType] = mapped_column(
        Enum(EquipmentType, name="equipment_type_enum"),
        nullable=False,
    )
    brand: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # unknown | probable | confirmed
    brand_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")


class UserEquipmentPref(Base):
    __tablename__ = "user_equipment_prefs"
    __table_args__ = (
        UniqueConstraint("user_id", "equipment_type", name="uq_user_equipment_pref"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    equipment_type: Mapped[str] = mapped_column(String(40), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class SharedWorkoutStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class Exercise(Base):
    __tablename__ = "exercises"
    __table_args__ = (UniqueConstraint("slug", name="uq_exercises_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    equipment_type: Mapped[EquipmentType] = mapped_column(
        Enum(EquipmentType, name="equipment_type_enum"),
        nullable=False,
    )
    muscle_group: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Un paso por línea.
    instructions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    primary_muscles: Mapped[str] = mapped_column(String(240), nullable=False, default="")
    secondary_muscles: Mapped[str] = mapped_column(String(240), nullable=False, default="")
    image_path: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    image_alt_path: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    image_credit: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    machine_id: Mapped[int | None] = mapped_column(ForeignKey("machines.id"), nullable=True)

    machine: Mapped[Machine | None] = relationship("Machine")


class WorkoutTemplate(Base):
    __tablename__ = "workout_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    focus: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    day_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    owner: Mapped[User] = relationship("User")
    items: Mapped[list["WorkoutTemplateExercise"]] = relationship(
        "WorkoutTemplateExercise",
        back_populates="template",
        order_by="WorkoutTemplateExercise.sort_order",
        cascade="all, delete-orphan",
    )


class WorkoutTemplateExercise(Base):
    __tablename__ = "workout_template_exercises"
    __table_args__ = (
        UniqueConstraint("template_id", "exercise_id", name="uq_template_exercise"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("workout_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    default_sets: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    default_reps: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    intensity_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rest_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=90)

    template: Mapped[WorkoutTemplate] = relationship("WorkoutTemplate", back_populates="items")
    exercise: Mapped[Exercise] = relationship("Exercise")


class SharedWorkout(Base):
    __tablename__ = "shared_workouts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_template_id: Mapped[int] = mapped_column(
        ForeignKey("workout_templates.id"),
        nullable=False,
        index=True,
    )
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[SharedWorkoutStatus] = mapped_column(
        Enum(SharedWorkoutStatus, name="shared_workout_status_enum"),
        nullable=False,
        default=SharedWorkoutStatus.pending,
    )
    cloned_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("workout_templates.id"),
        nullable=True,
    )
    share_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source_template: Mapped[WorkoutTemplate] = relationship(
        "WorkoutTemplate",
        foreign_keys=[source_template_id],
    )
    from_user: Mapped[User] = relationship("User", foreign_keys=[from_user_id])
    to_user: Mapped[User] = relationship("User", foreign_keys=[to_user_id])


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("workout_templates.id"), nullable=False)
    shared_workout_id: Mapped[int | None] = mapped_column(
        ForeignKey("shared_workouts.id"),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")


class UserExerciseLog(Base):
    __tablename__ = "user_exercise_logs"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "exercise_id",
            "set_number",
            name="uq_session_exercise_set",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("workout_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), nullable=False)
    set_number: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reps: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
