# Security

Unified Student Hub is still an early project. It has not gone through an independent security audit and should not be treated as a campus wide production platform yet.

## Reporting a security problem

Do not post passwords, tokens, cookies, private documents, or working exploit details in a public issue.

If GitHub private vulnerability reporting is enabled, use **Security → Report a vulnerability**.

If it is not enabled, contact the maintainer privately before sharing sensitive technical details.

## Current protections

The app currently uses:

- Argon2 password hashing
- random revocable sessions
- per user ownership checks
- request verification headers for writes
- operator controlled LMS hostname allowlists
- database backed throttling for sensitive account actions

LMS tokens are not intentionally saved by the application.

## Hosting safely

Shared deployments should use HTTPS with `COOKIE_SECURE=true`.

Database credentials and other secrets should stay in the hosting provider's secret settings, not in GitHub.

Use backups, reasonable request limits, and trusted outbound network rules where possible.

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for more deployment notes.

## Known limits

The project does not currently have:

- an independent penetration test
- email based password recovery
- campus SSO
- a full schema migration system
- background notification delivery

PDF parsing also runs in the application process.

For an open public deployment, monitor the service and keep dependencies updated.

Recovery codes are stored as SHA 256 digests. A successful password reset revokes server sessions. Offline copies already saved on another device remain on that device until they are cleared there.
