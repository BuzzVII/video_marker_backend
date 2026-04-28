from sqlmodel import Session, select

from app.models.frame import Frame
from app.models.image_set import ImageSet
from app.schemas.annotations import AnnotationPayload
from app.schemas.exports import (
    ExportFrame,
    ExportImageSet,
    LineExport,
    LineObservationExport,
    PointExport,
    PointObservationExport,
    ReconstructionExport,
)
from app.services.annotations import get_annotation_payload


def coordinate_to_normalized(value: float) -> float:
    # The frontend currently uses 0..100 percentages. Accept 0..1 as already normalized.
    if value > 1.0:
        return value / 100.0
    return value


def build_reconstruction_export(session: Session, image_set: ImageSet) -> ReconstructionExport:
    frames = session.exec(
        select(Frame).where(Frame.image_set_id == image_set.id).order_by(Frame.frame_index)
    ).all()
    frame_by_id = {frame.id: frame for frame in frames}
    annotations: AnnotationPayload = get_annotation_payload(session, image_set.id)

    points: list[PointExport] = []
    for point_id, positions_by_frame in annotations.pointPositionsByPointId.items():
        observations: list[PointObservationExport] = []

        for frame_id, position in positions_by_frame.items():
            frame = frame_by_id.get(frame_id)
            if frame is None:
                continue

            x_normalized = coordinate_to_normalized(position.x)
            y_normalized = coordinate_to_normalized(position.y)

            observations.append(
                PointObservationExport(
                    image_id=frame_id,
                    x_normalized=x_normalized,
                    y_normalized=y_normalized,
                    x_pixels=x_normalized * frame.width,
                    y_pixels=y_normalized * frame.height,
                )
            )

        points.append(PointExport(id=point_id, observations=observations))

    lines: list[LineExport] = []
    for line_id, occurrences_by_frame in annotations.lineOccurrencesByLineId.items():
        observations: list[LineObservationExport] = []

        for frame_id, occurrence in occurrences_by_frame.items():
            if frame_id not in frame_by_id:
                continue

            observations.append(
                LineObservationExport(
                    image_id=frame_id,
                    start_point_id=occurrence.startPointId,
                    end_point_id=occurrence.endPointId,
                )
            )

        lines.append(LineExport(id=line_id, observations=observations))

    return ReconstructionExport(
        image_set=ExportImageSet(id=image_set.id, name=image_set.name),
        frames=[
            ExportFrame(
                id=frame.id,
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
