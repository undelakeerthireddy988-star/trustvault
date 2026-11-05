"""The audit trail: one row per action, chained together with hashes.

If anyone changes or removes an old row, every later hash stops matching,
and verify_chain() reports where.
"""
import datetime
import hashlib
import json

from django.db import connection, transaction
from django.utils import timezone

from .models import AuditEvent

GENESIS = "GENESIS"


def _fields(ts, actor_id, actor_name, action, outcome, document_id, ip, detail):
    return [
        ts.astimezone(datetime.timezone.utc).isoformat(),
        actor_id, actor_name, action, outcome, document_id, ip, detail,
    ]


def _digest(prev_hash, fields):
    body = json.dumps(fields, sort_keys=True, default=str)
    return hashlib.sha256((prev_hash + body).encode()).hexdigest()


def client_ip(request):
    # Render puts the visitor's address in X-Forwarded-For. This header can be
    # forged by a client, so the IP is a hint, not proof (noted in THREATS.md).
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_event(request, action, document_id=None, outcome="allowed", detail=""):
    user = request.user if request.user.is_authenticated else None
    with transaction.atomic():
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(7001)")  # one writer at a time
        last = AuditEvent.objects.order_by("-id").first()
        prev = last.hash if last else GENESIS
        ts = timezone.now()
        actor_id = user.id if user else None
        actor_name = user.get_username() if user else ""
        ip = client_ip(request)
        digest = _digest(
            prev, _fields(ts, actor_id, actor_name, action, outcome, document_id, ip, detail)
        )
        return AuditEvent.objects.create(
            ts=ts, actor_id=actor_id, actor_name=actor_name, action=action,
            outcome=outcome, document_id=document_id, ip=ip, detail=detail,
            prev_hash=prev, hash=digest,
        )


def verify_chain():
    """Returns (True, None) if the log is intact, else (False, id_of_first_bad_row)."""
    prev = GENESIS
    for ev in AuditEvent.objects.order_by("id").iterator():
        fields = _fields(ev.ts, ev.actor_id, ev.actor_name, ev.action,
                         ev.outcome, ev.document_id, ev.ip, ev.detail)
        if ev.prev_hash != prev or ev.hash != _digest(prev, fields):
            return False, ev.id
        prev = ev.hash
    return True, None