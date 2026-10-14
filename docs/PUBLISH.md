# GitHub and hosting

The project source is available at:

https://github.com/cabauatanhans47-cyber/unified-student-hub

## Work on your own copy

```bash
git clone https://github.com/cabauatanhans47-cyber/unified-student-hub.git
cd unified-student-hub
```

Create a branch for your changes, follow the setup in the root README, and run the checks before pushing.

GitHub Actions shows the automated test and build results.

Keep `.env` files, access tokens, local databases, and private student documents out of commits.

## Hosting

GitHub stores the source code, but it does not run the FastAPI backend.

For the current Vercel setup, see [VERCEL.md](VERCEL.md).

For Render and Neon, see [RENDER_NEON.md](RENDER_NEON.md).

For self hosting, see [DEPLOYMENT.md](DEPLOYMENT.md).
