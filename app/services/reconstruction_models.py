from datetime import datetime, timezone

from sqlmodel import Session, func, select

from app.models.project import Project
from app.models.reconstruction_model import ReconstructionModel
from app.schemas.reconstruction_models import ReconstructionModelCreate, ReconstructionModelUpdate
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


def create_reconstruction_model(
    session: Session,
    project: Project,
    payload: ReconstructionModelCreate,
) -> ReconstructionModel:
    now = utc_now()
    model = ReconstructionModel(
        project_id=project.id,
        version=next_model_version(session, project.id),
        data_json=payload.data_json.model_dump(mode="json"),
        source=payload.source,
        created_at=now,
        updated_at=now,
    )
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
        model.data_json = payload.data_json.model_dump(mode="json")
    if payload.source is not None:
        model.source = payload.source
    model.updated_at = utc_now()
    session.add(model)
    touch_project(session, project)
    session.commit()
    session.refresh(model)
    return model
