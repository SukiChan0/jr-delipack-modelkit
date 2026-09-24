# Clean public export rules

An input archive or local working directory is not a blanket authorization to upload every file. Public release requires a reviewed, explicit file list and separate approval.

Prepare the public snapshot in a clean directory outside production repositories. Select approved code, synthetic examples, web assets, license/provenance files and public documentation by an explicit allowlist. Preserve relevant third-party attribution.

Always exclude:

- private execution instructions and local account, path or permission records
- raw operation logs, browser traces and unreviewed screenshots
- original .git history, production workflows/logs/artifacts and deployment configurations
- private photos, commercial models, customer data, credentials and unreviewed generated files

Generate FILE_MANIFEST.json from the final approved public files rather than copying an earlier working manifest. Scan the exported snapshot and staged diff, not only .gitignore. Review README/AGENTS/docs so the public project remains usable without the excluded files and every evidence claim has an accurate, sanitized source.

Record the exact target repository, owner, visibility and licence scope in the release approval; keep private operational records out of the public snapshot. Check actual target existence and permissions through an authorized account immediately before any approved remote write. No repository creation, push, visibility change, Pages or production deployment is authorized by this file.

No frontend, build, example or test may depend on private instructions, credentials or production access. Documentation rules are not automatic Git or network enforcement.
