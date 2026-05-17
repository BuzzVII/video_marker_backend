from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def new_radiance_field_job_id() -> str:
    return f"rfjob-{uuid4().hex[:12]}"


def new_radiance_field_id() -> str:
    return f"rf-{uuid4().hex[:12]}"


class RadianceFieldJob(SQLModel, table=True):
    __tablename__ = "radiance_field_job"

    id: str = Field(default_factory=new_radiance_field_job_id, primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    image_set_id: str | None = Field(default=None, foreign_key="image_set.id", index=True)
    name: str | None = None
    status: str = Field(default="queued", index=True)
    stage: str | None = Field(default="queued")
    progress: float = Field(default=0.0)
    error_message: str | None = None
    work_dir: str
    config_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    result_radiance_field_id: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class RadianceField(SQLModel, table=True):
    __tablename__ = "radiance_field"

    id: str = Field(default_factory=new_radiance_field_id, primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    source_job_id: str | None = Field(default=None, foreign_key="radiance_field_job.id", index=True)
    source_image_set_id: str | None = Field(default=None, foreign_key="image_set.id", index=True)
    name: str
    status: str = Field(default="available", index=True)
    asset_path: str
    asset_format: str = Field(default="ply")
    metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
