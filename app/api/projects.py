from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlmodel import Session, func, select

from app.db.session import get_session
from app.models.annotation_document import AnnotationDocument
from app.models.frame import Frame
from app.models.image_set import ImageSet
from app.models.project import Project
from app.models.reconstruction_model import ReconstructionModel
from app.schemas.annotations import AnnotationPayload
from app.schemas.exports import ReconstructionExport
from app.schemas.image_sets import ImageSetCreate, ImageSetSummary
from app.schemas.projects import ProjectCreate, ProjectRead, ProjectSummary, ProjectUpdate
from app.services.annotations import get_annotation_payload, save_annotation_payload
from app.services.exports import build_reconstruction_export
from app.services.projects import create_project, touch_project
from app.services.videos import create_image_set_from_video

router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_project_or_404(session: Session, project_id: str) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def image_set_summary(session: Session, image_set: ImageSet) -> ImageSetSummary:
    frame_count = session.exec(
        select(func.count()).select_from(Frame).where(Frame.image_set_id == image_set.id)
    ).one()

    return ImageSetSummary(
        id=image_set.id,
        project_id=image_set.project_id,
        name=image_set.name,
        created_at=image_set.created_at,
        updated_at=image_set.updated_at,
        frame_count=frame_count,
        source_type=image_set.source_type,
    )


def project_summary(session: Session, project: Project) -> ProjectSummary:
    image_set_count = session.exec(
        select(func.count()).select_from(ImageSet).where(ImageSet.project_id == project.id)
    ).one()
    return ProjectSummary(
        id=project.id,
        name=project.name,
        created_at=project.created_at,
        updated_at=project.updated_at,
        image_set_count=image_set_count,
    )


@router.get("", response_model=list[ProjectSummary])
def list_projects(session: Session = Depends(get_session)) -> list[ProjectSummary]:
    projects = session.exec(select(Project).order_by(Project.updated_at.desc())).all()
    return [project_summary(session, project) for project in projects]


@router.post("", response_model=ProjectSummary, status_code=201)
def create_project_endpoint(
    payload: ProjectCreate,
    session: Session = Depends(get_session),
) -> ProjectSummary:
    project = create_project(session, payload.name)
    return project_summary(session, project)


@router.get("/{project_id}", response_model=ProjectRead)
def read_project(
    project_id: str,
    session: Session = Depends(get_session),
) -> ProjectRead:
    project = get_project_or_404(session, project_id)
    image_sets = session.exec(
        select(ImageSet).where(ImageSet.project_id == project.id).order_by(ImageSet.created_at)
    ).all()

    return ProjectRead(
        id=project.id,
        name=project.name,
        created_at=project.created_at,
        updated_at=project.updated_at,
        image_sets=[image_set_summary(session, image_set) for image_set in image_sets],
    )


@router.patch("/{project_id}", response_model=ProjectSummary)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    session: Session = Depends(get_session),
) -> ProjectSummary:
    project = get_project_or_404(session, project_id)
    if payload.name is not None:
        project.name = payload.name
    touch_project(session, project)
    session.commit()
    session.refresh(project)
    return project_summary(session, project)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: str,
    session: Session = Depends(get_session),
) -> Response:
    project = get_project_or_404(session, project_id)

    image_sets = session.exec(select(ImageSet).where(ImageSet.project_id == project.id)).all()
    for image_set in image_sets:
        frames = session.exec(select(Frame).where(Frame.image_set_id == image_set.id)).all()
        for frame in frames:
            session.delete(frame)
        session.delete(image_set)

    annotation = session.exec(
        select(AnnotationDocument).where(AnnotationDocument.project_id == project.id)
    ).first()
    if annotation is not None:
        session.delete(annotation)

    models = session.exec(
        select(ReconstructionModel).where(ReconstructionModel.project_id == project.id)
    ).all()
    for model in models:
        session.delete(model)

    session.delete(project)
    session.commit()
    return Response(status_code=204)


@router.get("/{project_id}/image-sets", response_model=list[ImageSetSummary])
def list_project_image_sets(
    project_id: str,
    session: Session = Depends(get_session),
) -> list[ImageSetSummary]:
    project = get_project_or_404(session, project_id)
    image_sets = session.exec(
        select(ImageSet).where(ImageSet.project_id == project.id).order_by(ImageSet.created_at)
    ).all()
    return [image_set_summary(session, image_set) for image_set in image_sets]


@router.post("/{project_id}/image-sets", response_model=ImageSetSummary, status_code=201)
def create_empty_image_set(
    project_id: str,
    payload: ImageSetCreate,
    session: Session = Depends(get_session),
) -> ImageSetSummary:
    project = get_project_or_404(session, project_id)
    image_set = ImageSet(
        project_id=project.id,
        name=payload.name,
        source_type=payload.source_type,
    )
    session.add(image_set)
    touch_project(session, project)
    session.commit()
    session.refresh(image_set)
    return image_set_summary(session, image_set)


@router.post("/{project_id}/videos/upload", response_model=ImageSetSummary, status_code=201)
async def upload_video_to_project(
    project_id: str,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> ImageSetSummary:
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Upload must be a video file")

    project = get_project_or_404(session, project_id)

    try:
        return await create_image_set_from_video(session=session, project=project, file=file)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{project_id}/annotations", response_model=AnnotationPayload)
def read_project_annotations(
    project_id: str,
    session: Session = Depends(get_session),
) -> AnnotationPayload:
    project = get_project_or_404(session, project_id)
    return get_annotation_payload(session, project.id)


@router.put("/{project_id}/annotations", response_model=AnnotationPayload)
def update_project_annotations(
    project_id: str,
    payload: AnnotationPayload,
    session: Session = Depends(get_session),
) -> AnnotationPayload:
    project = get_project_or_404(session, project_id)
    return save_annotation_payload(session, project, payload)


@router.get("/{project_id}/export", response_model=ReconstructionExport)
def export_project(
    project_id: str,
    session: Session = Depends(get_session),
) -> ReconstructionExport:
    project = get_project_or_404(session, project_id)
    return build_reconstruction_export(session, project)
