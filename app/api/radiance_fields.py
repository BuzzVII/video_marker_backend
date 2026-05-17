from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from app.api.projects import get_project_or_404
from app.db.session import get_session
from app.models.radiance_field import RadianceField, RadianceFieldJob
from app.schemas.radiance_fields import (
    RadianceFieldJobCreate,
    RadianceFieldJobRead,
    RadianceFieldRead,
)
from app.services.radiance_fields import (
    create_radiance_field_job,
    radiance_field_to_read,
    resolve_data_path,
    run_radiance_field_job,
)

router = APIRouter(prefix="/api/projects/{project_id}", tags=["radiance fields"])


def get_radiance_field_or_404(
    session: Session,
    project_id: str,
    radiance_field_id: str,
) -> RadianceField:
    field = session.get(RadianceField, radiance_field_id)
    if field is None or field.project_id != project_id:
        raise HTTPException(status_code=404, detail="Radiance field not found")
    return field


def get_radiance_field_job_or_404(
    session: Session,
    project_id: str,
    job_id: str,
) -> RadianceFieldJob:
    job = session.get(RadianceFieldJob, job_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=404, detail="Radiance field job not found")
    return job


@router.get("/radiance-fields", response_model=list[RadianceFieldRead])
def list_radiance_fields(
    project_id: str,
    session: Session = Depends(get_session),
) -> list[dict]:
    get_project_or_404(session, project_id)
    fields = session.exec(
        select(RadianceField)
        .where(RadianceField.project_id == project_id)
        .order_by(RadianceField.created_at.desc())
    ).all()
    return [radiance_field_to_read(field) for field in fields]


@router.get("/radiance-fields/latest", response_model=RadianceFieldRead)
def read_latest_radiance_field(
    project_id: str,
    session: Session = Depends(get_session),
) -> dict:
    get_project_or_404(session, project_id)
    field = session.exec(
        select(RadianceField)
        .where(RadianceField.project_id == project_id)
        .where(RadianceField.status == "available")
        .order_by(RadianceField.created_at.desc())
    ).first()
    if field is None:
        raise HTTPException(status_code=404, detail="No radiance fields found for project")
    return radiance_field_to_read(field)


@router.get("/radiance-fields/{radiance_field_id}", response_model=RadianceFieldRead)
def read_radiance_field(
    project_id: str,
    radiance_field_id: str,
    session: Session = Depends(get_session),
) -> dict:
    get_project_or_404(session, project_id)
    field = get_radiance_field_or_404(session, project_id, radiance_field_id)
    return radiance_field_to_read(field)


@router.get("/radiance-fields/{radiance_field_id}/asset")
def read_radiance_field_asset(
    project_id: str,
    radiance_field_id: str,
    session: Session = Depends(get_session),
) -> FileResponse:
    get_project_or_404(session, project_id)
    field = get_radiance_field_or_404(session, project_id, radiance_field_id)
    asset_path = resolve_data_path(field.asset_path)
    if not asset_path.exists() or not asset_path.is_file():
        field.status = "missing_files"
        session.add(field)
        session.commit()
        raise HTTPException(status_code=404, detail="Radiance field asset file is missing")

    media_type = "application/octet-stream"
    if asset_path.suffix.lower() == ".ply":
        media_type = "application/octet-stream"
    return FileResponse(path=asset_path, media_type=media_type, filename=asset_path.name)


@router.post("/radiance-field-jobs", response_model=RadianceFieldJobRead, status_code=201)
def start_radiance_field_job(
    project_id: str,
    payload: RadianceFieldJobCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
) -> RadianceFieldJob:
    project = get_project_or_404(session, project_id)
    try:
        job = create_radiance_field_job(session, project, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    background_tasks.add_task(run_radiance_field_job, job.id)
    return job


@router.get("/radiance-field-jobs", response_model=list[RadianceFieldJobRead])
def list_radiance_field_jobs(
    project_id: str,
    session: Session = Depends(get_session),
) -> list[RadianceFieldJob]:
    get_project_or_404(session, project_id)
    return session.exec(
        select(RadianceFieldJob)
        .where(RadianceFieldJob.project_id == project_id)
        .order_by(RadianceFieldJob.created_at.desc())
    ).all()


@router.get("/radiance-field-jobs/{job_id}", response_model=RadianceFieldJobRead)
def read_radiance_field_job(
    project_id: str,
    job_id: str,
    session: Session = Depends(get_session),
) -> RadianceFieldJob:
    get_project_or_404(session, project_id)
    return get_radiance_field_job_or_404(session, project_id, job_id)
