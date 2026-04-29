from datetime import datetime

from pydantic import BaseModel

from app.schemas.image_sets import ImageSetSummary


class ProjectCreate(BaseModel):
    name: str


class ProjectUpdate(BaseModel):
    name: str | None = None


class ProjectSummary(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    image_set_count: int


class ProjectRead(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    image_sets: list[ImageSetSummary]
