from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session

from app.models.annotation_document import AnnotationDocument
from app.schemas.annotations import AnnotationPayload, empty_annotation_payload


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_annotation_payload(session: Session, image_set_id: str) -> AnnotationPayload:
    document = session.get(AnnotationDocument, image_set_id)
    if document is None:
        return empty_annotation_payload()
    return AnnotationPayload.model_validate(document.data_json)


def save_annotation_payload(
    session: Session,
    image_set_id: str,
    payload: AnnotationPayload,
) -> AnnotationPayload:
    data = payload.model_dump(mode="json")
    document = session.get(AnnotationDocument, image_set_id)

    if document is None:
        document = AnnotationDocument(
            image_set_id=image_set_id,
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


def annotation_as_dict(session: Session, image_set_id: str) -> dict[str, Any]:
    return get_annotation_payload(session, image_set_id).model_dump(mode="json")
