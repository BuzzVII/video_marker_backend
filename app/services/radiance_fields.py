from __future__ import annotations

import json
import shlex
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from app.core.config import settings
from app.db.session import engine
from app.models.frame import Frame
from app.models.image_set import ImageSet
from app.models.radiance_field import RadianceField, RadianceFieldJob
from app.models.project import Project
from app.schemas.radiance_fields import RadianceFieldJobCreate
from app.services.projects import touch_project


FINAL_ASSET_NAMES = ("scene.ply", "splat.ply", "point_cloud.ply", "scene.splat", "scene.ksplat")


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def radiance_storage_root() -> Path:
    return settings.radiance_field_dir


def ensure_radiance_dirs() -> None:
    root = radiance_storage_root()
    (root / "jobs").mkdir(parents=True, exist_ok=True)
    (root / "fields").mkdir(parents=True, exist_ok=True)


def relative_to_data_dir(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(settings.data_dir.resolve()))
    except ValueError:
        return str(path)


def resolve_data_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return settings.data_dir / candidate


def make_job_work_dir(job_id: str) -> Path:
    ensure_radiance_dirs()
    return radiance_storage_root() / "jobs" / job_id


def make_field_dir(field_id: str) -> Path:
    ensure_radiance_dirs()
    return radiance_storage_root() / "fields" / field_id


def create_radiance_field_job(
    session: Session,
    project: Project,
    payload: RadianceFieldJobCreate,
) -> RadianceFieldJob:
    image_set = session.get(ImageSet, payload.image_set_id)
    if image_set is None or image_set.project_id != project.id:
        raise ValueError("Image set not found for project")

    job = RadianceFieldJob(
        project_id=project.id,
        image_set_id=image_set.id,
        name=payload.name or f"Radiance field from {image_set.name}",
        status="queued",
        stage="queued",
        progress=0.0,
        work_dir="",
        config_json=payload.config,
    )
    session.add(job)
    session.flush()

    work_dir = make_job_work_dir(job.id)
    work_dir.mkdir(parents=True, exist_ok=True)
    job.work_dir = relative_to_data_dir(work_dir)
    job.updated_at = utc_now()
    touch_project(session, project)
    session.commit()
    session.refresh(job)
    return job


def job_to_read(job: RadianceFieldJob) -> RadianceFieldJob:
    return job


def radiance_field_asset_url(project_id: str, field_id: str) -> str:
    return f"/api/projects/{project_id}/radiance-fields/{field_id}/asset"


def radiance_field_to_read(field: RadianceField) -> dict[str, Any]:
    return {
        "id": field.id,
        "project_id": field.project_id,
        "source_job_id": field.source_job_id,
        "source_image_set_id": field.source_image_set_id,
        "name": field.name,
        "status": field.status,
        "asset_path": field.asset_path,
        "asset_format": field.asset_format,
        "asset_url": radiance_field_asset_url(field.project_id, field.id),
        "metadata_json": field.metadata_json,
        "created_at": field.created_at,
        "updated_at": field.updated_at,
    }


def mark_job(
    job_id: str,
    *,
    status: str | None = None,
    stage: str | None = None,
    progress: float | None = None,
    error_message: str | None = None,
    result_radiance_field_id: str | None = None,
) -> None:
    with Session(engine) as session:
        job = session.get(RadianceFieldJob, job_id)
        if job is None:
            return
        if status is not None:
            job.status = status
        if stage is not None:
            job.stage = stage
        if progress is not None:
            job.progress = max(0.0, min(1.0, progress))
        if error_message is not None:
            job.error_message = error_message
        if result_radiance_field_id is not None:
            job.result_radiance_field_id = result_radiance_field_id
        job.updated_at = utc_now()
        session.add(job)
        session.commit()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def copy_input_frames(session: Session, image_set_id: str, input_dir: Path, config: dict[str, Any]) -> list[Frame]:
    input_dir.mkdir(parents=True, exist_ok=True)
    frame_step = max(1, int(config.get("frame_step", 1)))
    max_frames = config.get("max_frames")
    max_frames = int(max_frames) if max_frames else None

    frames = session.exec(
        select(Frame).where(Frame.image_set_id == image_set_id).order_by(Frame.frame_index)
    ).all()

    selected = frames[::frame_step]
    if max_frames is not None:
        selected = selected[:max_frames]
    if not selected:
        raise ValueError("No frames found for selected image set")

    for index, frame in enumerate(selected, start=1):
        source = Path(frame.image_path)
        if not source.exists():
            raise FileNotFoundError(f"Frame image is missing: {source}")
        suffix = source.suffix or ".jpg"
        shutil.copy2(source, input_dir / f"frame_{index:06d}{suffix}")

    return list(selected)


