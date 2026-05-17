from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class RadianceFieldJobCreate(BaseModel):
    image_set_id: str
    name: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class RadianceFieldJobRead(BaseModel):
    id: str
    project_id: str
    image_set_id: str | None
    name: str | None
    status: str
    stage: str | None
    progress: float
    error_message: str | None
    work_dir: str
    config_json: dict[str, Any]
    result_radiance_field_id: str | None
    created_at: datetime
    updated_at: datetime


class RadianceFieldRead(BaseModel):
    id: str
    project_id: str
    source_job_id: str | None
    source_image_set_id: str | None
    name: str
    status: str
    asset_path: str
    asset_format: str
    asset_url: str
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class RadianceFieldStatusUpdate(BaseModel):
    status: Literal["available", "missing_files", "failed"] | None = None
    name: str | None = None
    metadata_json: dict[str, Any] | None = None
