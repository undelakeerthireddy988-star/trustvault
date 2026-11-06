import hashlib
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from vault.models import Document, Grant, Profile, Role


class Command(BaseCommand):
    help = "Create demo accounts and sample documents. Safe to run many times."

    def handle(self, *args, **options):
        User = get_user_model()
        password = os.environ.get("DEMO_PASSWORD", "TrustVault-Demo-2026")

        def make_user(username, role, staff=False):
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(password)
                user.is_staff = staff
                user.is_superuser = staff
                user.save()
            Profile.objects.update_or_create(user=user, defaults={"role": role})
            return user

        make_user("admin_demo", Role.ADMIN, staff=True)
        owner1 = make_user("owner_demo", Role.OWNER)
        owner2 = make_user("owner_two", Role.OWNER)
        viewer1 = make_user("viewer_demo", Role.VIEWER)
        make_user("viewer_two", Role.VIEWER)

        def make_doc(owner, title, category, filename, text):
            data = text.encode()
            doc, _ = Document.objects.get_or_create(
                owner=owner, title=title,
                defaults={
                    "category": category, "original_name": filename,
                    "content_type": "text/plain", "size": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(), "data": data,
                },
            )
            return doc

        salary = make_doc(owner1, "Salary letter", "HR", "salary-letter.txt", "Demo salary letter. Not real data.\n")
        make_doc(owner1, "Contract draft", "Legal", "contract-draft.txt", "Demo contract draft. Not real data.\n")
        make_doc(owner2, "Customer contract (private)", "Legal", "customer-contract.txt", "Demo private contract. Not real data.\n")

        if not Grant.objects.filter(document=salary, user=viewer1, revoked_at__isnull=True).exists():
            Grant.objects.create(document=salary, user=viewer1, level=Grant.Level.READ, granted_by=owner1)
        self.stdout.write(self.style.SUCCESS("Demo data ready."))