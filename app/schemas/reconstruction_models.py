from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


def default_reconstruction_model_data() -> dict[str, Any]:
    return {
        "cuboidsById": {},
        "pointVertexConstraintsById": {},
        "imageLineEdgeConstraintsById": {},
        "edgeLengthConstraintsById": {},
        "faceAssociationsById": {},
        "wallFeaturesById": {},
        "activeCuboidId": None,
        "activeVertex": None,
        "activeEdge": None,
        "activeFaces": [],
    }


class ReconstructionModelCreate(BaseModel):
    # Optional so the frontend can either let the backend allocate ids or preserve
    # an id it has already created locally.
    id: str | None = None
    data_json: dict[str, Any] = Field(default_factory=default_reconstruction_model_data)
    source: Literal["manual", "solver", "mixed"] = "manual"


class ReconstructionModelUpdate(BaseModel):
    # Keep this as a raw JSON object rather than a strongly typed whitelist.
    # The frontend model is still evolving, so the backend should preserve newer
    # keys such as faceAssociationsById, wallFeaturesById, and future fields.
    data_json: dict[str, Any] | None = None
    source: Literal["manual", "solver", "mixed"] | None = None


class ReconstructionModelRead(BaseModel):
    id: str
    project_id: str
    version: int
    data_json: dict[str, Any]
    source: str
    created_at: datetime
    updated_at: datetime
