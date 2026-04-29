from pydantic import BaseModel, ConfigDict, Field


class PointDefinition(BaseModel):
    id: str
    label: str | None = None
    color: str


class PointObservation(BaseModel):
    pointId: str
    imageSetId: str
    frameId: str
    x: float
    y: float


class LineDefinition(BaseModel):
    id: str
    label: str | None = None


class LineObservation(BaseModel):
    lineId: str
    imageSetId: str
    frameId: str
    startPointId: str
    endPointId: str


class AnnotationPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    pointsById: dict[str, PointDefinition] = Field(default_factory=dict)
    pointObservationsByPointId: dict[str, dict[str, PointObservation]] = Field(default_factory=dict)
    linesById: dict[str, LineDefinition] = Field(default_factory=dict)
    lineObservationsByLineId: dict[str, dict[str, LineObservation]] = Field(default_factory=dict)


def empty_annotation_payload() -> AnnotationPayload:
    return AnnotationPayload()