def command_with_extra_args(base_command: str, extra_args: list[str]) -> list[str]:
    return [*shlex.split(base_command), *extra_args]


def run_logged(command: list[str], cwd: Path, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as log:
        log.write("\n$ " + " ".join(shlex.quote(part) for part in command) + "\n")
        log.flush()
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        log.write(f"\n[exit code {completed.returncode}]\n")
        if completed.returncode != 0:
            raise RuntimeError(f"Command failed with exit code {completed.returncode}: {' '.join(command)}")


def find_training_config(train_output_dir: Path) -> Path:
    candidates = sorted(train_output_dir.rglob("config.yml")) + sorted(train_output_dir.rglob("config.yaml"))
    if not candidates:
        raise FileNotFoundError(f"Could not find Nerfstudio training config under {train_output_dir}")
    return candidates[-1]


def find_exported_asset(export_dir: Path, train_output_dir: Path) -> Path:
    candidates: list[Path] = []
    for root in (export_dir, train_output_dir):
        for suffix in ("*.ply", "*.splat", "*.ksplat"):
            candidates.extend(root.rglob(suffix))
    if not candidates:
        raise FileNotFoundError("Could not find exported radiance field asset")
    return max(candidates, key=lambda item: item.stat().st_mtime)


def create_field_from_asset(
    *,
    session: Session,
    job: RadianceFieldJob,
    image_set: ImageSet,
    asset_source: Path,
    selected_frames: list[Frame],
    metadata: dict[str, Any],
) -> RadianceField:
    field = RadianceField(
        project_id=job.project_id,
        source_job_id=job.id,
        source_image_set_id=image_set.id,
        name=job.name or f"Radiance field from {image_set.name}",
        status="available",
        asset_path="",
        asset_format=asset_source.suffix.lstrip(".") or "ply",
        metadata_json=metadata,
    )
    session.add(field)
    session.flush()

    field_dir = make_field_dir(field.id)
    field_dir.mkdir(parents=True, exist_ok=True)
    asset_dest = field_dir / f"scene.{field.asset_format}"
    shutil.copy2(asset_source, asset_dest)

    write_json(
        field_dir / "metadata.json",
        {
            **metadata,
            "field_id": field.id,
            "job_id": job.id,
            "asset_format": field.asset_format,
            "asset_path": relative_to_data_dir(asset_dest),
        },
    )
    write_json(
        field_dir / "source_frames.json",
        {
            "image_set_id": image_set.id,
            "frames": [
                {
                    "id": frame.id,
                    "frame_index": frame.frame_index,
                    "timestamp_seconds": frame.timestamp_seconds,
                    "image_path": frame.image_path,
                }
                for frame in selected_frames
            ],
        },
    )

    field.asset_path = relative_to_data_dir(asset_dest)
    field.updated_at = utc_now()
    session.add(field)
    session.commit()
    session.refresh(field)
    return field


def run_radiance_field_job(job_id: str) -> None:
    mark_job(job_id, status="running", stage="starting", progress=0.01, error_message="")

    try:
        with Session(engine) as session:
            job = session.get(RadianceFieldJob, job_id)
            if job is None:
                return
            image_set = session.get(ImageSet, job.image_set_id) if job.image_set_id else None
            if image_set is None:
                raise ValueError("Image set not found")

            work_dir = resolve_data_path(job.work_dir)
            work_dir.mkdir(parents=True, exist_ok=True)
            input_dir = work_dir / "input_images"
            ns_data_dir = work_dir / "nerfstudio_data"
            train_output_dir = work_dir / "nerfstudio_outputs"
            export_dir = work_dir / "exports"
            log_path = work_dir / "logs" / "radiance_job.log"

            mark_job(job_id, stage="copying_frames", progress=0.05)
            selected_frames = copy_input_frames(session, image_set.id, input_dir, job.config_json)
            write_json(
                work_dir / "job.json",
                {
                    "job_id": job.id,
                    "project_id": job.project_id,
                    "image_set_id": image_set.id,
                    "config": job.config_json,
                    "selected_frame_count": len(selected_frames),
                },
            )

        config = job.config_json
        downscale_factor = int(config.get("downscale_factor", 1))
        max_iterations = int(config.get("max_num_iterations", config.get("max_iterations", 15000)))
        method = str(config.get("method", settings.radiance_train_method))

        mark_job(job_id, stage="estimating_camera_poses", progress=0.15)
        process_args = [
            "images",
            "--data",
            str(input_dir),
            "--output-dir",
            str(ns_data_dir),
        ]
        if downscale_factor > 1:
            process_args.extend(["--downscale-factor", str(downscale_factor)])
        run_logged(command_with_extra_args(settings.radiance_ns_process_data_command, process_args), work_dir, log_path)

        mark_job(job_id, stage="training", progress=0.35)
        train_args = [
            method,
            "--data",
            str(ns_data_dir),
            "--output-dir",
            str(train_output_dir),
            "--max-num-iterations",
            str(max_iterations),
        ]
        run_logged(command_with_extra_args(settings.radiance_ns_train_command, train_args), work_dir, log_path)

        mark_job(job_id, stage="exporting", progress=0.9)
        training_config = find_training_config(train_output_dir)
        export_args = [
            "gaussian-splat",
            "--load-config",
            str(training_config),
            "--output-dir",
            str(export_dir),
        ]
        run_logged(command_with_extra_args(settings.radiance_ns_export_command, export_args), work_dir, log_path)

        asset_source = find_exported_asset(export_dir, train_output_dir)

        with Session(engine) as session:
            job = session.get(RadianceFieldJob, job_id)
            if job is None:
                return
            image_set = session.get(ImageSet, job.image_set_id) if job.image_set_id else None
            if image_set is None:
                raise ValueError("Image set not found")
            selected_frames = session.exec(
                select(Frame).where(Frame.image_set_id == image_set.id).order_by(Frame.frame_index)
            ).all()
            frame_step = max(1, int(job.config_json.get("frame_step", 1)))
            selected_frames = list(selected_frames[::frame_step])
            max_frames = job.config_json.get("max_frames")
            if max_frames:
                selected_frames = selected_frames[: int(max_frames)]

            field = create_field_from_asset(
                session=session,
                job=job,
                image_set=image_set,
                asset_source=asset_source,
                selected_frames=selected_frames,
                metadata={
                    "method": method,
                    "max_num_iterations": max_iterations,
                    "downscale_factor": downscale_factor,
                    "num_input_frames": len(selected_frames),
                    "training_config_path": relative_to_data_dir(training_config),
                    "job_work_dir": job.work_dir,
                },
            )
            job.result_radiance_field_id = field.id
            job.status = "succeeded"
            job.stage = "done"
            job.progress = 1.0
            job.error_message = None
            job.updated_at = utc_now()
            session.add(job)
            session.commit()

    except Exception as exc:
        mark_job(job_id, status="failed", stage="failed", error_message=str(exc))
