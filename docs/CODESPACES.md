# Run the Student Hub in GitHub Codespaces

1. Open the project repository on GitHub.
2. Select **Code → Codespaces → Create codespace on main**.
3. Wait for the development container to finish installing. It creates `.venv`, installs the Python packages, installs frontend packages, and builds the UI.
4. In the Codespaces terminal, run:

   ```bash
   source .venv/bin/activate
   cd backend
   COOKIE_SECURE=true uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

5. Open the **Ports** panel, find **8000**, and click **Open in Browser**. Keep the port private for personal development.
6. Create your Student Hub account. You can now add deadlines, import the sample syllabus, and plan your week.

If the initial setup command failed, run these from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
npm ci --prefix frontend
npm run build --prefix frontend
```

## Enable a school integration

Stop the server with Ctrl+C, then restart with the approved hostnames:

```bash
LMS_ALLOWED_HOSTS=your-school.instructure.com COOKIE_SECURE=true uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Use the actual hostname your school provides. Never paste your token into committed files. Paste it into the Imports screen only.

## Save code changes

Use the Source Control panel or normal Git commands to commit your source edits. The database, passwords, `.env`, and uploaded study material must not be committed. `.gitignore` excludes the local database and environment files.

Codespaces is a development environment that can stop or be deleted. It is not durable public hosting. Your SQLite data stays in that codespace and is lost if you delete it. Export deadlines before deleting a workspace; ICS exports do not contain accounts or study history.

## Update an existing Codespace for the beta features

Stop the server with Ctrl+C. With the virtual environment active, run:

```bash
cd /workspaces/unified-student-hub
# Back up your existing local database before the first upgraded startup.
# Run only if backend/hub.db exists; keep this backup private.
cp backend/hub.db /tmp/student-hub-before-beta.db
git pull --ff-only
npm ci --prefix frontend
npm run build --prefix frontend
cd backend
COOKIE_SECURE=true uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If `git pull` reports local changes, stop and preserve them before merging; do not reset or delete your work. This update adds a `study_preferences` table at startup and does not alter existing account, deadline, event, or session columns. Existing users can keep their accounts. A temporary backup is useful for this update but is not a durable off-device backup.
