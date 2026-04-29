from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.image_sets import ImageSetSummary
from app.services.projects import create_project
from app.services.videos import create_image_set_from_video

router = APIRouter(prefix="/api/videos", tags=["videos compatibility"])


@router.post("/upload", response_model=ImageSetSummary, status_code=201)
async def upload_video_compatibility(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> ImageSetSummary:
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Upload must be a video file")

    project_name = (file.filename or "Untitled project").rsplit(".", 1)[0].replace("_", " ")
    project = create_project(session, project_name)

    try:
        return await create_image_set_from_video(session=session, project=project, file=file)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
