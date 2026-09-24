# Input contract — schema version 1

Only JSON recipes are accepted by the geometry CLI. Input is limited to 256,000 bytes, 1–8 parts, 3–256 section points per part and 24–256 angular segments in multiples of four. All numbers must be finite. Unknown keys, repeated JSON keys and unsafe IDs are rejected. Recipes contain data, not executable scripts or paths for generated filenames.

## Option A — six values for a straight tapered bowl

```json
{
  "schema_version": 1,
  "units": "mm",
  "segments": 96,
  "parts": [{
    "id": "my_bowl",
    "source_status": "USER_ENTERED_MEASUREMENTS",
    "tapered_bowl": {
      "top_diameter_mm": 160,
      "base_diameter_mm": 112,
      "height_mm": 48,
      "wall_thickness_mm": 1.2,
      "floor_thickness_mm": 1.4
    }
  }]
}
```

The values above are invented examples. Choose your own inputs. This preset has no rounded corners, retaining lip or model-specific snap fit. `top_diameter_mm` is the maximum outer diameter at the top; `base_diameter_mm` is the exterior base of this idealized shape. It is not an assertion about measurement landmarks on a commercial product.

For slope `k=(Rtop-Rbase)/height`, parallel walls of normal thickness `t` require radial separation `t*sqrt(1+k²)`. This is not a general-purpose offset solver. The floor thickness is a separate input. Too-thick walls or floor are rejected.

## Option B — explicit material section

Set `section_rz_mm` to a simple polygon in radius/height coordinates. Use **radii**, not diameters. Closure is implicit; one repeated closing point is allowed. Each point has a non-negative R and Z, up to 1000 mm. Place the part with `position_mm` rather than using negative local Z.

Start at outside axis floor, continue around the outside, rim, inner wall and inner floor, and return to the axis. A profile of only the exterior silhouette does not define a hollow bowl. No automatic thickness is inserted into an explicit section.

The polygon may touch the axis along exactly one edge, or not at all. It must not self-intersect, self-touch or double back. Points are connected with straight lines, not hidden splines.

Allowed `source_status` string values (arrays and objects are invalid):

- `SYNTHETIC_EXAMPLE`
- `USER_DEFINED_NOT_MEASURED`
- `USER_ENTERED_MEASUREMENTS`
- `MANUAL_TRACE_UNVERIFIED`

These record the **asserted input source**, not an independent physical verification. Do not mark photo estimates as measurements.

Optional `color`: three normalized illustrative RGB values. Optional `position_mm`: X/Y/Z translation. There is no auto-fit or auto-scaled lid. Default material is opaque. The example lid is shown above its body to keep the parts visible; its fit is not certified. The CLI permits some meshes larger than the browser viewer's 65,535-vertex-per-part, 150,000-total-vertex and 20 MiB file limits; choose fewer points/segments for interactive preview.

## Photo tracing calibration

The browser takes two axis points and a known height, computes a uniform scale and a rotated R/Z frame, and exports clicked points. It letterboxes photos without stretching. It does not correct perspective or camera distortion. Two canvas pixels snap to the axis/floor, explicitly recorded in exported notes.

For a clearly photographed or measured section, this is a reference aid. For an ordinary product photo, the inside/underside cannot be reliably recovered just by tracing the outer edge. Use another view or supplied dimensions and mark assumptions.

## Geometry and units

Internal meshes / `mesh.json` / OBJ: millimetres, Z-up.
GLB: metres, Y-up, conversion `(x,y,z) -> (x,z,-y)/1000`.
Blender: vertex coordinates in metres, with UI set to display millimetres.

The mesh builder closes the **material boundary** while leaving the container's interior open. It checks surface orientation, edge incidence and zero-area triangles, not material behaviour, fine manufacturing features or lid mating.
