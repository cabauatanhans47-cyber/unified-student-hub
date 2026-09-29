# Release verification — v0.1

## Passed in the authoring environment

- 15 automated backend tests using FastAPI TestClient and SQLite.
- Frontend production build with Vite.
- Headless Chromium browser journey: register, create deadline, preview TXT syllabus, confirm import, generate a weekly plan, and complete a deadline.
- Desktop (1440 px) and mobile (390 px) rendering inspected from screenshots.
- No uncaught browser errors in that journey; no horizontal overflow at 390 px.

Backend tests cover cross-account task/event isolation, logout revocation, missing request-verification headers, invalid dates/timezones, preview-before-save, deduplication, preservation of completion/effort, oversized/invalid uploads, real text-PDF extraction, transaction rollback, capacity/deadline/busy-time scheduling, partial study blocks, daylight-saving changes, overdue/completed work, ICS all-day handling and recurrence warnings, LMS host validation, and mocked Canvas/Moodle request mapping.

## Not verified here

- Real Canvas or Moodle accounts. Adapters were checked with mocked HTTP responses; institutions differ in enabled endpoints, permissions, and deadline overrides.
- Docker image execution or a running PostgreSQL service. Docker was unavailable in the authoring environment. Local runtime and API checks used SQLite.
- GitHub Actions execution. The workflow is included, but it has not run remotely before publication.
- Load, penetration, independent accessibility, or formal security testing.
- A public hosted deployment. The delivered package is source code with self-hosting configuration.

## Reproduce

With Python 3.12 dependencies installed, run `python -m pytest -q` from the repository root (or inside `backend`). With Node.js 22+, run `npm ci --prefix frontend` and `npm run build --prefix frontend`.

A dependency emits a Starlette TestClient deprecation warning for httpx; it does not affect the passing tests. Recheck the test-client dependency when updating FastAPI/Starlette.

Screenshots use fabricated test-account data. They are examples of the implemented interface, not activity from real students.
