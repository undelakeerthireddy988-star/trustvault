import os, glob
# Delete broken database
if os.path.exists("db.sqlite3"):
    os.remove("db.sqlite3")
    print("Deleted db.sqlite3 - GOOD")
else:
    print("db.sqlite3 already gone")

# Delete all old migrations 0001, 0002...
for f in glob.glob("vault/migrations/000*.py"):
    os.remove(f)
    print("Deleted", f)

print("CLEAN DONE - Now run makemigrations")