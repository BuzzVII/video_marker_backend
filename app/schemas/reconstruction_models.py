from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CuboidVertexRef(BaseModel):
    cuboidId: str
    vertexIndex: int


class CuboidEdgeRef(BaseModel):
    cuboidId: str
    edgeIndex: int
    startVertexIndex: int
    endVertexIndex: int


class CuboidCreatedFrom(BaseModel):
    solverRunId: str | None = None
    manual: bool | None = None


class Cuboid(BaseModel):
    id: str
    label: str | None = None
    center: tuple[float, float, float]
    size: tuple[float, float, float]
    rotation: tuple[float, float, float, float]
    color: str | None = None
    locked: bool | None = None
    createdFrom: CuboidCreatedFrom | None = None


class PointVertexConstraint(BaseModel):
    id: str
    pointId: str
    vertex: CuboidVertexRef
    confidence: float | None = None
    source: Literal["manual", "solver"] = "manual"
    created_at: datetime | None = None
    updated_at: datetime | None = None


class EdgeLengthConstraint(BaseModel):
    id: str
    edge: CuboidEdgeRef
    length: float
    unit: Literal["m", "mm"] = "m"
    source: Literal["manual"] = "manual"
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ReconstructionModelData(BaseModel):
    model_config = ConfigDict(extra="allow")

    cuboidsById: dict[str, Cuboid] = Field(default_factory=dict)
    pointVertexConstraintsById: dict[str, PointVertexConstraint] = Field(default_factory=dict)
    edgeLengthConstraintsById: dict[str, EdgeLengthConstraint] = Field(default_factory=dict)
    activeCuboidId: str | None = None
    activeVertex: CuboidVertexRef | None = None
    activeEdge: CuboidEdgeRef | None = None


class ReconstructionModelCreate(BaseModel):
    data_json: ReconstructionModelData = Field(default_factory=ReconstructionModelData)
    source: Literal["manual", "solver", "mixed"] = "manual"


class ReconstructionModelUpdate(BaseModel):
    data_json: ReconstructionModelData | None = None
    source: Literal["manual", "solver", "mixed"] | None = None


class ReconstructionModelRead(BaseModel):
    id: str
    project_id: str
    version: int
    data_json: dict[str, Any]
    source: str
    created_at: datetime
    updated_at: datetime
