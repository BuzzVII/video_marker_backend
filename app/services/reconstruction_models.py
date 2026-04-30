from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, func, select

from app.models.project import Project
from app.models.reconstruction_model import ReconstructionModel
from app.schemas.reconstruction_models import (
    ReconstructionModelCreate,
    ReconstructionModelRead,
    ReconstructionModelUpdate,
    default_reconstruction_model_data,
)
from app.services.projects import touch_project


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def next_model_version(session: Session, project_id: str) -> int:
    max_version = session.exec(
        select(func.max(ReconstructionModel.version)).where(
            ReconstructionModel.project_id == project_id
        )
    ).one()
    return int(max_version or 0) + 1


def normalize_model_data(data: dict[str, Any] | None) -> dict[str, Any]:
    """Add defaults for known model fields without dropping unknown frontend keys."""
    normalized = default_reconstruction_model_data()
    if data:
        normalized.update(deepcopy(data))

    for key in (
        "cuboidsById",
        "pointVertexConstraintsById",
        "imageLineEdgeConstraintsById",
        "edgeLengthConstraintsById",
        "faceAssociationsById",
        "wallFeaturesById",
    ):
        if normalized.get(key) is None:
            normalized[key] = {}

    if normalized.get("activeFaces") is None:
        normalized["activeFaces"] = []

    return normalized


def reconstruction_model_to_read(model: ReconstructionModel) -> ReconstructionModelRead:
    return ReconstructionModelRead(
        id=model.id,
        project_id=model.project_id,
        version=model.version,
        data_json=normalize_model_data(model.data_json),
        source=model.source,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def create_reconstruction_model(
    session: Session,
    project: Project,
    payload: ReconstructionModelCreate,
) -> ReconstructionModel:
    now = utc_now()
    kwargs = {
        "project_id": project.id,
        "version": next_model_version(session, project.id),
        "data_json": normalize_model_data(payload.data_json),
        "source": payload.source,
        "created_at": now,
        "updated_at": now,
    }
    if payload.id:
        kwargs["id"] = payload.id

    model = ReconstructionModel(**kwargs)
    session.add(model)
    touch_project(session, project)
    session.commit()
    session.refresh(model)
    return model


def update_reconstruction_model(
    session: Session,
    project: Project,
    model: ReconstructionModel,
    payload: ReconstructionModelUpdate,
) -> ReconstructionModel:
    if payload.data_json is not None:
        model.data_json = normalize_model_data(payload.data_json)
    if payload.source is not None:
        model.source = payload.source
    model.updated_at = utc_now()
    session.add(model)
    touch_project(session, project)
    session.commit()
    session.refresh(model)
    return model


def upsert_reconstruction_model(
    session: Session,
    project: Project,
    model_id: str,
    payload: ReconstructionModelUpdate,
) -> tuple[ReconstructionModel, bool]:
    model = session.get(ReconstructionModel, model_id)
    if model is not None and model.project_id != project.id:
        # Same primary key exists under another project. Treat that as not found
        # instead of accidentally moving it between projects.
        return model, False

    if model is not None:
        return update_reconstruction_model(session, project, model, payload), False

    now = utc_now()
    model = ReconstructionModel(
        id=model_id,
        project_id=project.id,
        version=next_model_version(session, project.id),
        data_json=normalize_model_data(payload.data_json),
        source=payload.source or "manual",
        created_at=now,
        updated_at=now,
    )
    session.add(model)
    touch_project(session, project)
    session.commit()
    session.refresh(model)
    return model, True
