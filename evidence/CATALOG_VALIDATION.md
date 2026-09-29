# Catalog update validation — 2026-09-30

This additive metadata update was tested on Windows with Python 3.12.14 and
Node.js v24.19.0. No production website, commercial asset or physical sample was
used by these tests. The geometry engine, exporters, existing CLI and browser
application were unchanged.

| Check | Result | Scope |
|---|---|---|
| `python -m unittest discover -s tests -v` | PASS — 51/51 | Existing 39 geometry/export/audit tests plus 12 catalog tests |
| `node --test tests/test_web_contract.mjs` | PASS — 10/10 | Existing browser-source contracts; not a new browser interaction acceptance run |
| RT catalog read and flattened rows | PASS | Three model IDs, entered body/foot/bottom/lid dimensions, invariant shared lid, source status and separate assumptions |
| Mixed round/rectangular families | PASS | Synthetic round fixture and RT metadata retain separate IDs, dimension vocabularies, source labels and lids |
| Catalog rejection and isolation | PASS | Malformed/duplicate/oversized JSON, invalid numerics, unknown shape/dimensions, duplicate/unsafe IDs, wrong lid references, data budgets, controlled CLI errors, independent output copies |
| Legacy recipe boundary | PASS | Catalog is rejected as a geometry recipe; metadata is not silently converted to a rotational mesh |
| Physical dimensions, manufacturing, fit, sealing and compliance | NOT_VERIFIED | Input source assertions and display assumptions do not establish physical performance |
| Website integration or deployment | NOT_PERFORMED | The package returns metadata only |
| New Blender, GLB, OBJ or visual-browser acceptance | NOT_RUN | This update changes no geometry or viewer code and supplies no new meshes |

Test fixtures are synthetic except for the explicitly marked RT numeric catalog.
The catalog tests verify its transcribed values against the documented inputs,
not the accuracy of measurements on real samples. Existing geometry/browser
validation history and limitations remain in [VALIDATION.md](VALIDATION.md).
