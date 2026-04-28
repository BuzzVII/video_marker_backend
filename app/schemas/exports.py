from pydantic import BaseModel


class ExportProject(BaseModel):
    id: str
    name: str


class ExportImageSet(BaseModel):
    id: str
    name: str


class ExportFrame(BaseModel):
    id: str
    image_set_id: str
    width: int
    height: int
    frame_index: int
    timestamp_seconds: float


class PointObservationExport(BaseModel):
    image_set_id: str
    image_id: str
    x_normalized: float
    y_normalized: float
    x_pixels: float
    y_pixels: float


class PointExport(BaseModel):
    id: str
    observations: list[PointObservationExport]


class LineObservationExport(BaseModel):
    image_set_id: str
    image_id: str
    start_point_id: str
    end_point_id: str


class LineExport(BaseModel):
    id: str
    observations: list[LineObservationExport]


class ReconstructionExport(BaseModel):
    project: ExportProject
    image_sets: list[ExportImageSet]
    frames: list[ExportFrame]
    points: list[PointExport]
    lines: list[LineExport]
