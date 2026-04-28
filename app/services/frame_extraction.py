from pathlib import Path

import cv2
from sqlmodel import Session

from app.core.config import settings
from app.models.frame import Frame


def extract_frames(
    *,
    video_path: Path,
    image_set_id: str,
    session: Session,
    sample_seconds: float | None = None,
) -> list[Frame]:
    sample_seconds = sample_seconds or settings.frame_sample_seconds
    if sample_seconds <= 0:
        raise ValueError("sample_seconds must be greater than 0")

    out_dir = settings.frame_dir / image_set_id
    out_dir.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30.0

    frame_step = max(1, int(round(fps * sample_seconds)))
    frames: list[Frame] = []
    raw_index = 0
    saved_index = 0

    while True:
        ok, image = capture.read()
        if not ok:
            break

        if raw_index % frame_step == 0:
            height, width = image.shape[:2]
            frame_number = saved_index + 1
            frame_id = f"{image_set_id}-frame-{frame_number:06d}"
            image_path = out_dir / f"{frame_id}.jpg"

            write_ok = cv2.imwrite(str(image_path), image, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
            if not write_ok:
                raise ValueError(f"Could not write frame image: {image_path}")

            frame = Frame(
                id=frame_id,
                image_set_id=image_set_id,
                frame_index=frame_number,
                timestamp_seconds=raw_index / fps,
                image_path=str(image_path),
                width=width,
                height=height,
            )
            session.add(frame)
            frames.append(frame)
            saved_index += 1

        raw_index += 1

    capture.release()

    if not frames:
        raise ValueError("No frames were extracted from the uploaded video")

    return frames
