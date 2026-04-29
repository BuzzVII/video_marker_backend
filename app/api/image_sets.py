from pathlib import Path
import shutil

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlmodel import Session, func, select

from app.db.session import get_session
from app.models.frame import Frame
from app.models.image_set import ImageSet
from app.models.project import Project
from app.schemas.image_sets import FrameRead, ImageSetRead, ImageSetSummary
from app.services.projects import touch_project

router = APIRouter(prefix="/api/image-sets", tags=["image sets"])


def get_image_set_or_404(session: Session, image_set_id: str) -> ImageSet:
    image_set = session.get(ImageSet, image_set_id)
    if image_set is None:
        raise HTTPException(status_code=404, detail="Image set not found")
    return image_set


def to_summary(session: Session, image_set: ImageSet) -> ImageSetSummary:
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


@router.get("", response_model=list[ImageSetSummary])
def list_image_sets(session: Session = Depends(get_session)) -> list[ImageSetSummary]:
    image_sets = session.exec(select(ImageSet).order_by(ImageSet.created_at.desc())).all()
    return [to_summary(session, image_set) for image_set in image_sets]


@router.get("/{image_set_id}", response_model=ImageSetRead)
def read_image_set(
    image_set_id: str,
    session: Session = Depends(get_session),
) -> ImageSetRead:
    image_set = get_image_set_or_404(session, image_set_id)
    frames = session.exec(
        select(Frame).where(Frame.image_set_id == image_set.id).order_by(Frame.frame_index)
    ).all()

    return ImageSetRead(
        id=image_set.id,
        project_id=image_set.project_id,
        name=image_set.name,
        created_at=image_set.created_at,
        updated_at=image_set.updated_at,
        source_type=image_set.source_type,
        frames=[
            FrameRead(
                id=frame.id,
                label=f"Frame {frame.frame_index}",
                url=f"/api/image-sets/{image_set.id}/frames/{frame.id}/image",
                width=frame.width,
                height=frame.height,
                frame_index=frame.frame_index,
                timestamp_seconds=frame.timestamp_seconds,
                created_at=frame.created_at,
            )
            for frame in frames
        ],
    )


@router.delete("/{image_set_id}", status_code=204)
def delete_image_set(
    image_set_id: str,
    session: Session = Depends(get_session),
) -> Response:
    image_set = get_image_set_or_404(session, image_set_id)
    project = session.get(Project, image_set.project_id)

    frames = session.exec(select(Frame).where(Frame.image_set_id == image_set.id)).all()
    frame_dir: Path | None = Path(frames[0].image_path).parent if frames else None
    for frame in frames:
        session.delete(frame)

    session.delete(image_set)
    if project is not None:
        touch_project(session, project)
    session.commit()

    if frame_dir is not None and frame_dir.exists():
        shutil.rmtree(frame_dir, ignore_errors=True)

    return Response(status_code=204)


@router.get("/{image_set_id}/frames/{frame_id}/image")
def read_frame_image(
    image_set_id: str,
    frame_id: str,
    session: Session = Depends(get_session),
) -> FileResponse:
    get_image_set_or_404(session, image_set_id)
    frame = session.get(Frame, frame_id)
    if frame is None or frame.image_set_id != image_set_id:
        raise HTTPException(status_code=404, detail="Frame not found")

    image_path = Path(frame.image_path)
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Frame image file not found on disk")

    return FileResponse(image_path, media_type="image/jpeg")
