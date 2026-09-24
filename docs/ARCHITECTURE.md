# Deliberately small architecture

```text
local photo/sketch --manual browser calibration/tracing--> JSON recipe
user dimensions ----------------------------------------> JSON recipe
JSON -> strict validation -> rotational mesh -> OBJ / GLB / mesh.json
                                           -> optional Blender .blend adapter
mesh.json -> local on-demand WebGL viewer
```

No image-to-3D service, application server, database, build daemon, browser bridge or cloud account. The provided Python static server is a local viewing aid only; it exposes no model-generation API.

`jr_modelkit/geometry.py` owns parameter normalization and geometry. `exporters.py` owns serialization. `__main__.py` handles bounded local file input and new output directories. `web/` consumes or creates data but has no shell execution. The Blender script imports the same geometry implementation.

Explicit sections use positive material polygons in the R/Z half-plane. Their rotation yields a closed orientable material surface. At the axis, vertices collapse into one pole; no degenerate ring triangles are emitted. Polygon orientation is normalized, and generated edge counts/orientation and positive material volume are checked.

Normals are smoothed for a lightweight visual preview; they are not a photorealistic rim treatment. Direct GLB export avoids requiring Blender for the first demo. No claim is made that this writer covers the entire glTF specification; it intentionally emits an elementary static triangle subset.

Out of scope: general polygon offsetting, automatic segmentation, preserving arbitrary SVG Beziers, concave 3D boolean repairs, physical collisions, two-way Blender editing, source photo texture projection, remote quotation routing and scene migration.
