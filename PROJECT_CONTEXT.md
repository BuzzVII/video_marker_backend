# Project context

This backend is the FastAPI and SQLModel API for the video marker house plan fitting app. The project stores uploaded videos as image sets, extracted frames, project annotations, and explicit reconstruction models made from cuboids and constraints.

This package adds the first radiance field backend support. It is intentionally simple and local first:

- `RadianceFieldJob` tracks a processing attempt.
- `RadianceField` tracks a completed loadable result.
- SQLite stores status, metadata, configuration, and relative asset paths.
- Files are stored on disk under `data/radiance_fields`.
- FastAPI `BackgroundTasks` runs the first version of the processing job.
- The worker copies existing extracted image set frames, runs Nerfstudio commands, exports a Gaussian splat asset, and registers the result.

The design goal is not to make the radiance field the measured house model. The radiance field is a visual reconstruction layer. The explicit cuboid, wall, point, line, and length constraint model remains the auditable measurable model.

Important files added or changed:

- `app/models/radiance_field.py`
- `app/schemas/radiance_fields.py`
- `app/services/radiance_fields.py`
- `app/api/radiance_fields.py`
- `alembic/versions/0004_radiance_fields.py`
- `app/main.py`
- `app/core/config.py`
- `app/services/storage.py`
- `.env.example`

The worker expects Nerfstudio CLI tools to be available on the backend process PATH:

- `ns-process-data`
- `ns-train`
- `ns-export`

The exact commands can be overridden with environment variables:

- `RADIANCE_NS_PROCESS_DATA_COMMAND`
- `RADIANCE_NS_TRAIN_COMMAND`
- `RADIANCE_NS_EXPORT_COMMAND`
- `RADIANCE_TRAIN_METHOD`
