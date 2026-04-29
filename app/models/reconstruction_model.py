from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def new_model_id() -> str:
    return f"model-{uuid4().hex[:12]}"


class ReconstructionModel(SQLModel, table=True):
    __tablename__ = "reconstruction_model"

    id: str = Field(default_factory=new_model_id, primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    version: int = Field(index=True)
    data_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    source: str = Field(default="manual")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
