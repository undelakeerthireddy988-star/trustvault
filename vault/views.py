from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.views.decorators.http import require_POST

from .audit import log_event, verify_chain
from .forms import EditForm, GrantForm, UploadForm
from .models import AuditEvent, Document, Grant, Role
from .permissions import can, documents_visible_to, role_of

User = get_user_model()

MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 10


def authenticated(view):
    """Like login_required, but the refusal is also written to the audit log."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            log_event(request, "access", outcome="denied",
                      detail=f"not signed in: {request.method} {request.path}"[:200])
            return redirect(f"{reverse('login')}?{urlencode({'next': request.path})}")
        return view(request, *args, **kwargs)
    return wrapper


def _authorised_document(request, pk, action):
    """Fetch a document ONLY if this user may do `action` on it.
    Missing, deleted and not-granted all look the same (404).
    Refusals are written to the audit log."""
    doc = Document.objects.defer("data").filter(pk=pk).first()
    if doc is None or not can(request.user, doc, action):
        log_event(request, action, document_id=doc.pk if doc else None, outcome="denied")
        raise Http404
    return doc


def _date(value):
    try:
        return parse_date(value) if value else None
    except ValueError:
        return None


# ---------- sign in / out ----------

def _failed_detail(username):
    return f"failed login for '{username.strip().lower()[:50]}'"


def login_view(request):
    if request.user.is_authenticated:
        return redirect("document_list")
    next_url = request.POST.get("next") or request.GET.get("next", "")
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()},
                                           require_https=request.is_secure()):
        next_url = ""
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST":
        username = request.POST.get("username", "")
        recent = AuditEvent.objects.filter(
            action="login", outcome="denied", detail=_failed_detail(username),
            ts__gte=timezone.now() - timedelta(minutes=LOCKOUT_MINUTES),
        ).count()
        if recent >= MAX_FAILED_LOGINS:
            log_event(request, "login", outcome="denied", detail="locked out after too many failed attempts")
            form.add_error(None, "Too many failed attempts. Please wait 10 minutes and try again.")
        elif form.is_valid():
            login(request, form.get_user())
            log_event(request, "login")
            return redirect(next_url or "document_list")
        else:
            log_event(request, "login", outcome="denied", detail=_failed_detail(username))
    return render(request, "vault/login.html", {"form": form, "next": next_url})


@require_POST
def logout_view(request):
    if request.user.is_authenticated:
        log_event(request, "logout")
    logout(request)
    return redirect("login")


def home(request):
    return redirect("document_list")


# ---------- documents ----------

@authenticated
def document_list(request):
    # The list AND the search start from documents_visible_to(), so neither can leak.
    docs = documents_visible_to(request.user)
    filters = {k: request.GET.get(k, "").strip() for k in ("q", "owner", "category", "from", "to")}
    if filters["q"]:
        docs = docs.filter(Q(title__icontains=filters["q"]) | Q(original_name__icontains=filters["q"]))
    if filters["owner"]:
        docs = docs.filter(owner__username__icontains=filters["owner"])
    if filters["category"]:
        docs = docs.filter(category__icontains=filters["category"])
    d_from, d_to = _date(filters["from"]), _date(filters["to"])
    if d_from:
        docs = docs.filter(created_at__date__gte=d_from)
    if d_to:
        docs = docs.filter(created_at__date__lte=d_to)
    docs = docs.select_related("owner").order_by("-created_at")[:200]
    mine = {g.document_id: g.get_level_display()
            for g in Grant.objects.filter(user=request.user, revoked_at__isnull=True)}
    rows = [(d, "Owner" if d.owner_id == request.user.id else mine.get(d.id, "")) for d in docs]
    return render(request, "vault/document_list.html", {"rows": rows, "filters": filters})


@authenticated
def upload(request):
    if role_of(request.user) != Role.OWNER:
        log_event(request, "upload", outcome="denied", detail="role is not owner")
        return HttpResponseForbidden("Only document owners can upload.")
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        f = form.cleaned_data["file"]
        doc = Document.objects.create(
            owner=request.user, title=form.cleaned_data["title"],
            category=form.cleaned_data["category"], original_name=f["name"],
            content_type=f["content_type"], size=f["size"], sha256=f["sha256"], data=f["data"],
        )
        log_event(request, "upload", doc.pk, detail=f"{f['name']} ({f['size']} bytes) sha256={f['sha256'][:12]}")
        messages.success(request, "Document uploaded.")
        return redirect("document_detail", pk=doc.pk)
    return render(request, "vault/form.html",
                  {"form": form, "heading": "Upload a document", "back": reverse("document_list")})


@authenticated
def document_detail(request, pk):
    doc = _authorised_document(request, pk, "view")
    log_event(request, "view", doc.pk)
    is_owner = doc.owner_id == request.user.id
    ctx = {"doc": doc, "is_owner": is_owner, "can_edit": can(request.user, doc, "edit")}
    if is_owner:
        ctx["grants"] = doc.grants.filter(revoked_at__isnull=True).select_related("user")
        ctx["history"] = AuditEvent.objects.filter(document_id=doc.pk).order_by("-id")[:20]
    return render(request, "vault/document_detail.html", ctx)


@authenticated
def download(request, pk):
    doc = _authorised_document(request, pk, "download")
    full = Document.objects.get(pk=doc.pk)
    log_event(request, "download", doc.pk, detail=f"{doc.original_name} sha256={doc.sha256[:12]}")
    response = HttpResponse(bytes(full.data), content_type=doc.content_type)
    response["Content-Disposition"] = f'attachment; filename="{doc.original_name}"'
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response


@authenticated
def edit(request, pk):
    doc = _authorised_document(request, pk, "edit")
    form = EditForm(request.POST or None, request.FILES or None,
                    initial={"title": doc.title, "category": doc.category})
    if request.method == "POST" and form.is_valid():
        changes = []
        if form.cleaned_data["title"] != doc.title:
            doc.title = form.cleaned_data["title"]
            changes.append("title")
        if form.cleaned_data["category"] != doc.category:
            doc.category = form.cleaned_data["category"]
            changes.append("category")
        f = form.cleaned_data["file"]
        if f:
            doc.original_name, doc.content_type = f["name"], f["content_type"]
            doc.size, doc.sha256, doc.data = f["size"], f["sha256"], f["data"]
            changes.append(f"file replaced (sha256={f['sha256'][:12]})")
        doc.save()
        log_event(request, "edit", doc.pk, detail=", ".join(changes) or "no changes")
        messages.success(request, "Saved.")
        return redirect("document_detail", pk=doc.pk)
    return render(request, "vault/form.html",
                  {"form": form, "heading": "Edit document", "back": reverse("document_detail", args=[doc.pk])})


@require_POST
@authenticated
def delete(request, pk):
    doc = _authorised_document(request, pk, "delete")
    doc.deleted_at = timezone.now()
    doc.save(update_fields=["deleted_at"])
    log_event(request, "delete", doc.pk, detail="soft delete")
    messages.success(request, "Document deleted.")
    return redirect("document_list")


@require_POST
@authenticated
def share(request, pk):
    doc = _authorised_document(request, pk, "share")
    form = GrantForm(request.POST)
    if form.is_valid():
        target = User.objects.filter(username=form.cleaned_data["username"], is_active=True).first()
        if target is None or target.id == request.user.id:
            messages.error(request, "Choose another existing user.")
        else:
            level = form.cleaned_data["level"]
            grant = Grant.objects.filter(document=doc, user=target, revoked_at__isnull=True).first()
            if grant:
                grant.level = level
                grant.save(update_fields=["level"])
            else:
                Grant.objects.create(document=doc, user=target, level=level, granted_by=request.user)
            log_event(request, "grant", doc.pk, detail=f"{target.username} -> {level}")
            messages.success(request, f"{target.username} now has {level} access.")
    else:
        messages.error(request, "Enter a username and a level.")
    return redirect("document_detail", pk=doc.pk)


@require_POST
@authenticated
def revoke(request, pk, grant_id):
    doc = _authorised_document(request, pk, "share")
    # document=doc stops someone using a grant id that belongs to another document
    grant = Grant.objects.filter(pk=grant_id, document=doc, revoked_at__isnull=True).select_related("user").first()
    if grant:
        grant.revoked_at = timezone.now()
        grant.save(update_fields=["revoked_at"])
        log_event(request, "revoke", doc.pk, detail=grant.user.username)
        messages.success(request, f"Access removed for {grant.user.username}.")
    return redirect("document_detail", pk=doc.pk)


# ---------- administrator ----------

@authenticated
def audit(request):
    if role_of(request.user) != Role.ADMIN:
        log_event(request, "audit", outcome="denied", detail="not an administrator")
        raise Http404
    f = {k: request.GET.get(k, "").strip() for k in ("user", "action", "outcome", "doc")}
    events = AuditEvent.objects.all()
    if f["user"]:
        events = events.filter(actor_name__icontains=f["user"])
    if f["action"]:
        events = events.filter(action=f["action"])
    if f["outcome"] in ("allowed", "denied"):
        events = events.filter(outcome=f["outcome"])
    if f["doc"].isdigit():
        events = events.filter(document_id=int(f["doc"]))
    chain_ok, bad_id = verify_chain()
    since = timezone.now() - timedelta(hours=24)
    suspicious = (AuditEvent.objects.filter(outcome="denied", ts__gte=since)
                  .exclude(actor_name="").values("actor_name")
                  .annotate(n=Count("id")).filter(n__gte=3).order_by("-n"))
    log_event(request, "audit", detail="viewed the audit log")
    return render(request, "vault/audit.html", {
        "events": events.order_by("-id")[:200], "f": f,
        "chain_ok": chain_ok, "bad_id": bad_id, "suspicious": suspicious,
    })