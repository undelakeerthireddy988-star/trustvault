import hashlib
import os
import re

from django import forms

from .models import Grant

MAX_SIZE = 10 * 1024 * 1024  # 10 MB

# extension -> (content type we will serve, check on the first bytes)
ALLOWED = {
    "pdf": ("application/pdf", lambda b: b.startswith(b"%PDF-")),
    "png": ("image/png", lambda b: b.startswith(b"\x89PNG\r\n\x1a\n")),
    "jpg": ("image/jpeg", lambda b: b.startswith(b"\xff\xd8\xff")),
    "jpeg": ("image/jpeg", lambda b: b.startswith(b"\xff\xd8\xff")),
    "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",
             lambda b: b.startswith(b"PK\x03\x04")),
    "xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
             lambda b: b.startswith(b"PK\x03\x04")),
    "txt": ("text/plain", lambda b: b"\x00" not in b[:1024]),
}


def clean_name(name):
    name = os.path.basename(name.replace("\\", "/"))
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip(" .")
    return name[:255] or "file"


def validate_upload(upload):
    """Checks an uploaded file and returns its details, or raises ValidationError."""
    ext = upload.name.rsplit(".", 1)[-1].lower() if "." in upload.name else ""
    if ext not in ALLOWED:
        raise forms.ValidationError("This file type is not allowed. Use: " + ", ".join(sorted(ALLOWED)) + ".")
    if upload.size == 0:
        raise forms.ValidationError("The file is empty.")
    if upload.size > MAX_SIZE:
        raise forms.ValidationError("The file is larger than 10 MB.")
    data = upload.read()
    content_type, looks_right = ALLOWED[ext]
    if not looks_right(data):
        raise forms.ValidationError("The file content does not match its extension.")
    return {
        "name": clean_name(upload.name),
        "content_type": content_type,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "data": data,
    }


class UploadForm(forms.Form):
    title = forms.CharField(max_length=200)
    category = forms.CharField(max_length=60, required=False)
    file = forms.FileField()

    def clean_file(self):
        return validate_upload(self.cleaned_data["file"])


class EditForm(forms.Form):
    title = forms.CharField(max_length=200)
    category = forms.CharField(max_length=60, required=False)
    file = forms.FileField(required=False, label="Replace file (optional)")

    def clean_file(self):
        upload = self.cleaned_data.get("file")
        return validate_upload(upload) if upload else None


class GrantForm(forms.Form):
    username = forms.CharField(max_length=150)
    level = forms.ChoiceField(choices=Grant.Level.choices)