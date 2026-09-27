"""
Supabase Storage Service for CodeVerse LMS
Uploads files to Supabase Storage and returns persistent public URLs.
Works on Vercel (serverless) since it doesn't rely on local filesystem.
"""
import os
import time
import logging
import requests as http_requests

logger = logging.getLogger(__name__)

# ─── Configuration ─────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
BUCKET_NAME = os.environ.get("SUPABASE_STORAGE_BUCKET", "codeverse-files")

# Allowed file extensions (same as config.py ALLOWED_EXTENSIONS)
ALLOWED_EXTENSIONS = {
    "pdf", "zip", "rar", "7z", "tar", "gz",
    "ppt", "pptx", "doc", "docx", "txt", "md",
    "mp4", "mov", "avi", "webm", "mkv",
    "jpg", "jpeg", "jfif", "png", "gif", "webp", "svg",
    "xls", "xlsx",
}

# MIME type mapping
MIME_TYPES = {
    "pdf": "application/pdf",
    "zip": "application/zip",
    "rar": "application/x-rar-compressed",
    "7z": "application/x-7z-compressed",
    "tar": "application/x-tar",
    "gz": "application/gzip",
    "ppt": "application/vnd.ms-powerpoint",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "txt": "text/plain",
    "md": "text/markdown",
    "mp4": "video/mp4",
    "webm": "video/webm",
    "mov": "video/quicktime",
    "avi": "video/x-msvideo",
    "mkv": "video/x-matroska",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "jfif": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
    "svg": "image/svg+xml",
}


def _get_auth_key():
    """Use service role key if available, else fall back to anon key."""
    return SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY


def is_configured():
    """Check if Supabase storage is configured."""
    return bool(SUPABASE_URL and (SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY))


def upload_file(file_storage, subfolder: str = "uploads") -> tuple:
    """
    Upload a Werkzeug FileStorage object to Supabase Storage.

    Returns:
        (public_url: str, size_display: str, original_filename: str, category: str)
        or (None, None, None, None) on failure.
    """
    if not file_storage or not getattr(file_storage, "filename", None):
        return None, None, None, None

    orig_name = file_storage.filename.strip()
    if not orig_name:
        return None, None, None, None

    ext = orig_name.rsplit(".", 1)[-1].lower() if "." in orig_name else ""
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"[Storage] Blocked upload with disallowed extension: {ext!r}")
        return None, None, None, None

    # Build a clean, timestamped filename (no Arabic/special chars in path)
    timestamp = int(time.time())
    raw_stem = orig_name.rsplit(".", 1)[0] if "." in orig_name else orig_name
    # Keep only alphanumeric, hyphens, underscores
    safe_stem = "".join(c for c in raw_stem if c.isalnum() or c in ("-", "_"))[:60] or "file"
    safe_filename = f"{timestamp}_{safe_stem}.{ext}" if ext else f"{timestamp}_{safe_stem}"
    storage_path = f"{subfolder}/{safe_filename}"

    # Read file bytes
    file_storage.seek(0)
    file_bytes = file_storage.read()
    file_size = len(file_bytes)

    if not is_configured():
        logger.error("[Storage] Supabase not configured — cannot upload file.")
        return None, None, orig_name, _ext_to_category(ext)

    mime = MIME_TYPES.get(ext, "application/octet-stream")
    api_key = _get_auth_key()
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{storage_path}"

    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": mime,
        "x-upsert": "false",
    }

    try:
        resp = http_requests.post(upload_url, data=file_bytes, headers=headers, timeout=60)
        if resp.status_code in (200, 201):
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{storage_path}"
            size_display = _format_size(file_size)
            category = _ext_to_category(ext)
            logger.info(f"[Storage] Uploaded {safe_filename} ({size_display}) → {public_url}")
            return public_url, size_display, orig_name, category
        else:
            logger.error(f"[Storage] Upload failed {resp.status_code}: {resp.text[:200]}")
            return None, None, orig_name, _ext_to_category(ext)
    except Exception as e:
        logger.error(f"[Storage] Upload exception: {e}")
        return None, None, orig_name, _ext_to_category(ext)


def delete_file(storage_path: str) -> bool:
    """
    Delete a file from Supabase Storage by its storage path.
    storage_path example: 'uploads/1234567_myfile.pdf'
    """
    if not storage_path or not is_configured():
        return False

    api_key = _get_auth_key()
    delete_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{storage_path}"
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
    }
    try:
        resp = http_requests.delete(delete_url, headers=headers, timeout=15)
        if resp.status_code in (200, 204):
            logger.info(f"[Storage] Deleted {storage_path}")
            return True
        logger.warning(f"[Storage] Delete failed {resp.status_code}: {resp.text[:100]}")
        return False
    except Exception as e:
        logger.error(f"[Storage] Delete exception: {e}")
        return False


def extract_storage_path_from_url(public_url: str) -> str | None:
    """
    Extract the storage path from a Supabase public URL.
    e.g. '.../object/public/codeverse-files/uploads/123_file.pdf'
    → 'uploads/123_file.pdf'
    """
    if not public_url or not BUCKET_NAME:
        return None
    marker = f"/object/public/{BUCKET_NAME}/"
    if marker in public_url:
        return public_url.split(marker, 1)[1]
    return None


def _format_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{max(1, round(size_bytes / 1024))} KB"


def _ext_to_category(ext: str) -> str:
    if ext == "pdf":
        return "pdf"
    if ext in ("zip", "rar", "7z", "tar", "gz"):
        return "zip"
    if ext in ("ppt", "pptx"):
        return "slides"
    if ext in ("mp4", "mov", "avi", "webm", "mkv"):
        return "video"
    if ext in ("doc", "docx", "txt", "md", "xls", "xlsx"):
        return "doc"
    if ext in ("jpg", "jpeg", "jfif", "png", "gif", "webp", "svg"):
        return "image"
    return "other"
