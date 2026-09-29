# Display catalog — separate from geometry recipes

`jr_modelkit.catalog` validates metadata shared by round and rectangular product
families. It does not build rectangular meshes, load website assets, infer lid fit
or deploy a viewer. The geometry CLI and its `schema_version: 1` input are unchanged.

```bash
python -m jr_modelkit.catalog data/rt_series_dimensions.json
```

```python
from jr_modelkit.catalog import load_catalog, display_rows
rows = display_rows(load_catalog("data/rt_series_dimensions.json"))
# Each row has family_id, shape, model_id, body_dimensions_mm, shared_lid,
# units, source_status, source_note, verification_scope and display_assumptions.
```

Each body references the family's single `shared_lid.id`. The reader repeats its
dimensions without scaling them when producing display rows. A website can map
those stable IDs to its separately managed assets and use one set of controls.
This package does not include that website integration or commercial assets.

## Version 1 contract

Required root fields: `catalog_schema_version: 1`, `units: "mm"`, and `families`.
There must be 1–32 families and 1–64 models in each family. Input files are limited
to 256,000 bytes. Repeated JSON keys and unknown fields are rejected.

Each family requires `id`, `shape` (`round` or `rectangular`), `source_status`,
`source_note`, `verification_scope`, `shared_lid`, `models`, and `display_assumptions`.
The `verification_scope` is always
`INPUT_DATA_ONLY_PHYSICAL_ACCURACY_NOT_VERIFIED`. `source_status` uses the same four
asserted-input labels as [geometry recipes](INPUT_FORMAT.md). Text is limited to
1,000 characters per note/description.

All family, lid, body and assumption IDs must be globally unique. IDs start with
an ASCII letter, followed by at most 47 ASCII letters, digits, `_` or `-`. They are
labels, never file paths or URLs. A shared lid has `id` and `dimensions_mm`. A model
has `id`, `shared_lid_id` (its family lid), and `dimensions_mm`.

| Shape / part | Required dimensions | Optional dimensions |
|---|---|---|
| Rectangular body | `top_length_mm`, `top_width_mm`, `height_mm` | `cavity_depth_mm`, `foot_length_mm`, `foot_width_mm`, `bottom_panel_length_mm`, `bottom_panel_width_mm` |
| Rectangular lid | `length_mm`, `width_mm`, `height_mm` | `platform_length_mm`, `platform_width_mm` |
| Round body | `top_diameter_mm`, `height_mm` | `base_diameter_mm`, `cavity_depth_mm` |
| Round lid | `diameter_mm`, `height_mm` | None |

Dimensions must be finite numbers from 0.05 through 2,000 mm; booleans are invalid.
Cavity depth, when present, must be smaller than body height. This is a limited
consistency check, not a geometry solver. Length/width describe outer envelopes;
cavity depth is measured from the top rim. No capacity is inferred.

`display_assumptions` contains 0–32 entries, each with `id`, `description`, and an
optional finite `value_mm` from 0 through 2,000. They remain separate from the
owner-supplied dimensions in every display row. Text is returned as plain data;
frontends should render it as text, not HTML.

## Included RT data

RT68/78/88 share the 218 × 149 mm upper envelope and a 220 × 151 × 20 mm lid.
Their body heights are 39/45/53 mm and cavity depths 37/43/51 mm. The owner supplied
these values; this repository validates transcription structure and preserves the
distinction between those inputs and display assumptions. It does not independently
verify real specimens, fit, wall thickness, food contact or production tolerances.

The 1 mm central floor thickness and 0.3 mm per-side display clearance are explicitly
assumptions. Height minus cavity depth is a datum relationship, not floor thickness
or outer recess depth. Commercial meshes, raw reference photos and private records
are excluded. See [data license scope](../data/LICENSE.md).
