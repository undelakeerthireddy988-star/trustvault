How I used AI on this project. Each entry says what I asked, what the tool produced,
what was wrong with it, and what I did instead.

Tool: Claude (chat). I run every command and read every piece of code myself.
I only record things that really happened.

## Entry 1 - 2 Nov 2026 - .gitignore in the wrong place

**Asked:** How to move my .gitignore file into the project folder.

**Produced:** A Move-Item command that assumed the file was in C:\Users\Nivas\Documents.

**What was wrong:** PowerShell said "Cannot find path ... because it does not exist".
The assumption about where the file was had been wrong.

**What I did instead:** I created the .gitignore directly inside the project folder
with Set-Content, then checked on GitHub that venv/ and db.sqlite3 were not uploaded.

**Commit:** https://github.com/undelakeerthireddy988-star/trustvault/commit/3ab20d1