# Publish this project on GitHub

Recommended repository name: `unified-student-hub`.

## Have ChatGPT upload it

1. Create a new **Public** repository on your GitHub account.
2. Name it **unified-student-hub** and initialize it with a README.
3. Send its repository URL back in the conversation. The GitHub connector used to prepare this project can edit repositories, but could not create a new repository.

The package is ready for upload. No existing project needs to be changed.

## Upload it yourself with Git

Extract the ZIP and open a terminal inside the `unified-student-hub` directory. Create a new empty public GitHub repository **without** a README for this command-line path.

```bash
git init -b main
git add .
git commit -m "Add Unified Student Hub initial release"
git remote add origin https://github.com/YOUR_USERNAME/unified-student-hub.git
git push -u origin main
```

Replace `YOUR_USERNAME`. Authenticate using your normal GitHub Git sign-in flow. Never put a personal access token into files, README text, or a remote URL.

The repository includes a license and CI workflow. After pushing, check the **Actions** tab. Add a description such as “Open-source student deadlines, syllabus imports, and workload-aware weekly planning.” Optional repository topics: `education`, `student-planner`, `fastapi`, `react`, `self-hosted`.

For a shared running app, follow DEPLOYMENT.md. GitHub publication by itself does not create a hosted backend.
