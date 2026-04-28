# House Marker API

FastAPI backend for a house image annotation workflow. The app accepts a video upload, extracts frames, serves those frames to the frontend, stores point and line annotations in SQLite, and exports a reconstruction friendly JSON document.

The API shape follows the current brief:

```text
GET    /api/health
GET    /api/image-sets
POST   /api/videos/upload
GET    /api/image-sets/{image_set_id}
GET    /api/image-sets/{image_set_id}/frames/{frame_id}/image
GET    /api/image-sets/{image_set_id}/annotations
PUT    /api/image-sets/{image_set_id}/annotations
GET    /api/image-sets/{image_set_id}/export
```

## Project layout

```text
house_marker_api/
  app/
    api/
      health.py          # health endpoint
      image_sets.py      # image set, frame image, annotation, export endpoints
      videos.py          # video upload endpoint
    core/
      config.py          # environment settings
    db/
      session.py         # SQLModel engine and session dependency
    models/
      annotation_document.py
      frame.py
      image_set.py       # SQLModel database tables
    schemas/
      annotations.py
      exports.py
      image_sets.py      # request and response schemas
    services/
      annotations.py
      exports.py
      frame_extraction.py
      storage.py         # reusable business logic
    main.py
  alembic/
    versions/
      0001_initial.py    # initial database schema
    env.py
  data/
    uploads/             # uploaded source videos
    frames/              # extracted frame images
  pyproject.toml
  alembic.ini
  .env.example
```

## Install uv

Use the official installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then restart your shell, or source the path shown by the installer.

## Create the app locally

```bash
unzip house_marker_api.zip
cd house_marker_api
cp .env.example .env
uv sync
```

## Create the SQLite database

The initial migration is already included.

```bash
uv run alembic upgrade head
```

This creates:

```text
data/app.db
```

## Run the API

```bash
uv run fastapi dev app/main.py
```

The API will be available at:

```text
http://127.0.0.1:8000
```

The interactive docs will be available at:

```text
http://127.0.0.1:8000/docs
```

## Test the health endpoint

```bash
curl http://127.0.0.1:8000/api/health
```

Expected response:

```json
{"ok": true}
```

## Upload a video

```bash
curl -X POST   -F "file=@/path/to/video.mp4"   http://127.0.0.1:8000/api/videos/upload
```

The app saves the uploaded video under `data/uploads/`, extracts frames under `data/frames/{image_set_id}/`, creates an image set, and returns metadata like:

```json
{
  "id": "set-abc123",
  "name": "video",
  "created_at": "2026-04-28T06:20:00",
  "frame_count": 120,
  "source_type": "video"
}
```

## List image sets

```bash
curl http://127.0.0.1:8000/api/image-sets
```

## Read one image set and its frames

```bash
curl http://127.0.0.1:8000/api/image-sets/{image_set_id}
```

Frame records include a `url` field that the frontend can use directly:

```json
{
  "id": "frame-000001",
  "label": "Frame 1",
  "url": "/api/image-sets/set-a/frames/frame-000001/image",
  "width": 1920,
  "height": 1080,
  "frame_index": 1,
  "timestamp_seconds": 0.0
}
```

## Read annotations

```bash
curl http://127.0.0.1:8000/api/image-sets/{image_set_id}/annotations
```

New image sets return an empty annotation document:

```json
{
  "pointsById": {},
  "pointPositionsByPointId": {},
  "linesById": {},
  "lineOccurrencesByLineId": {}
}
```

## Save annotations

The first version saves the whole annotation document at once. This keeps the backend simple while the frontend state model is still changing.

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
        "frame-000001": {
          "pointId": "point-1",
          "imageId": "frame-000001",
          "x": 41.2,
          "y": 63.8
        }
      }
    },
    "linesById": {},
    "lineOccurrencesByLineId": {}
  }'   http://127.0.0.1:8000/api/image-sets/{image_set_id}/annotations
```

The backend accepts the frontend percentage style coordinates, such as `41.2`, and converts them to normalized coordinates only in the export endpoint.

## Export for reconstruction

```bash
curl http://127.0.0.1:8000/api/image-sets/{image_set_id}/export
```

The export includes frame metadata, point observations in normalized and pixel coordinates, and line observations:

```json
{
  "image_set": {
    "id": "set-a",
    "name": "Kitchen walkthrough"
  },
  "frames": [],
  "points": [],
  "lines": []
}
```

## Frame extraction settings

By default the app extracts one frame every `0.5` seconds.

Change this in `.env`:

```env
FRAME_SAMPLE_SECONDS=0.5
```

## Frontend endpoint constants

```js
export const API_ENDPOINTS = {
  health: "/api/health",

  imageSets: "/api/image-sets",
  imageSet: id => `/api/image-sets/${id}`,

  uploadVideo: "/api/videos/upload",

  frameImage: (imageSetId, frameId) =>
    `/api/image-sets/${imageSetId}/frames/${frameId}/image`,

  annotations: imageSetId =>
    `/api/image-sets/${imageSetId}/annotations`,

  saveAnnotations: imageSetId =>
    `/api/image-sets/${imageSetId}/annotations`,

  exportAnnotations: imageSetId =>
    `/api/image-sets/${imageSetId}/export`,
};
```

## Creating future migrations

After changing SQLModel table models:

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

## Notes

This implementation stores annotations as one JSON document per image set:

```text
AnnotationDocument
  image_set_id
  data_json
  updated_at
```

That is deliberate for the first version. Once the annotation model settles, the document can be split into relational tables for points, point observations, lines, and line observations.
