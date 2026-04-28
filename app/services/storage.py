from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


def ensure_data_dirs() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.frame_dir.mkdir(parents=True, exist_ok=True)


def safe_stem(filename: str | None) -> str:
    if not filename:
        return "upload"
    stem = Path(filename).stem.strip().replace(" ", "_")
    safe = "".join(ch for ch in stem if ch.isalnum() or ch in {"_", "-"})
    return safe or "upload"


async def save_upload_file(file: UploadFile) -> Path:
    ensure_data_dirs()
    suffix = Path(file.filename or "").suffix or ".mp4"
    out_path = settings.upload_dir / f"{uuid4().hex}{suffix}"

    with out_path.open("wb") as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)

    return out_path
