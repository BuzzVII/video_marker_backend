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
        id=payload.id if payload.id else None,
        project_id=project.id,
        version=next_model_version(session, project.id),
        data_json=payload.data_json.model_dump(mode="json"),
        source=payload.source,
        created_at=now,
        updated_at=now,
    )
    if model.id is None:
        # Let the SQLModel default factory assign the id.
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
        data_json=payload.data_json.model_dump(mode="json") if payload.data_json else {},
        source=payload.source or "manual",
        created_at=now,
        updated_at=now,
    )
    session.add(model)
    touch_project(session, project)
    session.commit()
    session.refresh(model)
    return model, True
