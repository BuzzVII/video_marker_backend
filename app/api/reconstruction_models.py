from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select

from app.api.projects import get_project_or_404
from app.db.session import get_session
from app.models.reconstruction_model import ReconstructionModel
from app.schemas.reconstruction_models import (
    ReconstructionModelCreate,
    ReconstructionModelRead,
    ReconstructionModelUpdate,
)
from app.services.projects import touch_project
from app.services.reconstruction_models import (
    create_reconstruction_model,
    reconstruction_model_to_read,
    upsert_reconstruction_model,
)

router = APIRouter(prefix="/api/projects/{project_id}/models", tags=["reconstruction models"])


def get_model_or_404(session: Session, project_id: str, model_id: str) -> ReconstructionModel:
    model = session.get(ReconstructionModel, model_id)
    if model is None or model.project_id != project_id:
        raise HTTPException(status_code=404, detail="Reconstruction model not found")
    return model


@router.get("/latest", response_model=ReconstructionModelRead)
def read_latest_model(
    project_id: str,
    session: Session = Depends(get_session),
) -> ReconstructionModelRead:
    get_project_or_404(session, project_id)
    model = session.exec(
        select(ReconstructionModel)
        .where(ReconstructionModel.project_id == project_id)
        .order_by(ReconstructionModel.version.desc(), ReconstructionModel.created_at.desc())
    ).first()
    if model is None:
        raise HTTPException(status_code=404, detail="No reconstruction models found for project")
    return reconstruction_model_to_read(model)


@router.get("", response_model=list[ReconstructionModelRead])
def list_models(
    project_id: str,
    session: Session = Depends(get_session),
) -> list[ReconstructionModelRead]:
    get_project_or_404(session, project_id)
    models = session.exec(
        select(ReconstructionModel)
        .where(ReconstructionModel.project_id == project_id)
        .order_by(ReconstructionModel.version.desc())
    ).all()
    return [reconstruction_model_to_read(model) for model in models]


@router.post("", response_model=ReconstructionModelRead, status_code=201)
def create_model(
    project_id: str,
    payload: ReconstructionModelCreate,
    session: Session = Depends(get_session),
) -> ReconstructionModelRead:
    project = get_project_or_404(session, project_id)

    if payload.id:
        existing = session.get(ReconstructionModel, payload.id)
        if existing is not None:
            raise HTTPException(status_code=409, detail="Reconstruction model id already exists")

    model = create_reconstruction_model(session, project, payload)
    return reconstruction_model_to_read(model)


@router.get("/{model_id}", response_model=ReconstructionModelRead)
def read_model(
    project_id: str,
    model_id: str,
    session: Session = Depends(get_session),
) -> ReconstructionModelRead:
    get_project_or_404(session, project_id)
    model = get_model_or_404(session, project_id, model_id)
    return reconstruction_model_to_read(model)


@router.put("/{model_id}", response_model=ReconstructionModelRead)
def replace_model(
    project_id: str,
    model_id: str,
    payload: ReconstructionModelUpdate,
    session: Session = Depends(get_session),
) -> ReconstructionModelRead:
    # PUT is idempotent here. If the frontend has already generated a model id
    # locally, saving to that URL will create the model instead of returning 404.
    project = get_project_or_404(session, project_id)
    model, created = upsert_reconstruction_model(session, project, model_id, payload)
    if model.project_id != project_id:
        raise HTTPException(status_code=404, detail="Reconstruction model not found")
    return reconstruction_model_to_read(model)


@router.delete("/{model_id}", status_code=204)
def delete_model(
    project_id: str,
    model_id: str,
    session: Session = Depends(get_session),
) -> Response:
    project = get_project_or_404(session, project_id)
    model = get_model_or_404(session, project_id, model_id)
    session.delete(model)
    touch_project(session, project)
    session.commit()
    return Response(status_code=204)
