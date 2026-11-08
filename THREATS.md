
---

### 4. `THREATS.md`

```markdown
# THREATS.md - TrustVault Security Model

## What We Protect
- User passwords, secrets, personal notes
- User accounts / sessions

## Threats & Fixes

| Threat | Fix |
| :--- | :--- |
| Someone opens vault without login | `@login_required` on all vault views |
| Passwords leaked in logs / GitHub | Never log passwords, use env vars, `.gitignore` for `.env` |
| CSRF attack - fake form submit | Django `{% csrf_token %}` on all forms |
| XSS - script in notes field | Django auto-escapes templates, don't use `\|safe` |
| SQL Injection | Use Django ORM only, never raw SQL with user input |
| Session hijack | `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True` in prod |
| Weak SECRET_KEY / DEBUG=True in prod | `SECRET_KEY` from env, `DEBUG=False` on Render |
| Brute force login | Django rate-limit + strong password validators |
| IDOR - user sees others' items | Always filter: `VaultItem.objects.filter(owner=request.user)` |

## Rules
1. Never show other user's data.
2. Never store SECRET_KEY in code.
3. Never set DEBUG=True on Live site.
4. Always filter by `request.user`.