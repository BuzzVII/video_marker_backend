from functools import cached_property
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/app.db"
    data_dir: Path = Path("./data")
    upload_dir: Path = Path("./data/uploads")
    frame_dir: Path = Path("./data/frames")
    radiance_field_dir: Path = Path("./data/radiance_fields")
    frame_sample_seconds: float = 0.5
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    radiance_ns_process_data_command: str = "ns-process-data"
    radiance_ns_train_command: str = "ns-train"
    radiance_ns_export_command: str = "ns-export"
    radiance_train_method: str = "splatfacto"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @cached_property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
