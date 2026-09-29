# Free beta setup: Render + Neon

The root `render.yaml` creates one Free Docker web service in Singapore. It does not create a Render database or a paid resource. It enables secure cookies and waits for passing CI checks before automatic deployments. It prompts for `DATABASE_URL` privately during Blueprint setup.

## 1. Create the Neon database

1. In the Neon dashboard, create a project named `unified-student-hub` on the Free plan.
2. Select AWS and the Singapore (`ap-southeast-1`) region to match the web service. Keep the default PostgreSQL version and database name unless you have a reason to change them.
3. Open **Connect** and copy the PostgreSQL connection string. Copy only the URL beginning `postgresql://`, not a `psql` command or shell quotes. Keep its TLS query parameters (such as `sslmode=require`).
4. Keep this string private. Paste it only into Render's secret environment-variable field, never into an issue, commit, screenshot, or chat.

The app automatically selects its installed psycopg 3 driver for standard `postgresql://` and legacy `postgres://` URLs. Pool pre-ping replaces stale connections when they are checked out; it is not a periodic keepalive and does not prevent either provider from sleeping.

## 2. Deploy on Render

1. In the Render dashboard, select **New → Blueprint**.
2. Connect GitHub if needed, allowing access to `cabauatanhans47-cyber/unified-student-hub`.
3. Select that repository and the `main` branch. Use the root `render.yaml`.
4. Name the Blueprint `unified-student-hub`. When prompted for `DATABASE_URL`, paste the private Neon URL.
5. Review the proposed resources: exactly one **Free** web service in **Singapore**, with no Render Postgres database or persistent disk. Stop if the dashboard proposes a charge.
6. Create/deploy the Blueprint. Wait for the service to become **Live**, then open its `https://…onrender.com` address.

The Dockerfile already builds the React frontend and runs FastAPI on port 8000. Do not set a separate static-site publish directory or add another frontend service. `COOKIE_SECURE=true` is already configured. LMS imports remain disabled until approved hostnames are configured.

## 3. Verify the real deployment

The Neon database starts empty. Codespaces accounts and deadlines are not automatically copied. Create a new account on the hosted app, then:

- Add sample deadlines, save study hours, and open the weekly plan.
- Add a real test deadline, then remove samples and confirm the real task stays.
- Reload and sign out/in; verify preferences and coursework remain.
- Restart the web service and repeat the checks. Use a second account to verify separation.
- Before inviting classmates, test a private PostgreSQL backup and restore into a separate database, and resolve the hosting-edge abuse-protection items in [BETA.md](BETA.md). Those are not automatically provisioned by this Blueprint.

During the small invited signup window registration is enabled. After the testers register, change `ALLOW_REGISTRATION` to `false` in `render.yaml` and commit it, so future Blueprint syncs preserve that choice. Existing users can still sign in.

## Limits and troubleshooting

- Render Free sleeps after 15 minutes without incoming traffic and can take about a minute to wake. The public address stays the same, but this is not an always-on service or an uptime guarantee.
- Render's local filesystem is temporary. All shared account/coursework data must use Neon, not SQLite.
- Render Free Postgres expires after 30 days; this setup deliberately uses Neon instead. Neon Free has compute/storage allowances; monitor both providers' usage and remain on Free plans.
- If database startup fails, check the Render `DATABASE_URL` value, Neon project status, and TLS parameters. Do not print the full connection string into logs when debugging.
- `/api/health` confirms the process is running; registration and persistence checks verify database access.
- Docker execution, actual Neon TLS connectivity, production restore, and host-edge controls must be verified on the deployed service. CI's PostgreSQL browser journey runs against a disposable PostgreSQL 16 instance, not the user's Neon account.

Official references: [Render Blueprint fields](https://render.com/docs/blueprint-spec), [Render Free limits](https://render.com/docs/free), [Neon regions](https://neon.com/docs/introduction/regions), [Neon connections](https://neon.com/docs/connect/connect-intro).
