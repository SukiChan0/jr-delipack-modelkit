# First public release gate

- [ ] Record the exact standalone repository owner/name and proposed visibility in the release approval; verify authenticated permissions and any name conflict. Do not infer a target from the current Git remote or an unrelated repository.
- [ ] Confirm code/assets license choices and third-party compatibility with the owner. Code GPL-3.0-or-later, invented sample data CC0, brand rights separate is the proposed package policy.
- [ ] Review a clean export, tracked file allowlist, dependencies, assets and history. Do not make the production repository public, inherit its Git history, or add this project inside its tree.
- [ ] Exclude private instructions, account/permission records, raw operation logs and local paths. Rebuild the public file manifest from the explicitly approved files; an input archive is not an upload allowlist.
- [ ] Verify the exact remote immediately before an approved write, including push URLs; redact credentials from any report. Do not use the current origin without checking it.
- [ ] Ensure public AGENTS/docs are self-contained and all included evidence links resolve. No production workflows, self-hosted runners, credentials or deployment hooks may be inherited.
- [ ] Rerun unit tests and independent GLB/OBJ import; ideally use the current official glTF validator and record exact version/results.
- [ ] Test real browser flow: reference -> calibration -> material trace -> JSON -> CLI -> mesh import -> view; keyboard/numeric alternative and mobile viewport; inspect requests for unintended uploads. Separate validated export data from actual browser download completion and disclose file-access restrictions.
- [ ] Test optional Blender in a new background process, reopen scene and independently verify units, part separation and editable curves. If not verified, keep it explicitly experimental; do not silently claim support.
- [ ] Include at least two distinct input recipes, including one not hand-tuned by the original author. Separate synthetic and actual measurement evidence.
- [ ] Confirm known failures and exclusions are documented. Model topology/entered dimensions are not real-product accuracy.
- [ ] Establish a genuine private security reporting route; no invented contact channel.
- [ ] Configure contribution review; never auto-merge public contributions into production.
- [ ] Approve exact README website link and metadata. Hosted demo URL remains absent until verified.
- [ ] Preserve unrelated websites, commercial assets, customer systems, credentials, scheduling and external messages untouched.
- [ ] Obtain explicit approval of the final public content, owner/name, visibility and license before create/push/publish.

A local alpha can be delivered before this gate. Do not report `PUBLIC_RELEASE_READY` merely because unit tests pass. Ordinary module failures should not stop unrelated production services.
