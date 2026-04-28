# House Marker API

FastAPI backend for a house image annotation workflow. The app now has project scoped annotations, so a single project can contain multiple image sets and one shared annotation document.

The intended model is:

```text
Project
  has many ImageSet records
  has one AnnotationDocument

ImageSet
  has many Frame records

AnnotationDocument
  stores points and lines observed across any image set in the project
```

## API

```text
GET    /api/health

GET    /api/projects
POST   /api/projects
GET    /api/projects/{project_id}

GET    /api/projects/{project_id}/image-sets
POST   /api/projects/{project_id}/videos/upload

GET    /api/image-sets
GET    /api/image-sets/{image_set_id}
GET    /api/image-sets/{image_set_id}/frames/{frame_id}/image

GET    /api/projects/{project_id}/annotations
PUT    /api/projects/{project_id}/annotations

GET    /api/projects/{project_id}/export
```

There is also a compatibility endpoint:

```text
POST   /api/videos/upload
```

That endpoint creates a project automatically and uploads the video as the first image set in that project. New frontend code should use the project scoped upload endpoint instead.

## Project layout

```text
house_marker_api/
  app/
    api/
      health.py
      image_sets.py
      projects.py
      videos.py
    core/
      config.py
    db/
      session.py
    models/
      annotation_document.py
      frame.py
      image_set.py
      project.py
    schemas/
      annotations.py
      exports.py
      image_sets.py
      projects.py
    services/
      annotations.py
      exports.py
      frame_extraction.py
      projects.py
      storage.py
      videos.py
    main.py
  alembic/
    versions/
      0001_initial.py
      0002_add_projects.py
    env.py
  data/
    uploads/
    frames/
  pyproject.toml
  alembic.ini
  .env.example
```

## Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then restart your shell, or source the path shown by the installer.

## Setup

```bash
unzip house_marker_api_project_api.zip
cd house_marker_api
cp .env.example .env
uv sync
uv run alembic upgrade head
```

## Run the API

```bash
uv run fastapi dev app/main.py
```

Open the API docs at:

```text
http://127.0.0.1:8000/docs
```

## Create a project

```bash
curl -X POST   -H "Content-Type: application/json"   -d '{"name": "House scan"}'   http://127.0.0.1:8000/api/projects
```

Response:

```json
{
  "id": "project-abc123",
  "name": "House scan",
  "created_at": "2026-04-28T06:20:00",
  "updated_at": "2026-04-28T06:20:00",
  "image_set_count": 0
}
```

## Upload a video into a project

```bash
curl -X POST   -F "file=@/path/to/video.mp4"   http://127.0.0.1:8000/api/projects/{project_id}/videos/upload
```

This creates a new image set under the project and extracts frames.

Response:

```json
{
  "id": "set-abc123",
  "project_id": "project-abc123",
  "name": "kitchen video",
  "created_at": "2026-04-28T06:20:00",
  "frame_count": 120,
  "source_type": "video"
}
```

## List image sets in a project

```bash
curl http://127.0.0.1:8000/api/projects/{project_id}/image-sets
```

## Read one image set and its frames

```bash
curl http://127.0.0.1:8000/api/image-sets/{image_set_id}
```

Frame ids are globally unique because they include the image set id:

```json
{
  "id": "set-abc123-frame-000001",
  "label": "Frame 1",
  "url": "/api/image-sets/set-abc123/frames/set-abc123-frame-000001/image",
  "width": 1920,
  "height": 1080,
  "frame_index": 1,
  "timestamp_seconds": 0.0
}
```

## Read project annotations

```bash
curl http://127.0.0.1:8000/api/projects/{project_id}/annotations
```

New projects return:

```json
{
  "pointsById": {},
  "pointPositionsByPointId": {},
  "linesById": {},
  "lineOccurrencesByLineId": {}
}
```

## Save project annotations

Point observations can now include both `imageSetId` and `imageId`:

```bash
curl -X PUT   -H "Content-Type: application/json"   -d '{
    "pointsById": {
      "point-1": {
        "id": "point-1",
        "color": "hsl(0, 85%, 55%)"
      }
    },
    "pointPositionsByPointId": {
      "point-1": {
        "obs-1": {
          "pointId": "point-1",
          "imageSetId": "set-abc123",
          "imageId": "set-abc123-frame-000001",
          "x": 41.2,
          "y": 63.8
        }
      }
    },
    "linesById": {},
    "lineOccurrencesByLineId": {}
  }'   http://127.0.0.1:8000/api/projects/{project_id}/annotations
```

Line observations use the same idea:

```json
{
  "lineId": "line-1",
  "imageSetId": "set-abc123",
  "imageId": "set-abc123-frame-000001",
  "startPointId": "point-1",
  "endPointId": "point-2"
}
```

The backend accepts frontend percentage coordinates, such as `41.2`, and converts them to normalized coordinates only in the export endpoint. If coordinates are already `0` to `1`, they are left unchanged.

## Export for reconstruction

```bash
curl http://127.0.0.1:8000/api/projects/{project_id}/export
```

The export shape is:

```json
{
  "project": {
    "id": "project-1",
    "name": "House scan"
  },
  "image_sets": [
    {
      "id": "set-1",
      "name": "Kitchen video"
    }
  ],
  "frames": [
    {
      "id": "set-1-frame-000001",
      "image_set_id": "set-1",
      "width": 1920,
      "height": 1080,
      "frame_index": 1,
      "timestamp_seconds": 0.0
    }
  ],
  "points": [
    {
      "id": "point-1",
      "observations": [
        {
          "image_set_id": "set-1",
          "image_id": "set-1-frame-000001",
          "x_normalized": 0.412,
          "y_normalized": 0.638,
          "x_pixels": 791.04,
          "y_pixels": 689.04
        }
      ]
    }
  ],
  "lines": [
    {
      "id": "line-1",
      "observations": [
        {
          "image_set_id": "set-1",
          "image_id": "set-1-frame-000001",
          "start_point_id": "point-1",
          "end_point_id": "point-2"
        }
      ]
    }
  ]
}
```

## Migration notes

Fresh setup:

```bash
uv run alembic upgrade head
```

Existing database from version 0.1:

```bash
uv run alembic upgrade head
```

The `0002_add_projects.py` migration creates one project per existing image set and moves each existing annotation document from image set scope to project scope.

## Creating future migrations

After changing SQLModel table models:

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

## Frontend endpoint constants

```js
export const API_ENDPOINTS = {
  health: "/api/health",

  projects: "/api/projects",
  project: id => `/api/projects/${id}`,

  projectImageSets: projectId =>
    `/api/projects/${projectId}/image-sets`,

  uploadVideoToProject: projectId =>
    `/api/projects/${projectId}/videos/upload`,

  imageSet: id => `/api/image-sets/${id}`,

  frameImage: (imageSetId, frameId) =>
    `/api/image-sets/${imageSetId}/frames/${frameId}/image`,

  annotations: projectId =>
    `/api/projects/${projectId}/annotations`,

  saveAnnotations: projectId =>
    `/api/projects/${projectId}/annotations`,

  exportAnnotations: projectId =>
    `/api/projects/${projectId}/export`,
};
```
