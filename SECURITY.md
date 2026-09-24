# Security and privacy

This release is a local alpha, not a hardened hosted service. Use trusted local files in a separate workspace. Do not expose Python's development HTTP server publicly. Serve `web/` only and bind to 127.0.0.1.

The normal generation and preview paths do not perform network inference, upload user data, invoke arbitrary recipe scripts or depend on account secrets. The site link opens only when the user follows it. The GitHub audit helper parses saved files offline.

Before public release, inspect all tracked files, archives, branches, release attachments and historical revisions for secrets and commercial assets. A private-to-public visibility toggle is NOT the recommended release procedure. Export a reviewed allowlist into a separate clean release repository while retaining required third-party notices.

If a secret has already leaked, revoke or rotate it first; deleting a visible file is not enough. Never put private photos, email credentials, CRM records, customer customizations or certificate originals in an issue or test fixture.

Potential malicious image/mesh files may exhaust a browser even with limits. Do not accept arbitrary `.blend` files, executable code or path-bearing archives from users into an automatic build pipeline.

## Reporting a vulnerability

Report suspected security vulnerabilities through [GitHub private vulnerability reporting](https://github.com/SukiChan0/jr-delipack-modelkit/security/advisories/new).

Include the affected version, impact and minimal reproduction steps using synthetic data. Do not include credentials, private photographs, customer information or commercial models. Do not disclose exploit details in public issues or discussions. If the private reporting form is unavailable, do not post sensitive details publicly.

No fixed response time is currently promised.
