from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str
    display_name: str


class UserProfile(BaseModel):
    email: str
    display_name: str


class EquipmentTypeSchema(str, Enum):
    machine = "machine"
    cable = "cable"
    smith = "smith"
    dumbbell = "dumbbell"
    cardio = "cardio"


class StartSessionResponse(BaseModel):
    session_id: int
    url: str


class LogSetRequest(BaseModel):
    exercise_id: int = Field(ge=1)
    weight_kg: float = Field(default=0, ge=0, le=500)
    reps: int = Field(default=0, ge=0, le=200)
    duration_min: float | None = Field(default=None, gt=0, le=300)


class LogSetResponse(BaseModel):
    id: int
    set_number: int
    weight_kg: float
    reps: int
    duration_min: float | None


class EquipmentPrefsRequest(BaseModel):
    enabled: list[EquipmentTypeSchema] = Field(max_length=10)


class MachineUpdateRequest(BaseModel):
    brand: str = Field(default="", max_length=80)
    model: str = Field(default="", max_length=120)
    confirmed: bool = False


class SharedStatusSchema(str, Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class ShareWorkoutRequest(BaseModel):
    template_id: int = Field(ge=1)
    to_user_id: int | None = Field(default=None, ge=1)
    to_email: str | None = Field(default=None, min_length=3, max_length=320)
    message: str = Field(default="", max_length=500)


class SharedWorkoutItem(BaseModel):
    id: int
    status: SharedStatusSchema
    message: str
    created_at: datetime
    accepted_at: datetime | None
    from_user_id: int
    from_display_name: str
    to_user_id: int
    source_template_id: int
    source_template_title: str
    cloned_template_id: int | None
    direction: str


class SharedWorkoutListResponse(BaseModel):
    items: list[SharedWorkoutItem]


class TemplateItemSpec(BaseModel):
    exercise_id: int
    default_sets: int = Field(default=3, ge=1, le=20)
    default_reps: int = Field(default=10, ge=1, le=100)
    intensity_pct: int | None = Field(default=None, ge=1, le=100)
    duration_min: int | None = Field(default=None, ge=1, le=240)
    rest_seconds: int = Field(default=90, ge=0, le=900)


class TemplateUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    # El orden de la lista es el orden de la rutina.
    items: list[TemplateItemSpec] = Field(min_length=1, max_length=40)


class TemplateUpdateResponse(BaseModel):
    template_id: int
    exercise_count: int
    synced_copies: int


class ShareWorkoutResponse(BaseModel):
    id: int
    status: SharedStatusSchema
    to_user_id: int
    source_template_id: int
    cloned_template_id: int | None = None
