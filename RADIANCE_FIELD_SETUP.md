# Gaussian splatting setup notes

The backend radiance worker expects the Nerfstudio CLI tools to be available on the PATH of the process running FastAPI:

- `ns-process-data`
- `ns-train`
- `ns-export`

The first implementation runs these commands:

```bash
ns-process-data images --data <job>/input_images --output-dir <job>/nerfstudio_data
ns-train splatfacto --data <job>/nerfstudio_data --output-dir <job>/nerfstudio_outputs --max-num-iterations 15000
ns-export gaussian-splat --load-config <config.yml> --output-dir <job>/exports
```

The output asset is copied into:

```text
data/radiance_fields/fields/<radiance_field_id>/scene.<format>
```

The DB stores the job state, field metadata, and relative asset paths. The actual splat files, logs, copied frames, Nerfstudio data, and exports remain on disk.

For a personal local setup, install Nerfstudio in its own environment, then start this FastAPI backend from a shell where those commands are available.
