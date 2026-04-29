# House Marker API

FastAPI backend for a project based image annotation and cuboid reconstruction workflow. It uses uv, SQLite, SQLModel and Alembic.

The main change in this version is that annotations and reconstruction models belong to a project, not to an individual image set. Image sets still own their frames.

## API summary

```text
GET    /api/health

GET    /api/projects
POST   /api/projects
GET    /api/projects/{project_id}
PATCH  /api/projects/{project_id}
DELETE /api/projects/{project_id}

GET    /api/projects/{project_id}/image-sets
POST   /api/projects/{project_id}/image-sets
POST   /api/projects/{project_id}/videos/upload

GET    /api/image-sets
GET    /api/image-sets/{image_set_id}
DELETE /api/image-sets/{image_set_id}
GET    /api/image-sets/{image_set_id}/frames/{frame_id}/image

GET    /api/projects/{project_id}/annotations
PUT    /api/projects/{project_id}/annotations

GET    /api/projects/{project_id}/models/latest
GET    /api/projects/{project_id}/models
POST   /api/projects/{project_id}/models
GET    /api/projects/{project_id}/models/{model_id}
PUT    /api/projects/{project_id}/models/{model_id}
DELETE /api/projects/{project_id}/models/{model_id}

GET    /api/projects/{project_id}/export

POST   /api/videos/upload
```

`POST /api/videos/upload` is kept as a compatibility route. It creates a project automatically and uploads the video into that project.

## Data model

```text
Project
  id
  name
  created_at
  updated_at

ImageSet
  id
  project_id
  name
  source_type
  original_video_path
  created_at
  updated_at

Frame
  id
  image_set_id
  frame_index
  timestamp_seconds
  image_path
  width
  height
  created_at

AnnotationDocument
  id
  project_id
  data_json
  created_at
  updated_at

ReconstructionModel
  id
  project_id
  version
  data_json
  source
  created_at
  updated_at
```

Cuboids, vertices, edges, point to vertex constraints and edge length constraints are stored inside `ReconstructionModel.data_json`. They are not separate SQL tables in this first pass.

## Setup

```bash
unzip house_marker_api_project_models.zip
cd house_marker_api
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run fastapi dev app/main.py
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Create a project

```bash
curl -X POST   -H "Content-Type: application/json"   -d '{"name":"House scan"}'   http://127.0.0.1:8000/api/projects
```

## Upload a video into a project

```bash
curl -X POST   -F "file=@/path/to/video.mp4"   http://127.0.0.1:8000/api/projects/{project_id}/videos/upload
```

## Create an empty image set

```bash
curl -X POST   -H "Content-Type: application/json"   -d '{"name":"Manual image set","source_type":"manual"}'   http://127.0.0.1:8000/api/projects/{project_id}/image-sets
```

This creates an image set record without frames. Image group upload endpoints can be added later.

## Project level annotations

Annotations now belong to the project.

```json
{
  "pointsById": {
    "point-1": {
      "id": "point-1",
      "label": "corner",
      "color": "hsl(0, 85%, 55%)"
    }
  },
  "pointObservationsByPointId": {
    "point-1": {
      "obs-1": {
        "pointId": "point-1",
        "imageSetId": "set-1",
        "frameId": "set-1-frame-000001",
        "x": 41.2,
        "y": 63.8
      }
    }
  },
  "linesById": {},
  "lineObservationsByLineId": {}
}
```

Read annotations:

```bash
curl http://127.0.0.1:8000/api/projects/{project_id}/annotations
```

Save annotations:

```bash
curl -X PUT   -H "Content-Type: application/json"   -d @annotations.json   http://127.0.0.1:8000/api/projects/{project_id}/annotations
```

## Reconstruction model JSON

A project can have many reconstruction model versions. The latest model is the one with the highest version number.

```json
{
  "data_json": {
    "cuboidsById": {
      "cuboid-1": {
        "id": "cuboid-1",
        "label": "Room block",
        "center": [0, 0, 1.2],
        "size": [4.0, 3.0, 2.4],
        "rotation": [0, 0, 0, 1],
        "color": "#9ecae1",
        "locked": false,
        "createdFrom": {
          "manual": true
        }
      }
    },
    "pointVertexConstraintsById": {
      "pvc-1": {
        "id": "pvc-1",
        "pointId": "point-1",
        "vertex": {
          "cuboidId": "cuboid-1",
          "vertexIndex": 0
        },
        "source": "manual"
      }
    },
    "edgeLengthConstraintsById": {
      "elc-1": {
        "id": "elc-1",
        "edge": {
          "cuboidId": "cuboid-1",
          "edgeIndex": 0,
          "startVertexIndex": 0,
          "endVertexIndex": 1
        },
        "length": 4.0,
        "unit": "m",
        "source": "manual"
      }
    },
    "activeCuboidId": "cuboid-1",
    "activeVertex": null,
    "activeEdge": null
  },
  "source": "manual"
}
```

Create a model:

```bash
curl -X POST   -H "Content-Type: application/json"   -d @model.json   http://127.0.0.1:8000/api/projects/{project_id}/models
```

Get latest model:

```bash
curl http://127.0.0.1:8000/api/projects/{project_id}/models/latest
```

Update a model:

```bash
curl -X PUT   -H "Content-Type: application/json"   -d @model_update.json   http://127.0.0.1:8000/api/projects/{project_id}/models/{model_id}
```

## Cuboid convention

```text
center = [x, y, z]
size = [width, depth, height]
rotation = quaternion [x, y, z, w]
```

Vertex convention in local cuboid coordinates:

```text
0 [-0.5, -0.5, -0.5]
1 [ 0.5, -0.5, -0.5]
2 [ 0.5,  0.5, -0.5]
3 [-0.5,  0.5, -0.5]
4 [-0.5, -0.5,  0.5]
5 [ 0.5, -0.5,  0.5]
6 [ 0.5,  0.5,  0.5]
7 [-0.5,  0.5,  0.5]
```

Edge convention:

```text
0  [0, 1]
1  [1, 2]
2  [2, 3]
3  [3, 0]
4  [4, 5]
5  [5, 6]
6  [6, 7]
7  [7, 4]
8  [0, 4]
9  [1, 5]
10 [2, 6]
11 [3, 7]
```

## Existing database migration

For an existing database from the previous scaffold:

```bash
uv run alembic upgrade head
```

The new migration adds timestamps where needed and creates the `reconstruction_model` table.

## Future work

The API intentionally stores annotation and reconstruction documents as JSON. Once the workflow settles, cuboids, observations and constraints can be normalised into separate SQL tables without changing the project level ownership model.
