from sqlmodel import Field, Relationship, SQLModel


class Frame(SQLModel, table=True):
    __tablename__ = "frame"

    id: str = Field(primary_key=True)
    image_set_id: str = Field(foreign_key="image_set.id", index=True)
    frame_index: int
    timestamp_seconds: float
    image_path: str
    width: int
    height: int

    image_set: "ImageSet" = Relationship(back_populates="frames")
