# Publish a static Listening Box dashboard for free

This keeps the existing Flask dashboard local and publishes a separate static research dashboard with GitHub Pages. The Raspberry Pi is not required.

## What is public

The publishing script exports aggregate counts, candidate-label totals, hourly/daily totals, and summary statistics. It does not export WAV files, local file paths, the SQLite database, or exact coordinates.

The repository is public. Review generated docs/data/dashboard.json and the PDF before committing them. Candidate labels are model outputs, not verified species observations.

## One-time setup on Windows

Open PowerShell in the repository folder:

    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    python -m pip install -r requirements-publish.txt

Make sure your existing SQLite database is at data/listeningbox.db. The existing .gitignore excludes data/; keep it that way.

Generate the public aggregate JSON and printable PDF:

    python publish_static.py

Review docs/data/dashboard.json and docs/reports/listening-box-report.pdf.

Then commit and push:

    git add publish_static.py requirements-publish.txt HOSTING.md docs/
    git commit -m "Add static public research dashboard"
    git push

For later refreshes, run python publish_static.py, inspect the output, then:

    git add docs/data/dashboard.json docs/reports/listening-box-report.pdf
    git commit -m "Update Listening Box research results"
    git push

## Enable GitHub Pages

1. Open the repository on GitHub.
2. Select Settings, then Pages.
3. Under Build and deployment, choose Deploy from a branch.
4. Select branch main.
5. Select folder /docs.
6. Save and wait for deployment.

The public site URL should be:

https://jeanamehta21-bot.github.io/TheListeningBox/

GitHub Pages serves static files. It does not run Flask or Python. Your existing python dashboard.py remains the local Flask dashboard.

## Data refresh workflow

The website changes only when you publish updated files. Run the export script on the Windows computer that has data/listeningbox.db, review the output, and push the generated JSON and PDF.

GitHub Pages is static hosting, not a live database. Do not commit the raw SQLite database, WAV files, credentials, or private coordinates.

## Troubleshooting

- Database not found: put your existing listeningbox.db in the project's data/ folder. Do not commit it.
- PDF import error: activate .venv and install requirements-publish.txt.
- Dashboard shows no data: run python publish_static.py and verify the JSON contains nonzero counts.
- PDF link missing: ensure docs/reports/listening-box-report.pdf was generated and committed.
- 404: verify Pages source is main and /docs, then wait for deployment.
