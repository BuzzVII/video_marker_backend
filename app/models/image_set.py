from datetime import datetime, timezone
from uuid import uuid4

from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def new_image_set_id() -> str:
    return f"set-{uuid4().hex[:12]}"


class ImageSet(SQLModel, table=True):
    __tablename__ = "image_set"

    id: str = Field(default_factory=new_image_set_id, primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    name: str
    source_type: str = Field(default="manual")
    original_video_path: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    project: "Project" = Relationship(back_populates="image_sets")
    frames: list["Frame"] = Relationship(back_populates="image_set")
