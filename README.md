# TrustVault

Secure document sharing where the wrong person cannot read a file, and the record shows who did.

- **Live site:** https://trustvault-96lf.onrender.com
  (free hosting: if it has been idle, the first page can take about a minute to load)
- **Repository:** https://github.com/undelakeerthireddy988-star/trustvault

## Demo logins

Password for every account: `TrustVault-Demo-2026`

| Username | Role | What to try |
|---|---|---|
| owner_demo | Document owner | Upload, share, revoke, delete. Owns "Salary letter" (shared read with viewer_demo) and "Contract draft" |
| owner_two | Document owner | Owns "Customer contract (private)", shared with nobody |
| viewer_demo | Viewer | Can open only "Salary letter". Try `/documents/3/` and you get Not Found |
| viewer_two | Viewer | Has no access to anything |
| admin_demo | Administrator | Audit log, user and role management. Cannot open file contents |

## Permission model (in my own words)

Every document has one owner. The owner can do everything to it. The owner can give a named person **read** or **edit** access, and take it back. Nobody else gets in. Administrators manage users and read the audit log, but get no access to file contents unless a document is shared with them like anyone else.

All decisions are made in one function, `can(user, doc, action)` in `vault/permissions.py`. It answers no unless the user is the owner or has an active grant. Every view that touches a document goes through `_authorised_document()` in `vault/views.py`, which calls it. The list and the search start from `documents_visible_to()`, so they cannot show other people's documents. A document you may not reach looks exactly like one that does not exist (404).

Taking access away works on the very next request, because there are no tokens or shareable links. Every request checks the grant table.

## Audit trail

Uploads, views, downloads, edits, deletions, grants, revokes, sign-ins, sign-outs and every refused attempt (including signed-out requests) are written to `AuditEvent`. The database refuses to update, delete or truncate that table (triggers in the `audit_append_only` migration in `vault/migrations/`). Each row stores a hash of the previous row, and the administrator's audit page checks the whole chain and shows "chain intact" or the first row that was changed.

## Run it on your machine

    git clone https://github.com/undelakeerthireddy988-star/trustvault.git
    cd trustvault
    python -m venv venv
    venv\Scripts\activate          (Mac/Linux: source venv/bin/activate)
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py seed_demo
    python manage.py runserver

Open http://127.0.0.1:8000 and sign in with a demo login above.

Run the automated tests: `python manage.py test`

## Deployment (Render)

- Web service (Python 3), free plan, region Singapore, connected to the GitHub repository.
- Build command: `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate && python manage.py seed_demo`
- Start command: `gunicorn config.wsgi:application`
- Environment variables: `SECRET_KEY`, `DATABASE_URL` (a Render Postgres database), `PYTHON_VERSION`, and optionally `DEMO_PASSWORD`.

## Database

Tables are defined in `vault/models.py` and created by the migrations in `vault/migrations/`:
Profile (role of each user), Document (the file bytes are stored in the database), Grant (per-document read or edit access, with `revoked_at`), AuditEvent (the audit log). `python manage.py seed_demo` creates the demo accounts and sample documents.

## API: who may call what

| Method | Path | Who may call it | If not allowed |
|---|---|---|---|
| GET, POST | `/login/` | Anyone | Five wrong passwords lock that username for 10 minutes |
| POST | `/logout/` | Signed-in users | GET gives 405 |
| GET | `/documents/` | Any signed-in user (shows only own and granted documents) | Redirect to sign in, logged |
| GET, POST | `/documents/upload/` | Owners | 403, logged |
| GET | `/documents/<id>/` | Owner or anyone with an active grant | 404, logged |
| GET | `/documents/<id>/download/` | Owner or anyone with an active grant | 404, logged |
| GET, POST | `/documents/<id>/edit/` | Owner or anyone with an edit grant | 404, logged |
| POST | `/documents/<id>/delete/` | Owner | 404, logged |
| POST | `/documents/<id>/share/` | Owner | 404, logged |
| POST | `/documents/<id>/revoke/<grant_id>/` | Owner | 404, logged |
| GET | `/audit/` | Administrators | 404, logged |
| GET, POST | `/admin/` | Django staff accounts (users and roles only, documents are not registered there) | Redirect to sign in |

## What I chose not to build, and why

Public links, folders, groups, file versions, a restore screen for deleted documents, sharing by e-mail, and an AI suggestion feature. I kept one small permission model so it can be checked line by line.

## How I used AI

Claude (chat) for the plan and most of the code, and Meta AI for some of the later work. Where the AI was wrong is in PROMPTS.md. The known weak spots are in THREATS.md.

## Not finished

Antivirus scanning of uploads, a copy of the audit hashes outside the database, per-IP rate limiting, and no restore screen for deleted documents. The code was written with AI help and I only trust what the tests show.