# GitHub and hosting

The source is at https://github.com/cabauatanhans47-cyber/unified-student-hub.

## Work on a copy

```bash
git clone https://github.com/cabauatanhans47-cyber/unified-student-hub.git
cd unified-student-hub
```

Use a branch for changes, follow the setup in the root README, and run the checks before pushing. GitHub Actions has the CI results.

Keep `.env`, access tokens, local databases, and private documents out of commits. Use normal GitHub authentication; don't put tokens in remote URLs.

## Hosting

The GitHub repository holds the source. It does not run the backend. See [Render and Neon](RENDER_NEON.md) for the beta setup, or [deployment notes](DEPLOYMENT.md) for self-hosting.
