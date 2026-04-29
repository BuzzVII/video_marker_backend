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
    annotations: AnnotationPayload = get_annotation_payload(session, project.id)

    points: list[PointExport] = []
    for point_id, observations_by_id in annotations.pointObservationsByPointId.items():
        observations: list[PointObservationExport] = []

        for _, observation in observations_by_id.items():
            frame = frame_by_key.get((observation.imageSetId, observation.frameId))
            if frame is None:
                continue

            x_normalized = coordinate_to_normalized(observation.x)
            y_normalized = coordinate_to_normalized(observation.y)

            observations.append(
                PointObservationExport(
                    image_set_id=observation.imageSetId,
                    image_id=observation.frameId,
                    x_normalized=x_normalized,
                    y_normalized=y_normalized,
                    x_pixels=x_normalized * frame.width if frame.width is not None else None,
                    y_pixels=y_normalized * frame.height if frame.height is not None else None,
                )
            )

        points.append(PointExport(id=point_id, observations=observations))

    lines: list[LineExport] = []
    for line_id, observations_by_id in annotations.lineObservationsByLineId.items():
        observations: list[LineObservationExport] = []

        for _, observation in observations_by_id.items():
            frame = frame_by_key.get((observation.imageSetId, observation.frameId))
            if frame is None:
                continue

            observations.append(
                LineObservationExport(
                    image_set_id=observation.imageSetId,
                    image_id=observation.frameId,
                    start_point_id=observation.startPointId,
                    end_point_id=observation.endPointId,
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
