from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from app.db.session import get_session
from app.models.image_set import ImageSet
from app.schemas.image_sets import ImageSetSummary
from app.services.frame_extraction import extract_frames
from app.services.storage import safe_stem, save_upload_file

router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.post("/upload", response_model=ImageSetSummary)
async def upload_video(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> ImageSetSummary:
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Upload must be a video file")

    video_path = await save_upload_file(file)

    image_set = ImageSet(
        id=f"set-{uuid4().hex[:12]}",
        name=safe_stem(file.filename).replace("_", " "),
        source_type="video",
        original_video_path=str(Path(video_path)),
    )
    session.add(image_set)
    session.flush()

    try:
        frames = extract_frames(
            video_path=video_path,
            image_set_id=image_set.id,
            session=session,
        )
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    session.commit()
    session.refresh(image_set)

    return ImageSetSummary(
        id=image_set.id,
        name=image_set.name,
        created_at=image_set.created_at,
        frame_count=len(frames),
        source_type=image_set.source_type,
    )
