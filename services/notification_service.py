"""
Notification Service for CodeVerse LMS
Supports live PostgreSQL queries via DATABASE_URL with graceful fallback.
Supports:
  - Broadcast notifications (user_id IS NULL) — visible to all students
  - Personal notifications (user_id set)      — visible to that student only
"""
import logging
from database import execute_query, check_connection

logger = logging.getLogger(__name__)

_NOTIFICATIONS_DB = [
    {
        "id": 1,
        "title": "تذكير أكاديمي: موعد الاختبار النصفي لهياكل البيانات والخوارزميات",
        "content": "يُرجى من جميع الطلاب مراجعة بنك الأسئلة والاستعداد الجيد.",
        "type": "exam",
        "icon": "campaign",
        "is_read": False,
        "created_at": "اليوم 11:20 ص",
        "target": "broadcast",
        "user_id": None,
        "recipient_label": "جميع الطلاب",
    },
    {
        "id": 2,
        "title": "فتح باب تسليم التكليف البرمجي: مشروع REST API و Redis",
        "content": "الموعد النهائي للتسليم: 18 سبتمبر 2024.",
        "type": "assignment",
        "icon": "assignment",
        "is_read": True,
        "created_at": "قبل يومين",
        "target": "broadcast",
        "user_id": None,
        "recipient_label": "جميع الطلاب",
    },
]


def is_db_active():
    try:
        ok, _, tables, _ = check_connection()
        return ok and "notifications" in tables
    except Exception:
        return False


def get_all_notifications():
    """Retrieve all notifications (broadcast + personal) for the admin panel."""
    if is_db_active():
        try:
            sql = """
                SELECT n.id, n.title, n.content, n.type, n.icon, n.is_read,
                       n.user_id,
                       COALESCE(s.name, s.username, 'جميع الطلاب') AS recipient_label,
                       TO_CHAR(n.created_at, 'YYYY-MM-DD HH24:MI') as created_at
                FROM notifications n
                LEFT JOIN students s ON CAST(s.id AS TEXT) = CAST(n.user_id AS TEXT)
                ORDER BY n.created_at DESC;
            """
            rows = execute_query(sql, fetch=True)
            if rows is not None:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Error querying notifications from DB: {e}")

    return list(_NOTIFICATIONS_DB)


def get_student_notifications(user_id=None):
    """Retrieve notifications for a student: broadcast (user_id IS NULL) + personal ones."""
    if is_db_active():
        try:
            sql = """
                SELECT id, title, content, type, icon, is_read, user_id,
                       CASE WHEN user_id IS NULL THEN 'broadcast' ELSE 'personal' END AS target,
                       TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') as created_at
                FROM notifications
                WHERE user_id IS NULL OR CAST(user_id AS TEXT) = %s
                ORDER BY created_at DESC;
            """
            rows = execute_query(sql, (str(user_id),), fetch=True)
            if rows is not None:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Error querying student notifications from DB: {e}")

    # Fallback: show all + personal for this user
    return [
        n for n in _NOTIFICATIONS_DB
        if n.get("user_id") is None or str(n.get("user_id")) == str(user_id)
    ]


def get_unread_count(user_id=None):
    """Return count of unread notifications for a student."""
    notifs = get_student_notifications(user_id)
    return sum(1 for n in notifs if not n.get("is_read"))


def create_notification(data: dict):
    """
    Create a notification.
    data keys:
      - title (required)
      - content (required)
      - type: 'exam' | 'assignment' | 'live' | 'announcement' | 'personal'
      - user_id: None for broadcast, or a student UUID/id for personal
    """
    title = (data.get("title") or "").strip()
    if not title:
        raise ValueError("عنوان التعميم أو الإشعار مطلوب.")

    content = (data.get("content") or "").strip()
    if not content:
        raise ValueError("نص التعميم أو الإشعار مطلوب.")

    notif_type = data.get("type", "announcement")
    if notif_type not in ("exam", "assignment", "live", "announcement", "personal"):
        notif_type = "announcement"

    icon_map = {
        "exam": "campaign",
        "assignment": "assignment",
        "live": "live_tv",
        "announcement": "campaign",
        "personal": "person",
    }
    icon = icon_map.get(notif_type, "campaign")
    user_id = data.get("user_id") or None  # None = broadcast

    if is_db_active():
        try:
            sql = """
                INSERT INTO notifications (title, content, type, icon, is_read, user_id)
                VALUES (%s, %s, %s, %s, FALSE, %s)
                RETURNING id, title, content, type, icon, is_read, user_id,
                          TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') as created_at;
            """
            rows = execute_query(sql, (title, content, notif_type, icon, user_id), fetch=True, commit=True)
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
        "user_id": user_id,
        "target": "personal" if user_id else "broadcast",
        "recipient_label": "طالب محدد" if user_id else "جميع الطلاب",
    }
    _NOTIFICATIONS_DB.insert(0, new_n)
    return new_n


def mark_notification_read(notification_id: int, user_id=None):
    """Mark a notification as read."""
    if is_db_active():
        try:
            execute_query(
                "UPDATE notifications SET is_read = TRUE WHERE id = %s;",
                (int(notification_id),), fetch=False, commit=True
            )
            return True
        except Exception as e:
            logger.warning(f"Error marking notification read: {e}")

    for n in _NOTIFICATIONS_DB:
        if n["id"] == int(notification_id):
            n["is_read"] = True
            return True
    return False


def mark_all_read(user_id=None):
    """Mark all notifications for a student as read."""
    if is_db_active():
        try:
            execute_query(
                "UPDATE notifications SET is_read = TRUE WHERE user_id IS NULL OR CAST(user_id AS TEXT) = %s;",
                (str(user_id) if user_id else "",), fetch=False, commit=True
            )
            return True
        except Exception as e:
            logger.warning(f"Error marking all notifications read: {e}")

    for n in _NOTIFICATIONS_DB:
        if n.get("user_id") is None or str(n.get("user_id")) == str(user_id):
            n["is_read"] = True
    return True


def delete_notification(notification_id: int):
    """Delete a notification."""
    if not notification_id:
        raise ValueError("معرّف الإشعار مطلوب للحذف.")

    if is_db_active():
        try:
            execute_query("DELETE FROM notifications WHERE id = %s;", (int(notification_id),), fetch=False, commit=True)
            return True
        except Exception as e:
            logger.error(f"Error deleting notification from DB: {e}")
            raise

    global _NOTIFICATIONS_DB
    before = len(_NOTIFICATIONS_DB)
    _NOTIFICATIONS_DB = [n for n in _NOTIFICATIONS_DB if n["id"] != int(notification_id)]
    return len(_NOTIFICATIONS_DB) < before
