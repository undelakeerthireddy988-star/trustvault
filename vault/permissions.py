"""The ONE place that decides who may do what to a document.

Every view must call can() before it touches a document.
The default answer is NO.
"""
from django.db.models import Q

from .models import Document, Grant, Role


def role_of(user):
    if not user.is_authenticated:
        return None
    profile = getattr(user, "profile", None)
    return profile.role if profile else Role.VIEWER


def active_grant(user, doc):
    return Grant.objects.filter(document=doc, user=user, revoked_at__isnull=True).first()


def can(user, doc, action):
    """action is one of: view, download, edit, delete, share."""
    if not user.is_authenticated or doc is None or doc.deleted_at is not None:
        return False
    if doc.owner_id == user.id:
        return True  # owners can do everything to their own documents
    grant = active_grant(user, doc)
    if grant is None:
        return False  # administrators get NO special access to file contents
    if action in ("view", "download"):
        return True
    if action == "edit":
        return grant.level == Grant.Level.EDIT
    return False  # delete and share: owner only


def documents_visible_to(user):
    """Documents this person may open: their own plus active grants.
    The document list AND the search both start from this, so neither can leak."""
    if not user.is_authenticated:
        return Document.objects.none()
    return (
        Document.objects.filter(deleted_at__isnull=True)
        .filter(Q(owner=user) | Q(grants__user=user, grants__revoked_at__isnull=True))
        .distinct()
        .defer("data")
    )