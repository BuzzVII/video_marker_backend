from datetime import datetime, timezone

from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Frame(SQLModel, table=True):
    __tablename__ = "frame"

    id: str = Field(primary_key=True)
    image_set_id: str = Field(foreign_key="image_set.id", index=True)
    frame_index: int
    timestamp_seconds: float | None = None
    image_path: str
    width: int | None = None
    height: int | None = None
    created_at: datetime = Field(default_factory=utc_now)

    image_set: "ImageSet" = Relationship(back_populates="frames")
