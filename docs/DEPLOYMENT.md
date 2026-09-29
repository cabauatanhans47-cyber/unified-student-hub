# Self-hosting and shared deployments

## Supported starting point

Use `compose.yaml` for a single app process and PostgreSQL on one host. The app port is bound to loopback by default. Place a reverse proxy on that host in front of `127.0.0.1:8000` for public access.

1. Generate a unique hexadecimal database password in `.env`.
2. Configure HTTPS at the reverse proxy with a certificate for your domain.
3. Set `COOKIE_SECURE=true` so session cookies are sent only over HTTPS.
4. Set exact trusted `LMS_ALLOWED_HOSTS` if you need LMS import. Never allow arbitrary user-provided hosts, metadata services, or internal management endpoints. Use outbound network restrictions in a shared deployment.
5. Limit request bodies at the proxy to approximately 3 MB and apply per-client request/rate limits to authentication and upload paths. The app limits parsed files to 2 MB and 50 PDF pages; parsing untrusted PDFs still consumes resources.
6. Keep one app worker for this release. Its authentication throttle allows 20 attempts per normalized username in a rolling five-minute window, shared across login and registration. Students behind a proxy or campus NAT do not share this account allowance. Successful and unsuccessful attempts both count; a 429 response includes `Retry-After`. The app does not use forwarding headers for this limit. Counters are in memory and reset on restart. Before using multiple workers or replicas, move counters to a shared rate-limit store. Account throttling does not stop attempts spread across many usernames: retain aggregate/per-client rate limits at the trusted reverse proxy or hosting edge, using only that provider's verified client-IP mechanism. Do not trust arbitrary `X-Forwarded-For` headers.
7. After desired users register, set `ALLOW_REGISTRATION=false` to close registration, then recreate the app container.
8. Back up PostgreSQL and test restore before relying on it.

The app is intended to run same-origin: frontend and `/api` on the same domain. Do not add wildcard credentialed CORS. API writes require `X-Requested-With: StudentHub`; session cookies are HttpOnly and SameSite=Lax. The app does not trust forwarded headers for URL-based security decisions.

## Backups

Example using a terminal on the Docker host:

```bash
docker compose exec -T db pg_dump -U studenthub -d studenthub > studenthub-backup.sql
```

Backups contain sensitive student/account data. Store them outside the public repository and restrict access. Restore into an empty database:

```bash
docker compose exec -T db psql -U studenthub -d studenthub < studenthub-backup.sql
```

For local SQLite, stop the app before copying `backend/hub.db`. An ICS export is only a deadlines export, not a full backup.

## Upgrades

The schema is created on startup. The beta onboarding update adds only the missing `study_preferences` table, without altering existing tables. This additive upgrade was tested against an existing SQLite database; back up PostgreSQL and validate the upgrade on a restored copy before a hosted rollout. There is no migration framework yet. Do not assume future schema changes can be applied by simply rebuilding a container. Back up first and review each release's migration instructions.

## What this deployment does not provide

No institutional compliance assessment, automated password recovery, campus SSO, distributed rate limiting, background sync, or high-availability architecture. Docker/PostgreSQL definitions are supplied, but were not executed in the authoring environment because no Docker daemon was available. Validate them on your own host before inviting others.

GitHub stores and distributes the code; a running server is separately required for a public app URL. Never turn an unrelated existing repository public to publish this project.
