# JR Delipack ModelKit

**Local photo-assisted, profile-driven modelling for round containers and separate lids.**

This alpha converts an explicit material half-section or a simple tapered-bowl recipe into an editable mesh. It includes a small local reference-tracing interface, a lightweight mesh viewer, OBJ/GLB export and an optional Blender scene adapter.

Project background: [JR DELIPACK](https://jrdelipack.com/).

This is a newly written standalone prototype, not an extract of the production JR DELIPACK website. The included objects are invented teaching examples, not R618, R948 or manufacturing drawings. No hosted demo or production deployment is included.

## What actually works in this release

- Python recipe validation and surface-of-revolution mesh generation.
- Explicit inner/outer material boundaries; the cavity remains open.
- A straight tapered-bowl preset with user-supplied normal wall and floor thickness.
- Separate named body/lid meshes and user-defined placement.
- OBJ in millimetres; binary glTF 2.0 in metres with the appropriate axis conversion.
- Repeatable output, finite-number/schema/size limits, and refusal to overwrite output directories.
- A local HTML interface for **manual** image/sketch calibration and tracing, plus mesh inspection. The trace-to-mesh path passed with limitations in a Windows Chromium 153 in-app browser, including an emulated mobile layout; native download completion remains unverified. See [validation evidence](evidence/VALIDATION.md) for the tested path and file-access limitation.
- Optional `.blend` export script, tested with Blender 4.5.14 LTS in separate background export/reopen processes. Blender is not bundled or installed automatically.
- An offline GitHub HTML/header inspection helper. It does not query Google or certify indexing.

## What this is NOT

This is not automatic image-to-3D reconstruction, a photogrammetry system, a universal model generator, a complete section editor, manufacturing CAD or a food-contact compliance checker.

A photograph does not disclose hidden wall thickness or lid retention geometry. Manual tracing does not remove perspective distortion. Numeric fidelity to an input dimension is not measurement accuracy. A closed material mesh does not mean the opening is capped, a lid fits, or a vessel is watertight in real use. Material volume in the report is **not container capacity**.

No automatic segmentation, texture extraction, arbitrary SVG import, snap-fit simulation, AI/cloud calls, physics game or quotation backend is included. Colours are illustrative; the default viewer is opaque and does not reproduce translucent plastic optics.

## Quick start — no third-party Python packages

Use a separate directory and an existing Python 3.10+ installation. The current validation used Python 3.12.14 on Windows 11 and passed 39/39 core tests. Other Python versions and operating systems are not guaranteed by this run.

From the repository root:

```bash
python -m unittest discover -s tests -v
python -m jr_modelkit validate examples/demo_set.json
python -m jr_modelkit build examples/demo_set.json --out build/my-first-set
```

The output directory must not already exist. Choose a new directory for each build; originals are never overwritten.

For a second author-independent invented input, try `examples/independent_synthetic.json`. It is a local audit teaching recipe, not a measured commercial product. Optional web-source regression checks run with `node --test tests/test_web_contract.mjs` on an existing Node installation; they do not install dependencies or replace browser acceptance.

Output:

```text
build/my-first-set/
├── model.glb
├── model.obj
├── mesh.json
├── recipe.resolved.json
└── report.json
```

On Windows, `py -3` may be used instead of `python` when that is the installed launcher. Do not reinstall the environment used by other production tasks.

### Local tracing and viewing

```bash
python -m http.server 8765 --bind 127.0.0.1 --directory web
```

Open `http://127.0.0.1:8765/`. Serve only `web/`, not your home directory or production workspace. This is a local static development server, not a public deployment recipe. Stop with Ctrl+C. Use a different available port if required.

1. Load a side-on photo or simple material-section sketch, or use the invented drawing.
2. Enter the known calibration height, then identify bottom and top points on the axis.
3. Trace the **closed material boundary**, including the inner wall and floor. If those are not visible, supply a measured/drawn section or use the numeric preset. Do not make unsupported measurement claims.
4. Download the recipe. Exporting is not validation.
5. Run `python -m jr_modelkit build PATH_TO_RECIPE.json --out build/another-new-directory`.
6. In the viewer choose the output `mesh.json`. Orbit, select a part and inspect it. Import the GLB or OBJ into your preferred tool for independent inspection.

Images remain in the browser's memory and are not embedded in the downloaded recipe. This is not an automatic metadata-redaction utility: do not publish your originals just because you used this interface.

Some embedded browsers restrict file access or downloads. In the tested browser, a selected file's metadata was readable but reading its contents initially failed with `NotReadableError`; selecting a byte-identical copy from a browser-readable temporary location worked without changing permissions. The recipe export Blob was validated, but automatic saving to the browser's download folder was not verified. Do not treat a displayed export message as proof that a file was saved.

### Optional Blender scene

With an existing Blender installation, in a separate background process:

```bash
blender --background --factory-startup --python blender/export_scene.py -- --recipe examples/demo_set.json --out build/blender-first-set
```

This adds `scene.blend`, including source section curves, in a new output folder. Two different synthetic scenes were exported and reopened in Blender 4.5.14 LTS, with their units, dimensions, separate meshes and source curves checked. Interactive GUI editing and other Blender versions were not tested. This adapter does not render a finished product photograph or modify an existing website.

## Inputs, limits and architecture

Read [input format](docs/INPUT_FORMAT.md), [architecture](docs/ARCHITECTURE.md) and [known limitations](docs/LIMITATIONS.md).

The Python geometry is authoritative. The browser traces points and previews generated meshes; it does not maintain an independent competing geometry solver. Per-part position is an explicit visual transform, not inferred fit.

## Privacy and safety

No account, API key, uploaded photo service, tracking script, telemetry, customer database, email or WordPress adapter is needed. No Blender or model download happens automatically. Existing production assets and automation systems are out of scope.

Do not open untrusted scripts or `.blend` files merely because a third party attached them to an issue. See [SECURITY.md](SECURITY.md).

## Licensing

Code and documentation in this standalone package use **GPL-3.0-or-later**, see [LICENSE](LICENSE); synthetic teaching input and derived meshes in `examples/` use **CC0-1.0**, see [examples/LICENSE.md](examples/LICENSE.md). No commercial product assets, logos, fonts, photographs, HDRIs or sound files are bundled.

The code license allows commercial reuse subject to its terms. It does not require an SEO backlink. User-created output is not automatically made GPL merely by running this tool; input and incorporated asset rights still matter.

JR DELIPACK brand identification is separate from the code license; see [TRADEMARKS.md](TRADEMARKS.md). Review rights and dependency compatibility before importing any existing project code or assets.

## Status and contribution

This is a locally tested **0.1.0-alpha.2** alpha, not a release already proven with external users. Browser acceptance has documented file-access/download limitations; real-photo accuracy, physical fit and engineering performance are unverified. See [validation evidence](evidence/VALIDATION.md), [CONTRIBUTING.md](CONTRIBUTING.md) and [release checklist](docs/RELEASE_CHECKLIST.md). No ranking, domain-rating increase or indexing outcome is promised.
