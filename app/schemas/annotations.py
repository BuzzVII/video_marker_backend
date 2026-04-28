from pydantic import BaseModel, ConfigDict


class Point(BaseModel):
    id: str
    color: str | None = None


class PointPosition(BaseModel):
    pointId: str
    imageSetId: str | None = None
    imageId: str
    x: float
    y: float


class Line(BaseModel):
    id: str


class LineOccurrence(BaseModel):
    lineId: str
    imageSetId: str | None = None
    imageId: str
    startPointId: str
    endPointId: str


class AnnotationPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    pointsById: dict[str, Point] = {}
    pointPositionsByPointId: dict[str, dict[str, PointPosition]] = {}
    linesById: dict[str, Line] = {}
    lineOccurrencesByLineId: dict[str, dict[str, LineOccurrence]] = {}


def empty_annotation_payload() -> AnnotationPayload:
    return AnnotationPayload(
        pointsById={},
        pointPositionsByPointId={},
        linesById={},
        lineOccurrencesByLineId={},
    )
