# Deploy Student Hub on Vercel

Use the repository root, not the frontend folder. Vercel serves the built frontend from public/ and routes the API to the root FastAPI app.py entrypoint.

1. Import cabauatanhans47-cyber/unified-student-hub at https://vercel.com/new.
2. Keep Root Directory at the repository root. Use the FastAPI framework preset. The checked-in vercel.json supplies the build command.
3. Connect a PostgreSQL database, such as Neon through Vercel Marketplace, or use your existing PostgreSQL service. Add its connection string as DATABASE_URL in the project's environment settings. Use the provider's pooled connection string and required SSL settings. If an integration supplies a differently named variable, map it to DATABASE_URL.
4. Set COOKIE_SECURE=true. Configure production and preview database variables separately; use a separate database for previews to avoid changing production records.
5. Deploy. Check /api/health, register a test account, add a deadline, refresh, and verify the deadline persists. Try Weekly plan and Account settings.

No database credentials belong in GitHub or frontend variables. Vercel's ephemeral filesystem cannot store student accounts. The API intentionally returns 503 until PostgreSQL is configured on Vercel. Local development still supports SQLite.

Initial startup creates missing tables under a PostgreSQL advisory lock. Existing tables are preserved. This is additive schema setup, not a general migration system. Configure database backups with the database provider before inviting users.

## What students get

Weekly plan supports different availability for each weekday and recurring classes within semester dates. These are manual commitments; imported ICS RRULE expansion is not implemented. Advanced settings require a connection to save, and are cached for offline planning when offline access synchronizes.

Account settings include optional deadline reminders, account JSON export, account deletion, and a one-use password recovery code. Generate and save the code before losing your password. Password reset revokes server sessions. Offline copies already saved on other devices remain available until cleared there.

Reminders run while the app is open; browser notifications need permission. They are not background push notifications. Deadline ICS exports add calendar alarms when reminders are enabled.

Materials and PDF annotations remain on each device. Use Materials backup separately from the account export. Account export does not yet have a restore workflow. Logging study minutes reduces estimated remaining effort; it is not a study-history ledger.

## Verification

Run backend pytest, frontend unit tests and build, and all three browser smoke scripts in frontend/tests against a running server. GitHub Actions also exercises browser flows with PostgreSQL.

Deployment is only complete after Vercel reports success and the live URL passes the persistence check above. The presence of this configuration alone does not mean a live deployment exists.
