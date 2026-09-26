"""
File Storage Service for CodeVerse LMS
Supports live PostgreSQL queries via DATABASE_URL with graceful fallback.
"""
import logging
from database import execute_query, check_connection

logger = logging.getLogger(__name__)

# Empty — all files come from the live database.
_FILES_DB = []


def is_db_active():
    try:
        ok, _, tables, _ = check_connection()
        return ok and "files" in tables
    except Exception:
        return False


import os
import datetime

def get_disk_storage_bytes():
    """Calculate actual disk storage used in uploads folder."""
    try:
        from flask import current_app
        root = current_app.root_path
    except Exception:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(root, "static", "uploads")
    total_bytes = 0
    if os.path.exists(upload_dir):
        for root_dir, _, filenames in os.walk(upload_dir):
            for f in filenames:
                fp = os.path.join(root_dir, f)
                try:
                    total_bytes += os.path.getsize(fp)
                except Exception:
                    pass
    return total_bytes


def format_storage(total_bytes, quota_gb=50):
    if total_bytes <= 0:
        return "0.0", "MB", "0.0 MB", f"{quota_gb} GB", "0%"
    elif total_bytes < 1024 * 1024:
        val = round(total_bytes / 1024, 1)
        return str(val), "KB", f"{val} KB", f"{quota_gb} GB", "< 0.1%"
    elif total_bytes < 1024 * 1024 * 1024:
        val = round(total_bytes / (1024 * 1024), 1)
        quota_bytes = quota_gb * 1024 * 1024 * 1024
        pct = round((total_bytes / quota_bytes) * 100, 2)
        pct_str = f"{pct}%" if pct >= 0.01 else "< 0.1%"
        return str(val), "MB", f"{val} MB", f"{quota_gb} GB", pct_str
    else:
        val = round(total_bytes / (1024 * 1024 * 1024), 2)
        quota_bytes = quota_gb * 1024 * 1024 * 1024
        pct = round((total_bytes / quota_bytes) * 100, 1)
        return str(val), "GB", f"{val} GB", f"{quota_gb} GB", f"{pct}%"


