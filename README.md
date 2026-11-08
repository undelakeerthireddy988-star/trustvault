# 🔐 TrustVault

Secure personal vault to store passwords, notes & secrets.

**Live:** https://trustvault-xxxx.onrender.com
**Stack:** Django 6.1.2 + PostgreSQL + Gunicorn + WhiteNoise + Render

## Features
- Signup / Login / Logout
- Dashboard with all vault items
- Add / Edit / Delete items
- Search + Copy password
- Secure - login required for all pages

## Run Locally
```bash
git clone https://github.com/undelakeerthireddy988-star/trustvault.git
cd trustvault
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver