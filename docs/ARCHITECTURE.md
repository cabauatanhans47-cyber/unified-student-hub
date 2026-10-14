# Architecture

The project is split into a React frontend and a FastAPI backend.

```text
frontend/src/       React interface and offline study features
backend/app/
  main.py           API routes, authentication, validation, and imports
  models.py         SQLAlchemy models and database sessions
  importers.py      PDF, TXT, and ICS parsing
  lms.py            Canvas and Moodle adapters
  planner.py        Weekly scheduling logic
  student_features.py
                    Account, reminder, and scheduling features
backend/tests/      Backend tests
```

## How data moves through the app

1. A student signs in and receives an HttpOnly session cookie.
2. The database stores a SHA 256 digest of that session token with an expiry time.
3. Passwords are hashed with Argon2.
4. API requests use the authenticated account ID from the session. The browser does not choose a user ID.
5. Imports first create a preview. Nothing is saved until the student confirms it.
6. Imported items use stable IDs when possible so repeated imports can update matching records instead of creating duplicates.
7. The planner receives deadlines, busy times, study hours, and daily capacity, then builds a schedule without calling external services.
8. FastAPI serves the built frontend in production. During development, Vite proxies API requests to FastAPI.

## Planner

The planner uses the earliest deadlines first.

It considers:

- remaining task effort
- deadline dates
- busy calendar events
- recurring classes
- the selected timezone
- allowed study hours
- the daily study budget

The planner is deterministic and does not rely on an AI model.

## Extending the project

### Adding an importer

Return `tasks`, `events`, and `warnings` in the same shape used by the existing import flow.

Use stable external IDs when possible and keep timestamps timezone aware.

Preview endpoints should not save data directly.

### Changing the planner

Keep `plan_week` independent from the network and database.

Add tests for overlaps, capacity, deadlines, and timezone behavior when the scheduling logic changes.

### Changing the database

The project currently creates missing tables on startup but does not have a full migration framework.

Do not assume an existing database can be safely changed by editing a model alone.

Add a proper migration path before introducing breaking schema changes.

### Adding integrations

Keep credentials temporary unless encrypted storage is intentionally designed.

Use HTTPS, bounded requests, exact trusted hostnames, and supported institution APIs.

## API examples

Interactive API documentation is available at `/docs`.

Write requests use the verification header shown below.

```bash
curl -c cookies.txt -H 'Content-Type: application/json' \
  -H 'X-Requested-With: StudentHub' \
  -d '{"username":"student","password":"choose-a-unique-long-password"}' \
  http://localhost:8000/api/auth/register

curl -b cookies.txt \
  'http://localhost:8000/api/plan?start=2030-01-01&tz=Asia%2FManila&start_hour=17&end_hour=21&daily_minutes=120'
```

Do not commit cookie files or credentials.

## Useful references

- Canvas assignments API: https://developerdocs.instructure.com/services/canvas/resources/assignments
- Moodle calendar API: https://moodledev.io/docs/5.0/apis/core/calendar
- Moodle web service functions: https://docs.moodle.org/dev/Talk:Web_service_API_functions
