from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.annotation_document import AnnotationDocument
from app.models.project import Project
from app.schemas.annotations import AnnotationPayload, empty_annotation_payload
from app.services.projects import touch_project


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_annotation_document(session: Session, project_id: str) -> AnnotationDocument | None:
    return session.exec(
        select(AnnotationDocument).where(AnnotationDocument.project_id == project_id)
    ).first()


def get_annotation_payload(session: Session, project_id: str) -> AnnotationPayload:
    document = get_annotation_document(session, project_id)
    if document is None:
        return empty_annotation_payload()
    return AnnotationPayload.model_validate(document.data_json)


def save_annotation_payload(
    session: Session,
    project: Project,
    payload: AnnotationPayload,
) -> AnnotationPayload:
    data = payload.model_dump(mode="json")
    document = get_annotation_document(session, project.id)

    if document is None:
        now = utc_now()
        document = AnnotationDocument(
            project_id=project.id,
            data_json=data,
            created_at=now,
            updated_at=now,
        )
        session.add(document)
    else:
        document.data_json = data
        document.updated_at = utc_now()
        session.add(document)

    touch_project(session, project)
    session.commit()
    session.refresh(document)
    return AnnotationPayload.model_validate(document.data_json)
