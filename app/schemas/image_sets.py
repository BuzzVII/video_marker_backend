from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ImageSetCreate(BaseModel):
    name: str
    source_type: Literal["video", "images", "manual"] = "manual"


class ImageSetSummary(BaseModel):
    id: str
    project_id: str
    name: str
    created_at: datetime
    updated_at: datetime
    frame_count: int
    source_type: str


class FrameRead(BaseModel):
    id: str
    label: str
    url: str
    width: int | None
    height: int | None
    frame_index: int
    timestamp_seconds: float | None
    created_at: datetime


class ImageSetRead(BaseModel):
    id: str
    project_id: str
    name: str
    created_at: datetime
    updated_at: datetime
    source_type: str
    frames: list[FrameRead]
