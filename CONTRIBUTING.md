# Contributing

Thanks for taking an interest in Unified Student Hub.

If you find a bug or want to improve something, open an issue or send a focused pull request.

## Before you start

Please do not include real student data, private syllabi, passwords, tokens, cookies, or other sensitive information in issues, screenshots, or commits.

## Suggested workflow

1. Open an issue that explains the problem or improvement.
2. Include simple reproduction steps when reporting a bug.
3. Fork the repository and create a branch for the change.
4. Follow the local setup in the root README.
5. Keep the change focused.
6. Add or update tests when behavior changes.
7. Run the checks before opening a pull request.

Backend tests:

```bash
cd backend
python -m pytest -q
```

Frontend build:

```bash
npm run build --prefix frontend
```

For interface changes, include desktop and mobile screenshots using fake sample data.

Please avoid committing local databases, `.env` files, credentials, uploads, dependency folders, or build output.

If a limitation is user visible, document it instead of hiding it behind placeholder behavior.

Contributions are provided under the MIT license. Keep discussions respectful and constructive.
