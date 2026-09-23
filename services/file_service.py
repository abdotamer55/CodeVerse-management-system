"""
File Storage Service for CodeVerse LMS
Supports live PostgreSQL queries via DATABASE_URL with graceful fallback.
"""
import logging
from database import execute_query, check_connection

logger = logging.getLogger(__name__)

_FILES_DB = [
    {
        "id": 1,
        "name": "مذكرة هياكل البيانات والخوارزميات الشاملة.pdf",
        "file_name": "data-structures-algorithms-guide.pdf",
        "category": "pdf",
        "icon": "picture_as_pdf",
        "size_display": "2.4 MB",
        "downloads_count": 640,
        "updated_at": "14 سبتمبر 2024",
        "description": "مرجع مكتوب باللغة العربية يشمل مفاهيم Big-O، القوائم المرتبطة، والأشجار الثنائية.",
    },
    {
        "id": 2,
        "name": "starter-rest-api-redis.zip",
        "file_name": "starter-rest-api-redis.zip",
        "category": "zip",
        "icon": "folder_zip",
        "size_display": "1.1 MB",
        "downloads_count": 428,
        "updated_at": "12 سبتمبر 2024",
        "description": "كود البداية الجاهز لمشروع بناء خادم REST API مع إعدادات Docker Compose لـ Redis.",
    },
    {
        "id": 3,
        "name": "معمارية الخدمات المصغرة وطوابير RabbitMQ.pdf",
        "file_name": "microservices-rabbitmq-slides.pdf",
        "category": "pdf",
        "icon": "picture_as_pdf",
        "size_display": "4.6 MB",
        "downloads_count": 310,
        "updated_at": "08 سبتمبر 2024",
        "description": "شرائح العرض التقديمي لمعمل البث الحي رقم 14.",
    },
    {
        "id": 4,
        "name": "react19-server-actions-cheatsheet.pdf",
        "file_name": "react19-server-actions-cheatsheet.pdf",
        "category": "pdf",
        "icon": "picture_as_pdf",
        "size_display": "850 KB",
        "downloads_count": 512,
        "updated_at": "05 سبتمبر 2024",
        "description": "ورقة مرجعية سريعة لأهم دوال وهوكس React 19.",
    },
]


def is_db_active():
    try:
        ok, _, tables, _ = check_connection()
        return ok and "files" in tables
    except Exception:
        return False


def get_files_summary():
    """Aggregated file repository metrics."""
    if is_db_active():
        try:
            sql = "SELECT COUNT(*) as total_files, COALESCE(SUM(downloads_count), 0) as downloads FROM files;"
            rows = execute_query(sql, fetch=True)
            if rows:
                r = rows[0]
                return {
                    "total_files": r["total_files"],
                    "storage_used": "4.8",
                    "storage_total": "50 GB",
                    "storage_percent": "9.6%",
                    "student_downloads": f"{r['downloads']:,}",
                    "recent_count": 12,
                }
        except Exception as e:
            logger.warning(f"Error querying files summary: {e}")

    return {
        "total_files": 168,
        "storage_used": "4.8",
        "storage_total": "50 GB",
        "storage_percent": "9.6%",
        "student_downloads": "3,420",
        "recent_count": 12,
    }


def get_all_files():
    """Retrieve all library resources."""
    if is_db_active():
        try:
            sql = "SELECT * FROM files ORDER BY id ASC;"
            rows = execute_query(sql, fetch=True)
            if rows:
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
    if category not in ("pdf", "zip", "video", "slides", "folder", "code", "doc"):
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
    }
    icon = data.get("icon") or icon_map.get(category, "draft")
    size_display = (data.get("size_display") or "2.4 MB").strip()
    description = (data.get("description") or "").strip()
    file_url = (data.get("file_url") or "#").strip()
    updated_at = "اليوم"

    if is_db_active():
        try:
            sql = """
                INSERT INTO files (name, file_name, category, icon, size_display, downloads_count, updated_at, description, file_url)
                VALUES (%s, %s, %s, %s, %s, 0, %s, %s, %s)
                RETURNING *;
            """
            rows = execute_query(sql, (name, file_name, category, icon, size_display, updated_at, description, file_url), fetch=True)
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
    }
    _FILES_DB.append(new_f)
    return new_f


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

