from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.annotation_document import AnnotationDocument
from app.schemas.annotations import AnnotationPayload, empty_annotation_payload


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
    project_id: str,
    payload: AnnotationPayload,
) -> AnnotationPayload:
    data = payload.model_dump(mode="json")
    document = get_annotation_document(session, project_id)

    if document is None:
        document = AnnotationDocument(
            project_id=project_id,
            data_json=data,
            updated_at=utc_now(),
        )
        session.add(document)
    else:
        document.data_json = data
        document.updated_at = utc_now()
        session.add(document)

    session.commit()
    session.refresh(document)
    return AnnotationPayload.model_validate(document.data_json)