def get_last_added_text():
    if not is_db_active():
        return "لا توجد ملفات بعد"
    try:
        rows = execute_query("SELECT created_at FROM files ORDER BY created_at DESC LIMIT 1;", fetch=True)
        if rows and rows[0].get("created_at"):
            ca = rows[0]["created_at"]
            now = datetime.datetime.now(datetime.timezone.utc) if getattr(ca, "tzinfo", None) else datetime.datetime.now()
            diff = now - ca
            secs = max(0, int(diff.total_seconds()))
            if secs < 60:
                return "الآن"
            elif secs < 3600:
                mins = max(1, secs // 60)
                return f"قبل {mins} دقيقة"
            elif secs < 86400:
                hrs = secs // 3600
                return f"قبل {hrs} ساعة"
            else:
                days = secs // 86400
                return f"قبل {days} يوم"
    except Exception as e:
        logger.warning(f"Error calculating last added file time: {e}")
    return "لا توجد ملفات بعد"


def get_files_summary():
    """Aggregated file repository metrics with real storage and live stats."""
    disk_bytes = get_disk_storage_bytes()
    used_num, used_unit, used_str, quota_str, pct_str = format_storage(disk_bytes, quota_gb=50)
    last_added = get_last_added_text()

    tracks_count = 2
    files_this_month = 0

    if is_db_active():
        try:
            sql = "SELECT COUNT(*) as total_files, COALESCE(SUM(downloads_count), 0) as downloads FROM files;"
            rows = execute_query(sql, fetch=True)
            total = 0
            downloads = 0
            if rows:
                r = rows[0]
                total = int(r["total_files"] or 0)
                downloads = int(r["downloads"] or 0)

            # Check tracks
            t_rows = execute_query("SELECT COUNT(DISTINCT track) as tc FROM lessons WHERE track IS NOT NULL AND track != '';", fetch=True)
            if t_rows and t_rows[0].get("tc"):
                tracks_count = max(int(t_rows[0]["tc"]), 2)

            # Check files this month
            m_rows = execute_query("SELECT COUNT(*) as mc FROM files WHERE created_at >= date_trunc('month', CURRENT_DATE);", fetch=True)
            if m_rows and m_rows[0].get("mc"):
                files_this_month = int(m_rows[0]["mc"])

            monthly_growth_text = f"+{files_this_month} ملفات هذا الشهر" if files_this_month > 0 else "مستقر هذا الشهر"

            return {
                "total_files": total,
                "storage_used": used_str,
                "storage_used_number": used_num,
                "storage_used_unit": used_unit,
                "storage_total": quota_str,
                "storage_percent": pct_str,
                "student_downloads": f"{downloads:,}",
                "recent_count": total,
                "last_added": last_added,
                "tracks_count": tracks_count,
                "monthly_growth": monthly_growth_text,
                "files_this_month": files_this_month,
            }
        except Exception as e:
            logger.warning(f"Error querying files summary: {e}")

    return {
        "total_files": len(_FILES_DB),
        "storage_used": used_str,
        "storage_used_number": used_num,
        "storage_used_unit": used_unit,
        "storage_total": quota_str,
        "storage_percent": pct_str,
        "student_downloads": "0",
        "recent_count": len(_FILES_DB),
        "last_added": last_added,
        "tracks_count": tracks_count,
        "monthly_growth": "مستقر هذا الشهر",
        "files_this_month": 0,
    }


def get_all_files():
    """Retrieve all library resources."""
    if is_db_active():
        try:
            sql = "SELECT * FROM files ORDER BY id ASC;"
            rows = execute_query(sql, fetch=True)
            if rows is not None:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Error querying all files: {e}")

    return _FILES_DB


def get_lesson_files(lesson_id: int):
    """Return aggregated files for a lesson, reusing the canonical files table."""
    if not lesson_id:
        return []
    if is_db_active():
        try:
            sql = """
                SELECT f.*, lf.display_name, lf.is_primary
                FROM lesson_files lf
                JOIN files f ON f.id = lf.file_id
                WHERE lf.lesson_id = %s
                ORDER BY lf.is_primary DESC, f.name ASC;
            """
            rows = execute_query(sql, (int(lesson_id),), fetch=True)
            if rows:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Error querying lesson files: {e}")
    return []


def attach_file_to_lesson(lesson_id: int, file_id: int, display_name: str = None, is_primary: bool = False):
    """Create a lesson-to-file mapping without duplicating the underlying file row."""
    if not lesson_id or not file_id:
        raise ValueError("معرّف الحصة والملف مطلوبان.")
    if is_db_active():
        try:
            sql = """
                INSERT INTO lesson_files (lesson_id, file_id, display_name, is_primary)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (lesson_id, file_id) DO UPDATE SET display_name = EXCLUDED.display_name, is_primary = EXCLUDED.is_primary
                RETURNING *;
            """
            rows = execute_query(sql, (int(lesson_id), int(file_id), display_name, bool(is_primary)), fetch=True)
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.error(f"Error attaching file to lesson in DB: {e}")
            raise
    return {"lesson_id": int(lesson_id), "file_id": int(file_id), "display_name": display_name, "is_primary": bool(is_primary)}


def create_file(data: dict):
    """Create / upload a new file record."""
    name = (data.get("name") or "").strip()
    if not name:
        raise ValueError("اسم الملف مطلوب.")

    file_name = (data.get("file_name") or name).strip()
    category = data.get("category", "pdf")
    if category not in ("pdf", "zip", "video", "slides", "folder", "code", "doc", "image", "audio", "other"):
        category = "pdf"

    icon_map = {
        "pdf": "picture_as_pdf",
        "zip": "folder_zip",
        "rar": "folder_zip",
        "video": "video_file",
        "slides": "slideshow",
        "doc": "description",
        "code": "code",
        "folder": "folder",
        "image": "image",
        "audio": "audio_file",
        "other": "draft",
    }
    icon = data.get("icon") or icon_map.get(category, "draft")
    size_display = (data.get("size_display") or "2.4 MB").strip()
    description = (data.get("description") or "").strip()
    file_url = (data.get("file_url") or "#").strip()
    updated_at = "اليوم"
    folder_id = data.get("folder_id")
    folder_id = int(folder_id) if folder_id and str(folder_id).isdigit() else None

    if is_db_active():
        try:
            sql = """
                INSERT INTO files (name, file_name, category, icon, size_display, downloads_count, updated_at, description, file_url, folder_id)
                VALUES (%s, %s, %s, %s, %s, 0, %s, %s, %s, %s)
                RETURNING *;
            """
            rows = execute_query(sql, (name, file_name, category, icon, size_display, updated_at, description, file_url, folder_id), fetch=True)
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.error(f"Error creating file in DB: {e}")
            raise

    new_f = {
        "id": max([f["id"] for f in _FILES_DB], default=10) + 1,
        "name": name,
        "file_name": file_name,
        "category": category,
        "icon": icon,
        "size_display": size_display,
        "downloads_count": 0,
        "updated_at": updated_at,
        "description": description,
        "file_url": file_url,
        "folder_id": folder_id,
    }
    _FILES_DB.append(new_f)
    return new_f


def get_folder_by_id(folder_id: int):
    """Retrieve folder by its ID with contained files count."""
    if not folder_id:
        return None
    if is_db_active():
        try:
            sql = """
                SELECT f.*, 
                       (SELECT COUNT(*) FROM files sf WHERE sf.folder_id = f.id) as files_count
                FROM files f
                WHERE f.id = %s AND f.category = 'folder'
                LIMIT 1;
            """
            rows = execute_query(sql, (int(folder_id),), fetch=True)
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.warning(f"Error fetching folder {folder_id}: {e}")
    return None


def get_all_folders():
    """Retrieve all folders with their item counts."""
    if is_db_active():
        try:
            sql = """
                SELECT f.*, 
                       (SELECT COUNT(*) FROM files sf WHERE sf.folder_id = f.id) as files_count
                FROM files f
                WHERE f.category = 'folder'
                ORDER BY f.id DESC;
            """
            rows = execute_query(sql, fetch=True)
            if rows:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Error fetching all folders: {e}")
    return [f for f in _FILES_DB if f.get("category") == "folder"]


def get_root_files():
    """Retrieve top-level items (folders and files not inside any folder)."""
    if is_db_active():
        try:
            sql = """
                SELECT f.*, 
                       CASE WHEN f.category = 'folder' THEN 
                           (SELECT COUNT(*) FROM files sf WHERE sf.folder_id = f.id)
                       ELSE 0 END as files_count
                FROM files f
                WHERE f.folder_id IS NULL
                ORDER BY CASE WHEN f.category = 'folder' THEN 0 ELSE 1 END, f.id DESC;
            """
            rows = execute_query(sql, fetch=True)
            if rows is not None:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Error fetching root files: {e}")
    return [f for f in _FILES_DB if not f.get("folder_id")]


def get_files_by_folder(folder_id: int):
    """Retrieve all files contained inside a specific folder."""
    if not folder_id:
        return []
    if is_db_active():
        try:
            sql = """
                SELECT f.*
                FROM files f
                WHERE f.folder_id = %s
                ORDER BY f.id DESC;
            """
            rows = execute_query(sql, (int(folder_id),), fetch=True)
            if rows is not None:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Error fetching files for folder {folder_id}: {e}")
    return [f for f in _FILES_DB if f.get("folder_id") == int(folder_id)]


def get_available_files_for_folder(folder_id: int):
    """Retrieve files from the library that can be added to this folder."""
    if is_db_active():
        try:
            sql = """
                SELECT f.*
                FROM files f
                WHERE f.category != 'folder' 
                  AND (f.folder_id IS NULL OR f.folder_id != %s)
                ORDER BY f.id DESC;
            """
            rows = execute_query(sql, (int(folder_id),), fetch=True)
            if rows is not None:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Error fetching available files for folder {folder_id}: {e}")
    return [f for f in _FILES_DB if f.get("category") != "folder" and f.get("folder_id") != int(folder_id)]


def attach_files_to_folder(folder_id: int, file_ids: list):
    """Link existing files to a target folder."""
    if not folder_id or not file_ids:
        return 0
    int_ids = [int(fid) for fid in file_ids if str(fid).isdigit()]
    if not int_ids:
        return 0
    if is_db_active():
        try:
            sql = "UPDATE files SET folder_id = %s WHERE id = ANY(%s) AND category != 'folder';"
            execute_query(sql, (int(folder_id), int_ids), fetch=False)
            return len(int_ids)
        except Exception as e:
            logger.error(f"Error attaching files to folder {folder_id}: {e}")
            raise
    return len(int_ids)


def detach_file_from_folder(file_id: int):
    """Detach a file from its current folder (move to root library)."""
    if not file_id:
        return False
    if is_db_active():
        try:
            execute_query("UPDATE files SET folder_id = NULL WHERE id = %s;", (int(file_id),), fetch=False)
            return True
        except Exception as e:
            logger.error(f"Error detaching file {file_id}: {e}")
            raise
    return False


def delete_file(file_id: int):
    """Delete a file from the repository."""
    if not file_id:
        raise ValueError("معرّف الملف مطلوب للحذف.")

    deleted = False
    if is_db_active():
        try:
            execute_query("DELETE FROM files WHERE id = %s;", (int(file_id),), fetch=False)
            deleted = True
        except Exception as e:
            logger.error(f"Error deleting file from DB: {e}")
            raise

    global _FILES_DB
    before = len(_FILES_DB)
    _FILES_DB = [f for f in _FILES_DB if f["id"] != int(file_id)]
    if len(_FILES_DB) < before:
        deleted = True
    return deleted

