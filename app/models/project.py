from datetime import datetime, timezone
from uuid import uuid4

from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def new_project_id() -> str:
    return f"project-{uuid4().hex[:12]}"


class Project(SQLModel, table=True):
    __tablename__ = "project"

    id: str = Field(default_factory=new_project_id, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    image_sets: list["ImageSet"] = Relationship(back_populates="project")
