# Architecture

```text
frontend/src/       React UI: account, deadlines, imports, weekly plan
backend/app/
  main.py          FastAPI routes, session auth, validation, import confirmation
  models.py        SQLAlchemy tables and request-scoped sessions
  importers.py     PDF/TXT extraction and ICS parsing
  lms.py           HTTPS allowlisted Canvas/Moodle adapters
  planner.py       Pure scheduling function; no network/database dependency
backend/tests/     API isolation, import, and planner tests
```

## Data flow

1. A student signs in and receives a random HttpOnly session cookie. The database stores a SHA-256 digest of the token with an expiry. Passwords use Argon2.
2. Account-scoped endpoints filter all tasks and events by the authenticated user ID. The client never chooses that ID.
3. Imports produce unsaved candidates. The student reviews, edits, and removes candidates before the confirmation endpoint applies changes in one transaction.
4. Stable source IDs become per-user deduplication keys. Importing matching items updates dates and titles while retaining task effort/completion.
5. The planner receives tasks, busy intervals, a local start date, timezone, daily time window, and capacity. It iterates UTC slots to avoid DST duplication, rejects past/occupied time, and allocates earliest deadlines first.
6. FastAPI serves the compiled frontend in production. Vite proxies `/api` during frontend development.

## Extend it

- **New importer:** return `{tasks, events, warnings}` matching `TaskInput`/`EventInput`. Supply a stable `external_id`, use timezone-aware timestamps, and add a review screen. Add your source to the source enum. Never save directly from the preview endpoint.
- **Planner changes:** modify the pure `plan_week` function and add invariant tests for no overlaps, capacity limits, deadline limits, and timezone boundaries.
- **New database columns:** introduce a migration tool before changing an installed database. `create_all()` only creates missing tables; it does not migrate them.
- **New integration:** keep credentials transient or design encrypted storage deliberately. Use exact operator-managed host allowlists, HTTPS, disabled redirects, bounded calls, and institution-supported APIs.

## API examples

Interactive schemas: `/docs`. Authentication is cookie-based. Write requests need the verification header:

```bash
curl -c cookies.txt -H 'Content-Type: application/json' \
  -H 'X-Requested-With: StudentHub' \
  -d '{"username":"student","password":"choose-a-unique-long-password"}' \
  http://localhost:8000/api/auth/register

curl -b cookies.txt \
  'http://localhost:8000/api/plan?start=2030-01-01&tz=Asia%2FManila&start_hour=17&end_hour=21&daily_minutes=120'
```

Keep cookie jars and credentials out of source control.

## Source references

- Canvas assignments API: https://developerdocs.instructure.com/services/canvas/resources/assignments
- Moodle calendar API overview: https://moodledev.io/docs/5.0/apis/core/calendar
- Moodle web service function listing: https://docs.moodle.org/dev/Talk:Web_service_API_functions
- A Moodle instance's own **Site administration → Server → Web services → API documentation** is authoritative for that installation's enabled functions.
