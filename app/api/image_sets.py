from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session, func, select

from app.db.session import get_session
from app.models.frame import Frame
from app.models.image_set import ImageSet
from app.schemas.annotations import AnnotationPayload
from app.schemas.exports import ReconstructionExport
from app.schemas.image_sets import FrameRead, ImageSetRead, ImageSetSummary
from app.services.annotations import get_annotation_payload, save_annotation_payload
from app.services.exports import build_reconstruction_export

router = APIRouter(prefix="/api/image-sets", tags=["image sets"])


def get_image_set_or_404(session: Session, image_set_id: str) -> ImageSet:
    image_set = session.get(ImageSet, image_set_id)
    if image_set is None:
        raise HTTPException(status_code=404, detail="Image set not found")
    return image_set


@router.get("", response_model=list[ImageSetSummary])
def list_image_sets(session: Session = Depends(get_session)) -> list[ImageSetSummary]:
    image_sets = session.exec(select(ImageSet).order_by(ImageSet.created_at.desc())).all()

    result: list[ImageSetSummary] = []
    for image_set in image_sets:
        frame_count = session.exec(
            select(func.count()).select_from(Frame).where(Frame.image_set_id == image_set.id)
        ).one()

        result.append(
            ImageSetSummary(
                id=image_set.id,
                name=image_set.name,
                created_at=image_set.created_at,
                frame_count=frame_count,
                source_type=image_set.source_type,
            )
        )

    return result


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
        name=image_set.name,
        created_at=image_set.created_at,
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
            )
            for frame in frames
        ],
    )


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


@router.get("/{image_set_id}/annotations", response_model=AnnotationPayload)
def read_annotations(
    image_set_id: str,
    session: Session = Depends(get_session),
) -> AnnotationPayload:
    get_image_set_or_404(session, image_set_id)
    return get_annotation_payload(session, image_set_id)


@router.put("/{image_set_id}/annotations", response_model=AnnotationPayload)
def update_annotations(
    image_set_id: str,
    payload: AnnotationPayload,
    session: Session = Depends(get_session),
) -> AnnotationPayload:
    get_image_set_or_404(session, image_set_id)
    return save_annotation_payload(session, image_set_id, payload)


@router.get("/{image_set_id}/export", response_model=ReconstructionExport)
def export_image_set(
    image_set_id: str,
    session: Session = Depends(get_session),
) -> ReconstructionExport:
    image_set = get_image_set_or_404(session, image_set_id)
    return build_reconstruction_export(session, image_set)
