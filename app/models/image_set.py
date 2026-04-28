from datetime import datetime, timezone

from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ImageSet(SQLModel, table=True):
    __tablename__ = "image_set"

    id: str = Field(primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    name: str
    source_type: str = Field(default="video")
    original_video_path: str | None = None
    created_at: datetime = Field(default_factory=utc_now)

    project: "Project" = Relationship(back_populates="image_sets")
    frames: list["Frame"] = Relationship(back_populates="image_set")
