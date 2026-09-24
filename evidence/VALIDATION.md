# Local validation — 0.1.0-alpha.2

Updated 2026-09-24 for JR Delipack ModelKit. These are local synthetic-fixture results, not tests of a production website, real product or published repository. The current run used Windows 11, Python 3.12.14, a Chromium 153 in-app browser and Blender 4.5.14 LTS. This summary deliberately excludes private paths, account checks and raw operational logs.

| Check | Result | Evidence / limitation |
|---|---|---|
| Python core, exports, input rejection and HTML audit tests | PASS — 39/39 | Current suite on Python 3.12.14 / Windows 11; includes malformed numeric and source-status regression handling |
| Web source contracts and reference mathematics | PASS — 10/10 | Node.js v24.19.0, `tests/test_web_contract.mjs`; static checks, separate from real browser acceptance |
| Independent GLB and OBJ readback | PASS — 3 recipes, 6 parts | Current independent readback of distinct synthetic inputs; part structure, units and mesh checks, not physical-product validation |
| Additional CLI input checks | PASS — 16 rejection cases, 2 boundary cases | Separate acceptance checks; not added to the 39-test unit-suite count |
| Bundled synthetic examples | INCLUDED | `../examples/generated/` and `../examples/custom_generated/`; `independent-mesh-check.json` is the original bundled two-fixture report, not a replacement for the current three-recipe result |
| Official Khronos glTF Validator | NOT_RUN | Independent parser readback is not official conformance certification |
| Browser trace-to-mesh path | PASS_WITH_LIMITATIONS | Built-in drawing -> mouse axis calibration / manual trace -> actual exported Blob data -> Python build -> selected mesh-file import -> part selection, keyboard yaw/zoom and drag; download/file-access limits below |
| Native browser download saving | NOT_VERIFIED | The download-event observation timed out after 10 seconds; the actual Blob was inspected and built, but automatic filesystem saving was not confirmed |
| Browser file-access compatibility | LIMITATION_OBSERVED | File metadata was readable but an initial content read failed with `NotReadableError`; selecting a byte-identical copy in a browser-readable temporary location succeeded without permission changes |
| Browser invalid-input handling | PASS for tested cases | Invalid/empty JSON, oversized mesh input, invalid PNG, image byte/pixel-limit rejection and subsequent valid-input recovery were exercised |
| Desktop / emulated mobile layout | PASS for tested viewports | 934 × 794 desktop and 390 × 844 mobile emulation; no horizontal overflow, mobile single-column layout. Not a physical-phone test |
| Keyboard controls | PASS for tested controls | Part selection, yaw, zoom ArrowRight to 1.05 and Enter opening the numeric-alternative details; not a complete assistive-technology audit |
| No-WebGL fallback / context loss | PASS for tested faults | Local fault injection verified unavailable-context fallback; actual `WEBGL_lose_context` produced the expected message, and reload restored the viewer |
| Observed interaction network | PASS for observed window | 20 request events: 17 HTTP GETs, all localhost, plus 3 local blob events. No POST, external-origin or production-resource request observed |
| Blender export and scene reopen | PASS — 31/31 and 18/18 checks | Two different synthetic scenes in Blender 4.5.14 LTS, separate background processes; meshes, units/dimensions and editable source-curve data checked |
| Blender GUI editing | NOT_TESTED | Presence of source-curve data is not an interactive editing acceptance test |
| Other browsers / operating systems / mobile hardware | NOT_TESTED | Current Windows in-app-browser result is not a Safari, Firefox, Android or physical iPhone guarantee |
| User photos / commercial model fidelity | NOT_TESTED | Only synthetic input was generated; no automatic photo reconstruction |
| Existing production code provenance audit | NOT_PERFORMED | This is newly written standalone code, not an extract of production code |
| Search indexing | UNKNOWN | Local software tests do not establish search-engine indexing; public repository availability is a separate publication check |
| Unrelated production changes / external messages | 0 | No deployment, customer-system integration or external sending was performed |

## What the results do and do not prove

Sanitized result records: [core acceptance](core-acceptance.json), [browser acceptance](browser-acceptance.json), and [Blender acceptance](blender-acceptance.json). Reproduce the optional web source checks with `node --test tests/test_web_contract.mjs`; no Node dependency installation is needed.

The geometry core generated independently readable OBJ/GLB files and rejected the covered invalid inputs. Background Blender export and reopen succeeded in the stated environment. Browser interaction, emulated mobile layout, fault fallback and the observed network window passed within their stated scope, but native download saving remains unverified and one local file-access restriction was observed. `PASS_WITH_LIMITATIONS` is not an unqualified native-download end-to-end PASS or proof about untested browsers.

These checks do not prove arbitrary-photo accuracy, constant wall thickness in an arbitrary explicit profile, lid mating, usable capacity, leakage resistance, food safety or manufacturability. The viewer's corrected view-depth and display-colour handling improve visibility, not physical accuracy or transparency simulation. Real photographs and commercial-product accuracy remain NOT_TESTED.

## Counting and release status

The input package previously reported 35 tests in another preparation environment. That is historical package evidence, not an additional 35 tests to add to the current 39/39. The 16 rejection cases, 2 boundary cases and Blender checks have separate scopes; they are not a single consolidated product-certification score.

Publication authorization is separate from these test results. Follow [the public release checklist](../docs/RELEASE_CHECKLIST.md) for subsequent releases and [the security policy](../SECURITY.md) for vulnerability reporting. These tests do not authorize unrelated deployments.

Keep incomplete checks and environment limits visible until new executed evidence changes them. Raw machine/account records are intentionally not required by this public summary.
