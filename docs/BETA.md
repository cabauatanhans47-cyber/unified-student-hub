# Early beta testing

## What works

- Private accounts and the existing deadlines, imports, calendar export, and planner.
- An Overview checklist: add a deadline, save study hours, and review the weekly plan.
- Three removable sample deadlines in the coming week. They are clearly labeled and are private to the signed-in account. Edited sample deadlines are still samples and are removed by the sample cleanup action.
- Account-saved timezone, daily window, and study budget. The current week is selected afresh on each visit.
- Per-account authentication throttling, with regression tests for shared connections.

## Hosting is still required

The original pilot instructions use Render Free and Neon Free. The current hosted beta also has a Vercel setup described in [VERCEL.md](VERCEL.md). Follow [RENDER_NEON.md](RENDER_NEON.md) to create the database and deploy the included Blueprint. Pushing code does not automatically set up a database, domain, or permanent hosting. A provider supplied HTTPS address is sufficient for the pilot; a custom domain can wait.

Use a Docker-compatible web service and durable PostgreSQL. The repository's root `Dockerfile` builds the frontend and serves it with the API, as one application on port 8000. Keep one worker and one replica while authentication counters are stored within each running process. Configure:

| Setting | Value |
| --- | --- |
| App port | `8000` |
| Liveness path | `/api/health` (process health only; test database access separately) |
| `DATABASE_URL` | The provider's private PostgreSQL URL, with the SQLAlchemy `postgresql+psycopg://` driver prefix and provider-required TLS options |
| `COOKIE_SECURE` | `true` |
| `ALLOW_REGISTRATION` | `true` during the invited signup window; then `false` |
| `LMS_ALLOWED_HOSTS` | Empty until a real school hostname has been approved and tested |

Store credentials in the hosting provider's secret settings. Do not commit database URLs or `.env`. Do not use ephemeral SQLite for shared hosting. `/api/health` alone does not establish that accounts can be saved.

## Checks before inviting classmates

1. Verify HTTPS registration, login, logout, deadline creation, sample addition/removal, and weekly planning on the actual hosted URL, including a phone.
2. Save study preferences, reload, sign out and back in, and verify they persist. Restart the hosted app and verify accounts and coursework persist too.
3. Verify an unrelated second account cannot read the first account's tasks or preferences.
4. At the trusted hosting edge, configure authentication/upload rate limits and an approximately 3 MB request-body limit. Account-based throttling alone does not control attempts against many usernames. Trust only the provider's documented client-IP mechanism. Test several students signing in from the same connection.
5. Enable private scheduled database backups. Restore a backup into a separate database, then verify accounts, tasks, events, and study preferences. Do not test restoration by overwriting the live database. Retention, encryption, and restore instructions depend on the chosen provider.
6. Tell testers this is an early beta. Account recovery codes, account deletion, and reminders are available, but background LMS sync and recurring ICS expansion are not. Encourage testers to use sample coursework first. Ask them to use coursework they are comfortable putting in a pilot.

Docker app execution, real Neon connectivity, hosting-edge protection, and a production PostgreSQL restore are still specific to the deployment checks. CI now runs the browser journey against a disposable PostgreSQL 16 database; consult the exact workflow run for its result. The local SQLite upgrade/backup test is not a substitute for them.

## Pilot success criteria

Start with five classmates who want to help. Each should be able to register, add a real deadline, save study hours, and read their plan without a walkthrough. Ask where they got stuck and whether the plan fits their available time. Follow up after a week to ask whether they returned and found it useful. Keep feedback voluntary; no analytics tracking is added by this release.

Fix the confusing steps before inviting a bigger group.
