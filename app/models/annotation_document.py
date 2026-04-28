from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def new_annotation_id() -> str:
    return f"ann-{uuid4().hex[:12]}"


class AnnotationDocument(SQLModel, table=True):
    __tablename__ = "annotation_document"

    id: str = Field(default_factory=new_annotation_id, primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True, unique=True)
    data_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    updated_at: datetime = Field(default_factory=utc_now)
