"""
Notification Service for CodeVerse LMS
Supports live PostgreSQL queries via DATABASE_URL with graceful fallback.
"""
import logging
from database import execute_query, check_connection

logger = logging.getLogger(__name__)

_NOTIFICATIONS_DB = [
    {
        "id": 1,
        "title": "تذكير أكاديمي: موعد الاختبار النصفي لهياكل البيانات والخوارزميات",
        "content": "أُرسل إلى جميع طلاب مسار هندسة برمجيات الأنظمة (348 طالباً) · اليوم 11:20 ص",
        "type": "exam",
        "icon": "campaign",
        "is_read": False,
        "created_at": "اليوم 11:20 ص",
        "target": "all",
    },
    {
        "id": 2,
        "title": "فتح باب تسليم التكليف البرمجي: مشروع REST API و Redis",
        "content": "الموعد النهائي للتسليم: 18 سبتمبر 2024 · قبل يومين",
        "type": "assignment",
        "icon": "assignment",
        "is_read": True,
        "created_at": "قبل يومين",
        "target": "all",
    },
    {
        "id": 3,
        "title": "رابط معمل البث الحي المباشر #14: حل مسائل الـ Dynamic Programming",
        "content": "يبدأ البث اليوم في تمام الساعة 07:00 مساءً · قبل 3 أيام",
        "type": "live",
        "icon": "live_tv",
        "is_read": True,
        "created_at": "قبل 3 أيام",
        "target": "all",
    },
    {
        "id": 4,
        "title": "تم رصد نتيجة تقييم مشروع REST API و Redis بنجاح",
        "content": "الدرجة: 38 / 40 · اجتياز فحص الـ CI/CD بنسبة 100% · أمس",
        "type": "assignment",
        "icon": "task_alt",
        "is_read": False,
        "created_at": "أمس",
        "target": "student",
    },
]


def is_db_active():
    try:
        ok, _, tables, _ = check_connection()
        return ok and "notifications" in tables
    except Exception:
        return False


def get_all_notifications():
    """Retrieve all broadcast and administrative notifications."""
    if is_db_active():
        try:
            sql = """
                SELECT id, title, content, type, icon, is_read, 
                       TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') as created_at
                FROM notifications
                ORDER BY created_at DESC;
            """
            rows = execute_query(sql, fetch=True)
            if rows is not None:
                return rows
        except Exception as e:
            logger.warning(f"Error querying notifications from DB: {e}")

    return list(_NOTIFICATIONS_DB)


def get_student_notifications(user_id=None):
    """Retrieve notifications pertinent to student view (broadcast + user-specific)."""
    if is_db_active():
        try:
            sql = """
                SELECT id, title, content, type, icon, is_read,
                       TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') as created_at
                FROM notifications
                WHERE user_id IS NULL OR user_id = %s
                ORDER BY created_at DESC;
            """
            rows = execute_query(sql, (user_id,), fetch=True)
            if rows is not None:
                return rows
        except Exception as e:
            logger.warning(f"Error querying student notifications from DB: {e}")

    # Fallback
    return [n for n in _NOTIFICATIONS_DB if n.get("target") in ("all", "student")]


def get_unread_count(user_id=None):
    """Return count of unread notifications."""
    notifs = get_student_notifications(user_id)
    return sum(1 for n in notifs if not n.get("is_read"))


def create_notification(data: dict):
    """Create a new broadcast or targeted notification."""
    title = (data.get("title") or "").strip()
    if not title:
        raise ValueError("عنوان التعميم أو الإشعار مطلوب.")

    content = (data.get("content") or "").strip()
    if not content:
        raise ValueError("نص التعميم أو الإشعار مطلوب.")

    notif_type = data.get("type", "announcement")
    if notif_type not in ("exam", "assignment", "live", "announcement"):
        notif_type = "announcement"

    icon_map = {
        "exam": "campaign",
        "assignment": "assignment",
        "live": "live_tv",
        "announcement": "campaign",
    }
    icon = icon_map.get(notif_type, "campaign")

    if is_db_active():
        try:
            sql = """
                INSERT INTO notifications (title, content, type, icon, is_read)
                VALUES (%s, %s, %s, %s, FALSE)
                RETURNING id, title, content, type, icon, is_read,
                          TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') as created_at;
            """
            rows = execute_query(sql, (title, content, notif_type, icon), fetch=True)
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.error(f"Error creating notification in DB: {e}")
            raise

    new_n = {
        "id": max([n["id"] for n in _NOTIFICATIONS_DB], default=10) + 1,
        "title": title,
        "content": content,
        "type": notif_type,
        "icon": icon,
        "is_read": False,
        "created_at": "الآن",
        "target": "all",
    }
    _NOTIFICATIONS_DB.insert(0, new_n)
    return new_n


def delete_notification(notification_id: int):
    """Delete a notification."""
    if not notification_id:
        raise ValueError("معرّف الإشعار مطلوب للحذف.")

    deleted = False
    if is_db_active():
        try:
            execute_query("DELETE FROM notifications WHERE id = %s;", (int(notification_id),), fetch=False)
            deleted = True
        except Exception as e:
            logger.error(f"Error deleting notification from DB: {e}")
            raise

    global _NOTIFICATIONS_DB
    before = len(_NOTIFICATIONS_DB)
    _NOTIFICATIONS_DB = [n for n in _NOTIFICATIONS_DB if n["id"] != int(notification_id)]
    if len(_NOTIFICATIONS_DB) < before:
        deleted = True
    return deleted

