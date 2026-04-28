from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AnnotationDocument(SQLModel, table=True):
    __tablename__ = "annotation_document"

    image_set_id: str = Field(primary_key=True, foreign_key="image_set.id")
    data_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    updated_at: datetime = Field(default_factory=utc_now)
