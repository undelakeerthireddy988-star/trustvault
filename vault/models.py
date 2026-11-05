from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Role(models.TextChoices):
    ADMIN = "admin", "Administrator"
    OWNER = "owner", "Document owner"
    VIEWER = "viewer", "Viewer"


class Profile(models.Model):
    """Extra data for each login: which role the person has."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.VIEWER)

    def _str_(self):
        return f"{self.user.username} ({self.role})"


class Document(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_documents"
    )
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=60, blank=True)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    data = models.BinaryField()  # the file itself, kept in the database, never on a public URL
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)  # soft delete


class Grant(models.Model):
    class Level(models.TextChoices):
        READ = "read", "Read"
        EDIT = "edit", "Edit"

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="grants")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="grants"
    )
    level = models.CharField(max_length=4, choices=Level.choices)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)  # empty means the grant is active

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document", "user"],
                condition=Q(revoked_at__isnull=True),
                name="one_active_grant_per_user_document",
            )
        ]


class AuditEvent(models.Model):
    """One row per action. Plain ids, not links, so history survives deletions."""
    ts = models.DateTimeField(default=timezone.now)
    actor_id = models.IntegerField(null=True, blank=True)
    actor_name = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=40)
    outcome = models.CharField(max_length=10)  # "allowed" or "denied"
    document_id = models.IntegerField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    detail = models.TextField(blank=True)
    prev_hash = models.CharField(max_length=64)
    hash = models.CharField(max_length=64)