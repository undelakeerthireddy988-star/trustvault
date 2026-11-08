# PROMPTS.md - TrustVault

Prompts used to build this project.

## 1. Project Idea
> Build a secure personal vault web app called TrustVault where users can
> store passwords, notes and secrets safely. Django + PostgreSQL.

## 2. App Structure
> Create Django project `trustvault` and app `vault`.
> Models: Profile, VaultItem (title, username, password, url, notes, created_at)
> Use Django Auth for login/signup.

## 3. UI
> Clean dark UI, dashboard, add/edit/delete vault items, search, copy password button.
> Mobile friendly.

## 4. Security
> - Never store passwords in plain text in logs
> - Use env SECRET_KEY, DEBUG=False in production
> - ALLOWED_HOSTS = ['*'] for Render test, then set real domain
> - CSRF + login required for all vault pages

## 5. Deployment
> Deploy on Render with gunicorn + whitenoise + dj-database-url + psycopg.
> Build: pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
> Start: gunicorn trustvault.wsgi:application