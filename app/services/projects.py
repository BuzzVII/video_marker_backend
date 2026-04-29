from datetime import datetime, timezone

from sqlmodel import Session

from app.models.project import Project


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_project(session: Session, name: str) -> Project:
    project = Project(name=name)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def touch_project(session: Session, project: Project) -> None:
    project.updated_at = utc_now()
    session.add(project)
