# Release verification — v0.1

## Passed in the authoring environment

- 15 automated backend tests using FastAPI TestClient and SQLite.
- Frontend production build with Vite.
- Headless Chromium browser journey: register, create deadline, preview TXT syllabus, confirm import, generate a weekly plan, and complete a deadline.
- Desktop (1440 px) and mobile (390 px) rendering inspected from screenshots.
- No uncaught browser errors in that journey; no horizontal overflow at 390 px.

Backend tests cover cross-account task/event isolation, logout revocation, missing request-verification headers, invalid dates/timezones, preview-before-save, deduplication, preservation of completion/effort, oversized/invalid uploads, real text-PDF extraction, transaction rollback, capacity/deadline/busy-time scheduling, partial study blocks, daylight-saving changes, overdue/completed work, ICS all-day handling and recurrence warnings, LMS host validation, and mocked Canvas/Moodle request mapping.

## Verified after publication

- GitHub Actions **Test and build** [run 36639017426](https://github.com/cabauatanhans47-cyber/unified-student-hub/actions/runs/36639017426) completed successfully for commit `31af6637f28e7cf0018b06739de6d96a94b022a3` on 2026-09-29 (UTC). The run and job steps were checked through the GitHub API: dependency installation, backend tests, and frontend production build all succeeded. This verifies that published commit; it does not establish Docker/PostgreSQL or live LMS verification.

## Authentication throttle regression checks

- All 20 backend tests passed locally on Python 3.12 after the account-scoped throttle change (the original 15 tests plus five new regressions).
- New checks cover independent students sharing one proxy, case-insensitive account limits shared across registration/login, ignored spoofed forwarding headers, cooldown expiry and `Retry-After`, successful-attempt counting, and concurrent calls.
- The frontend was not changed. Hosting-edge limits, Docker/PostgreSQL execution, and real school integrations still require deployment-specific verification.

## Not verified here

- Real Canvas or Moodle accounts. Adapters were checked with mocked HTTP responses; institutions differ in enabled endpoints, permissions, and deadline overrides.
- Docker image execution or a running PostgreSQL service. Docker was unavailable in the authoring environment. Local runtime and API checks used SQLite.
- Load, penetration, independent accessibility, or formal security testing.
- A public hosted deployment. The delivered package is source code with self-hosting configuration.

## Reproduce

With Python 3.12 dependencies installed, run `python -m pytest -q` from the repository root (or inside `backend`). With Node.js 22+, run `npm ci --prefix frontend` and `npm run build --prefix frontend`.

A dependency emits a Starlette TestClient deprecation warning for httpx; it does not affect the passing tests. Recheck the test-client dependency when updating FastAPI/Starlette.

Screenshots use fabricated test-account data. They are examples of the implemented interface, not activity from real students.

## Student beta preparation

- All 30 backend tests pass locally with Python 3.12. In addition to prior coverage, these verify saved preferences across login sessions, account isolation, invalid preferences, current sample dates, repeat sample addition, preservation of edited samples, safe sample cleanup, and request verification on new writes.
- An additive-schema test starts with the previous SQLite tables and existing account/coursework rows, creates the new preferences table, and confirms that coursework and preferences survive a SQLite backup and restore.
- The frontend production build passes.
- `frontend/tests/beta-smoke.cjs` checks the actual browser flow: signup, three-step onboarding, keyboard sample activation, real deadline creation, saved hours after reload, sample cleanup without deleting coursework, a second account, syllabus import, and completion. It asserts no browser exceptions and no horizontal overflow at 390 px, and captures desktop/mobile screenshots.
- The **Test and build** workflow runs this browser check and uploads screenshots. Consult the workflow run for the exact commit's pass/fail result. Local Chromium could not launch because this authoring environment disallows its required sockets; no local browser pass is claimed for this update.
- Permanent hosting, production PostgreSQL backups/restores, provider-edge abuse protection, and live school integrations remain unverified and unconfigured. See [beta launch gates](BETA.md).
