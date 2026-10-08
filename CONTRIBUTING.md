# Contributing

If you find a bug or want to improve something, open an issue or a focused pull request.

1. Open an issue describing the user problem or bug. Include minimal reproduction steps, expected behavior, and actual behavior. Do not include student data, tokens, or private syllabi.
2. Fork the repository and create a focused branch.
3. Follow the local setup in README.md. Keep code changes narrowly scoped and include meaningful tests for behavior changes.
4. Run `python -m pytest -q` inside `backend`, and `npm run build` inside `frontend`.
5. Open a pull request explaining what changed, why, and how you checked it. For interface changes, include desktop and mobile screenshots with fabricated sample data.

Use the existing module boundaries. Avoid committing databases, `.env`, credentials, uploads, dependency folders, or build output. Document user-visible limitations rather than hiding them behind placeholders.

Areas that still need work: recurring events, per-day study windows, and clearer import feedback.

Contributions are provided under this project's MIT license. Be respectful, constructive, and welcoming in discussions.
