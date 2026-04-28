from datetime import datetime

from pydantic import BaseModel


class ImageSetSummary(BaseModel):
    id: str
    name: str
    created_at: datetime
    frame_count: int
    source_type: str


class FrameRead(BaseModel):
    id: str
    label: str
    url: str
    width: int
    height: int
    frame_index: int
    timestamp_seconds: float


class ImageSetRead(BaseModel):
    id: str
    name: str
    created_at: datetime
    source_type: str
    frames: list[FrameRead]
