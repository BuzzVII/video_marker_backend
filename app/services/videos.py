from pathlib import Path

from fastapi import UploadFile
from sqlmodel import Session

from app.models.image_set import ImageSet
from app.models.project import Project
from app.schemas.image_sets import ImageSetSummary
from app.services.frame_extraction import extract_frames
from app.services.projects import touch_project
from app.services.storage import safe_stem, save_upload_file


async def create_image_set_from_video(
    *,
    session: Session,
    project: Project,
    file: UploadFile,
) -> ImageSetSummary:
    video_path = await save_upload_file(file)

    image_set = ImageSet(
        project_id=project.id,
        name=safe_stem(file.filename).replace("_", " "),
        source_type="video",
        original_video_path=str(Path(video_path)),
    )
    session.add(image_set)
    session.flush()

    frames = extract_frames(
        video_path=video_path,
        image_set_id=image_set.id,
        session=session,
    )
    touch_project(session, project)
    session.commit()
    session.refresh(image_set)

    return ImageSetSummary(
        id=image_set.id,
        project_id=image_set.project_id,
        name=image_set.name,
        created_at=image_set.created_at,
        updated_at=image_set.updated_at,
        frame_count=len(frames),
        source_type=image_set.source_type,
    )
