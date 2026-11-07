Ways this system could be broken, what I did about each one, and which ones I knowingly accepted and why.

| Threat | What I did | Status |
| :--- | :--- | :--- |
| Server hack - Attacker gets database | Encryption is done in browser with AES-GCM. Server only stores encrypted data. Without password, database is useless. | Fixed |
| Share link guessed - Attacker guesses /share/1, /share/2 | Changed to long random token using secrets.token_urlsafe(32). Link expires after 1 view and after 24 hours. | Fixed |
| Key stolen from localStorage by XSS | Stopped saving key in localStorage. User must enter password every time to decrypt. | Fixed |
| Weak password guessed by brute-force | Used PBKDF2 with 600,000 iterations to derive key from password. Weak passwords still risky if user chooses "12345". | Partially Fixed - Accepted |
| User loses password | No password reset for secrets. If password is lost, secrets cannot be recovered. This is accepted because zero-knowledge means even I cannot recover it. | Knowingly Accepted |
| Render free server sleeps / slow | First load takes time on free tier. No fix yet, accepted for demo. | Knowingly Accepted |
