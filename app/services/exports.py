from sqlmodel import Session, select

from app.models.frame import Frame
from app.models.image_set import ImageSet
from app.models.project import Project
from app.schemas.annotations import AnnotationPayload
from app.schemas.exports import (
    ExportFrame,
    ExportImageSet,
    ExportProject,
    LineExport,
    LineObservationExport,
    PointExport,
    PointObservationExport,
    ReconstructionExport,
)
from app.services.annotations import get_annotation_payload


def coordinate_to_normalized(value: float) -> float:
    # The frontend may send 0..100 percentages. Accept 0..1 as already normalized.
    if value > 1.0:
        return value / 100.0
    return value


def build_reconstruction_export(session: Session, project: Project) -> ReconstructionExport:
    image_sets = session.exec(
        select(ImageSet).where(ImageSet.project_id == project.id).order_by(ImageSet.created_at)
    ).all()
    image_set_ids = [image_set.id for image_set in image_sets]

    if image_set_ids:
        frames = session.exec(
            select(Frame).where(Frame.image_set_id.in_(image_set_ids)).order_by(
                Frame.image_set_id, Frame.frame_index
            )
        ).all()
    else:
        frames = []

    frame_by_key = {(frame.image_set_id, frame.id): frame for frame in frames}
    frames_by_id: dict[str, list[Frame]] = {}
    for frame in frames:
        frames_by_id.setdefault(frame.id, []).append(frame)

    annotations: AnnotationPayload = get_annotation_payload(session, project.id)

    points: list[PointExport] = []
    for point_id, positions_by_observation_id in annotations.pointPositionsByPointId.items():
        observations: list[PointObservationExport] = []

        for _, position in positions_by_observation_id.items():
            frame = None
            image_set_id = position.imageSetId

            if image_set_id is not None:
                frame = frame_by_key.get((image_set_id, position.imageId))
            else:
                candidates = frames_by_id.get(position.imageId, [])
                if len(candidates) == 1:
                    frame = candidates[0]
                    image_set_id = frame.image_set_id

            if frame is None or image_set_id is None:
                continue

            x_normalized = coordinate_to_normalized(position.x)
            y_normalized = coordinate_to_normalized(position.y)

            observations.append(
                PointObservationExport(
                    image_set_id=image_set_id,
                    image_id=position.imageId,
                    x_normalized=x_normalized,
                    y_normalized=y_normalized,
                    x_pixels=x_normalized * frame.width,
                    y_pixels=y_normalized * frame.height,
                )
            )

        points.append(PointExport(id=point_id, observations=observations))

    lines: list[LineExport] = []
    for line_id, occurrences_by_observation_id in annotations.lineOccurrencesByLineId.items():
        observations: list[LineObservationExport] = []

        for _, occurrence in occurrences_by_observation_id.items():
            image_set_id = occurrence.imageSetId
            frame = None

            if image_set_id is not None:
                frame = frame_by_key.get((image_set_id, occurrence.imageId))
            else:
                candidates = frames_by_id.get(occurrence.imageId, [])
                if len(candidates) == 1:
                    frame = candidates[0]
                    image_set_id = frame.image_set_id

            if frame is None or image_set_id is None:
                continue

            observations.append(
                LineObservationExport(
                    image_set_id=image_set_id,
                    image_id=occurrence.imageId,
                    start_point_id=occurrence.startPointId,
                    end_point_id=occurrence.endPointId,
                )
            )

        lines.append(LineExport(id=line_id, observations=observations))

    return ReconstructionExport(
        project=ExportProject(id=project.id, name=project.name),
        image_sets=[ExportImageSet(id=image_set.id, name=image_set.name) for image_set in image_sets],
        frames=[
            ExportFrame(
                id=frame.id,
                image_set_id=frame.image_set_id,
                width=frame.width,
                height=frame.height,
                frame_index=frame.frame_index,
                timestamp_seconds=frame.timestamp_seconds,
            )
            for frame in frames
        ],
        points=points,
        lines=lines,
    )
