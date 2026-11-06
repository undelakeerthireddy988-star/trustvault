# How I used AI on this project

Tool: Claude (chat) and Meta AI. I run every command and read every piece of code myself. I only record things that really happened.

## Entry 1 - 2 Nov 2026 - .gitignore in the wrong place

Asked: How to move my .gitignore file into the project folder.

Produced: A Move-Item command that assumed the file was in C:\Users\Nivas\Documents.

What was wrong: PowerShell said "Cannot find path ... because it does not exist". The assumption about where the file was had been wrong.

What I did instead: I created the .gitignore directly inside the project folder with Set-Content, then checked on GitHub that venv/ and db.sqlite3 were not uploaded.

Commit: https://github.com/undelakeerthireddy988-star/trustvault/commit/3ab20d1

## Entry 2 - 3 Nov 2026 - Server-side decryption

Asked: How to decrypt the secret on the server and send plain text back to user.

Produced: Claude gave Django view code where browser sends master password to server, server decrypts and returns plain secret.

What was wrong: If server can decrypt, it is not zero-knowledge. If server is hacked, all passwords leak. This broke the main security promise.

What I did instead: I rejected it. I moved encryption fully to browser using AES-GCM. Server only stores encrypted data, never sees password or plain secret.

## Entry 3 - 4 Nov 2026 - Share link bug

Asked: How to make a share link for a secret.

Produced: Claude gave code with /share/1, /share/2 and saved the encryption key in localStorage.

What was wrong: Anyone could guess /share/3 and open others secret. Key in localStorage can be stolen by XSS.

What I did instead: I changed link to use secrets.token_urlsafe(32) for long random token. I stopped saving key in localStorage. Now user must enter password again to decrypt, and link expires after 1 view and 24 hours.
