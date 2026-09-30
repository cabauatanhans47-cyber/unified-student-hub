# Offline study workspace

On a personal device, sign in while connected and choose **Enable offline access**. Wait until **Offline access enabled** appears before disconnecting. The app downloads its shell, PDF engine, deadlines, calendar commitments, and preferences. Browser installation is optional: use **Install app** when offered, or the browser's Add to Home Screen menu. HTTPS (or localhost for development) is required. Use a recent browser with IndexedDB, service workers, and Web Locks.

## What works offline

- Reopen this same site/browser, view and create/edit/complete/delete deadlines, export ICS, adjust study preferences, and rebuild the seven-day plan.
- Open materials already added on this device; add new local files, read PDFs, highlight areas, draw, write separate review notes, and download originals or annotated PDFs.
- Run a focus timer with 1–180 study minutes, 1–60 rest minutes, and 1–12 cycles. Rest runs between cycles, with no rest after the final study cycle. Pause/resume/reset and refresh recovery are supported. Use one timer tab at a time. A sleeping/closed browser cannot guarantee sounds; reopening catches up from elapsed wall-clock time.

First-time sign-in, registration, syllabus/calendar/LMS imports, and calendar commitment removal require internet. There is no offline account registration or offline import parsing for deadlines. Materials are separate from syllabus deadline imports.

## Files and annotations

Files are **device-only**, keyed to the signed-in username. They are not uploaded to Render, Neon, or an external document viewer and do not synchronize between devices. PDF highlighting is area-based, with freehand drawing; it does not rewrite original PDF text. Export creates a flattened annotated copy. Encrypted/corrupt PDFs may not open or export. Notes download as TXT separately.

Supported: PDF, PPTX/PPT, DOCX/DOC, XLSX/XLS, TXT, MD, CSV, PNG, JPG/JPEG, WEBP. Modern Office documents have text previews, not original formatting, slide animations, or editable Office layouts. Legacy Office files are stored and downloaded for another app to open. Office previews are limited to 10 MB compressed/15 MB selected XML, text previews to 2 MB. All files have a 25 MB individual limit. Spreadsheet previews use stored cell values, not recalculated formulas. PDFs have visual canvas previews rather than an accessible PDF text layer; use the original in a screen-reader-compatible reader when needed.

Use **Download materials backup** to save originals, notes, and annotations together. Restore adds new copies to the current account/device. Combined originals over 100 MB require individual downloads instead; restore accepts backups up to 150 MB and 100 entries. Browser quota/eviction or clearing site data can remove local work. Keep backups outside the browser. Storage is not encrypted by this app. Avoid shared browser profiles; sign-out removes automatic offline account reopening but retained device files are not a security boundary against another person with access to browser storage.

## Reconnection and conflicts

Deadline and preference changes are durably queued before sending. Reconnect or select **Sync now**. Each write has an account-bound UUID and a server receipt, so retries after a lost response do not create duplicates. A conflict with changed/deleted server data stops the queue and keeps local edits. Download **pending changes backup**, then discard pending changes to reload server data and manually reapply intended edits. This JSON backup is for recovery/reference, not an automatic restore input. Do not clear site data with pending changes.

An offline sign-out also queues server-session revocation before the next online session check. A session that expires while offline must be signed in again online to sync. No authenticated API responses are stored in the service-worker cache; per-account snapshots are stored in IndexedDB only after opt-in. Service-worker asset caches contain public app files only.

## Deployment

No paid service or file-storage provider is added. Build with `npm ci && npm run build` in frontend. The build creates the service worker and local PDF fonts/maps. FastAPI serves the manifest and service worker at the origin root. The backend adds the `sync_receipts` table via the existing startup `create_all`; no existing table columns change. Receipts are retained for retry safety; database owners should account for their growth. Schema migrations, cloud material storage, collaborative editing, OCR, notification delivery, and background LMS sync are future work.
