# Security

This is an initial self-hostable release, not an independently audited campus platform.

Do not post access tokens, passwords, cookies, private documents, or exploit details in public issues. If GitHub private vulnerability reporting is enabled for the repository, use **Security → Report a vulnerability**. Otherwise ask the maintainer for a private reporting channel without posting exploit details.

The app uses Argon2 password hashes, random revocable sessions, per-user ownership checks, request verification headers, and exact operator-controlled LMS hostname allowlists. Tokens are not intentionally persisted; avoid enabling HTTP request-body/debug logging that could capture them.

Serve shared deployments over HTTPS with `COOKIE_SECURE=true`, reverse-proxy body/rate limits, constrained outbound access, and regular database backups. Read `docs/DEPLOYMENT.md` for authentication throttling and hosting controls.

Known limitations: no email-based recovery, no versioned schema migrations, and PDF parsing runs in the application process. Do not open unrestricted public registration on an unmonitored server. Keep dependencies updated and test them before deploying upgrades.

Recovery uses a pre-generated single-use secret stored only as a SHA-256 digest. Reset revokes all server sessions; previously saved offline device copies must be cleared on those devices. Authentication and sensitive-action counters are stored in the database across instances.
