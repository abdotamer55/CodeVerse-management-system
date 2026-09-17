"""
Lesson Service for CodeVerse LMS
Supports live PostgreSQL queries via DATABASE_URL with graceful fallback.
"""
import logging
from database import execute_query, check_connection

logger = logging.getLogger(__name__)

_LESSONS_DB = [
    {
        "id": 1,
        "code": "LES-014",
        "title": "معمارية الـ Microservices وتدفق الرسائل عبر NestJS & RabbitMQ",
        "short_title": "معمارية الـ Microservices وRabbitMQ",
        "track": "هندسة النظم الخلفية (Backend)",
        "track_slug": "backend",
        "duration_minutes": 95,
        "duration_text": "ساعة و 35 دقيقة",
        "attendees": 184,
        "progress": 70,
        "is_live": True,
        "live_time": "اليوم 07:00 م",
        "instructor": "د. طارق الحارثي",
        "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "description": "دراسة تفصيلية لبناء بيئات الخدمات المصغرة المستقلة، أنماط معالجة الأحداث غير المتزامنة، وإعداد وسيط الرسائل الموزع RabbitMQ في إنتاجية عالية.",
        "topics": [
            "مفهوم Event-Driven Architecture",
            "تهيئة بروتوكول AMQP في NestJS",
            "إدارة رسائل الفشل ومستودعات Dead Letter Exchange",
            "تطبيق عملي لمزامنة بيانات الدفع والطلبات",
        ],
        "pdf_name": "microservices-rabbitmq-guide.pdf",
        "repo_name": "cv-microservices-starter",
    },
    {
        "id": 2,
        "code": "LES-022",
        "title": "فهرسة قواعد البيانات واستراتيجيات تسريع استعلامات الـ SQL المركبة",
        "short_title": "فهرسة قواعد البيانات واستعلامات SQL",
        "track": "هندسة النظم الخلفية (Backend)",
        "track_slug": "backend",
        "duration_minutes": 80,
        "duration_text": "ساعة و 20 دقيقة",
        "attendees": 142,
        "progress": 100,
        "is_live": False,
        "live_time": "مسجلة بالكامل",
        "instructor": "م. ريان السعيد",
        "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
        "description": "فهم خوارزميات B-Tree و Hash Indexes في محركات PostgreSQL، قراءة خطة التنفيذ EXPLAIN ANALYZE وتحسين استعلامات الربط JOIN المعقدة.",
        "topics": [
            "كيف تفكر محركات التخزين عند قراءة الأقراص",
            "أنواع الفهارس المركبة Composite Indexes",
            "تحليل كلفة الاستعلام Cost Metrics في Postgres",
            "تمارين عملية لتخفيض زمن الاستعلام من 3 ثوانٍ إلى 12ms",
        ],
        "pdf_name": "postgres-indexing-mastery.pdf",
        "repo_name": "sql-performance-lab",
    },
    {
        "id": 3,
        "code": "LES-030",
        "title": "أسرار React 19: بنية Server Actions ودورة حياة مكونات RSC",
        "short_title": "أسرار React 19 و Server Components",
        "track": "تطوير الواجهات المتقدمة (Frontend)",
        "track_slug": "frontend",
        "duration_minutes": 110,
        "duration_text": "ساعة و 50 دقيقة",
        "attendees": 196,
        "progress": 40,
        "is_live": False,
        "live_time": "غداً 08:30 م",
        "instructor": "م. أروى الحمدان",
        "video_url": "",
        "description": "التحول الجذري في نموذج عتاد React: التمييز بين مكونات الخادم ومكونات العميل، استدعاء الدوال الخلفية مباشرة دون كتابة نقاط REST يدوية.",
        "topics": [
            "معمارية React Server Components",
            "معالجة النماذج عبر useActionState",
            "Optimistic Updates وتجربة المستخدم الفورية",
            "إدارة الكاش و revalidatePath",
        ],
        "pdf_name": "react19-server-actions.pdf",
        "repo_name": "nextjs15-react19-playground",
    },
]


def is_db_active():
    try:
        ok, _, tables, _ = check_connection()
        return ok and "lessons" in tables
    except Exception:
        return False


def get_lessons_summary():
    """Aggregated lesson statistics."""
    if is_db_active():
        try:
            sql = """
                SELECT 
                    COUNT(*) as published_count,
                    COALESCE(ROUND(SUM(duration_minutes)/60.0), 0) as training_hours,
                    COUNT(CASE WHEN is_live = true THEN 1 END) as live_this_week,
                    COUNT(CASE WHEN pdf_name IS NOT NULL THEN 1 END) as pdf_count
                FROM lessons;
            """
            rows = execute_query(sql, fetch=True)
            if rows:
                r = rows[0]
                return {
                    "published_count": r["published_count"],
                    "training_hours": int(r["training_hours"]),
                    "live_this_week": r["live_this_week"],
                    "pdf_count": r["pdf_count"],
                }
        except Exception as e:
            logger.warning(f"Error querying lesson summary: {e}")

    return {
        "published_count": 84,
        "training_hours": 142,
        "live_this_week": 6,
        "pdf_count": 52,
    }


def get_all_lessons(query=None, track=None):
    """Retrieve lessons with optional filter."""
    if is_db_active():
        try:
            sql = "SELECT * FROM lessons ORDER BY order_num ASC;"
            rows = execute_query(sql, fetch=True)
            if rows:
                results = [dict(r) for r in rows]
                if track and track != "all":
                    results = [l for l in results if l.get("track_slug") == track]
                if query:
                    q = query.strip().lower()
                    results = [
                        l for l in results
                        if q in l["title"].lower() or q in l["code"].lower()
                    ]
                return results
        except Exception as e:
            logger.warning(f"Error querying all lessons: {e}")

    results = _LESSONS_DB
    if track and track != "all":
        results = [l for l in results if l.get("track_slug") == track]
    if query:
        q = query.strip().lower()
        results = [
            l for l in results
            if q in l["title"].lower() or q in l["code"].lower()
        ]
    return results


def get_lesson_by_id(lesson_id: int):
    """Retrieve full lesson details."""
    if is_db_active():
        try:
            sql = "SELECT * FROM lessons WHERE id = %s LIMIT 1;"
            rows = execute_query(sql, (lesson_id,), fetch=True)
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.warning(f"Error querying lesson by ID: {e}")

    for l in _LESSONS_DB:
        if l["id"] == lesson_id:
            return l
    return _LESSONS_DB[0]


def get_student_lesson_overview():
    """Admin-controlled lesson metadata drives current, next, and material listings."""
    def lesson_sort_key(item):
        lesson_date = item.get("lesson_date")
        if lesson_date is None or lesson_date == "":
            return (1, "", item.get("id", 0))
        normalized_date = lesson_date.isoformat() if hasattr(lesson_date, "isoformat") else str(lesson_date)
        return (0, normalized_date, item.get("id", 0))

    lessons = sorted(get_all_lessons(), key=lesson_sort_key)
    for lesson in lessons:
        lesson.setdefault("lesson_date", lesson.get("live_time", "يحددها المسؤول"))
        lesson.setdefault("image_url", "")
        lesson.setdefault("material_url", lesson.get("pdf_url", ""))
    return {"current": lessons[0] if lessons else None, "next": lessons[1] if len(lessons) > 1 else None, "materials": lessons}


def get_lesson_materials(lesson_id: int):
    """Return metadata-backed lesson materials, preserving the existing files table as the source of truth."""
    try:
        from services import file_service
        return file_service.get_lesson_files(lesson_id)
    except Exception:
        return []


def create_lesson(data: dict):
    """Create a new lesson."""
    title = (data.get("title") or "").strip()
    if not title:
        raise ValueError("عنوان الحصة مطلوب.")

    code = (data.get("code") or "").strip()
    if not code:
        code = f"LES-{len(_LESSONS_DB) + 1:03d}"

    track = (data.get("track") or "هندسة برمجيات الأنظمة").strip()
    track_slug = "react" if "react" in track.lower() else ("node" if "node" in track.lower() else "systems")
    duration_minutes = int(data.get("duration_minutes") or 60)
    duration_text = f"{duration_minutes} دقيقة"
    lesson_date = (data.get("lesson_date") or "").strip()
    image_url = (data.get("image_url") or "").strip()
    material_url = (data.get("material_url") or "").strip()
    homework_id = data.get("homework_id") or None
    short_title = title[:50]

    if is_db_active():
        try:
            sql = """
                INSERT INTO lessons (code, title, short_title, track, track_slug, duration_minutes, duration_text, attendees, progress, instructor, order_num, lesson_date, image_url, material_url, homework_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 0, 0, 'د. طارق الحارثي', 10, NULLIF(%s, '')::date, %s, %s, %s)
                RETURNING *;
            """
            rows = execute_query(
                sql,
                (code, title, short_title, track, track_slug, duration_minutes, duration_text, lesson_date, image_url, material_url, homework_id),
                fetch=True
            )
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.error(f"Error creating lesson in DB: {e}")
            raise

    new_l = {
        "id": max([l["id"] for l in _LESSONS_DB], default=10) + 1,
        "code": code,
        "title": title,
        "short_title": short_title,
        "track": track,
        "track_slug": track_slug,
        "duration_minutes": duration_minutes,
        "duration_text": duration_text,
        "attendees": 0,
        "progress": 0,
        "is_live": False,
        "instructor": "د. طارق الحارثي",
        "lesson_date": lesson_date, "image_url": image_url, "material_url": material_url, "homework_id": homework_id,
    }
    _LESSONS_DB.append(new_l)
    return new_l


def update_lesson(lesson_id: int, data: dict):
    """Update an existing lesson."""
    title = (data.get("title") or "").strip()
    code = (data.get("code") or "").strip()
    track = (data.get("track") or "").strip()
    duration_minutes = int(data.get("duration_minutes") or 60)
    duration_text = f"{duration_minutes} دقيقة"
    lesson_date = (data.get("lesson_date") or "").strip()
    image_url = (data.get("image_url") or "").strip()
    material_url = (data.get("material_url") or "").strip()
    homework_id = data.get("homework_id") or None

    if is_db_active():
        try:
            sql = """
                UPDATE lessons
                SET title = COALESCE(NULLIF(%s, ''), title),
                    code = COALESCE(NULLIF(%s, ''), code),
                    track = COALESCE(NULLIF(%s, ''), track),
                    duration_minutes = %s,
                    duration_text = %s,
                    lesson_date = NULLIF(%s, '')::date,
                    image_url = %s,
                    material_url = %s,
                    homework_id = %s
                WHERE id = %s
                RETURNING *;
            """
            rows = execute_query(
                sql,
                (title, code, track, duration_minutes, duration_text, lesson_date, image_url, material_url, homework_id, int(lesson_id)),
                fetch=True
            )
            if rows:
                return dict(rows[0])
        except Exception as e:
            logger.error(f"Error updating lesson in DB: {e}")
            raise

    for l in _LESSONS_DB:
        if l["id"] == int(lesson_id):
            if title: l["title"] = title
            if code: l["code"] = code
            if track: l["track"] = track
            l["duration_minutes"] = duration_minutes
            l["duration_text"] = duration_text
            l["lesson_date"] = lesson_date
            l["image_url"] = image_url
            l["material_url"] = material_url
            l["homework_id"] = homework_id
            return l
    return None


def delete_lesson(lesson_id: int):
    """Delete a lesson."""
    if not lesson_id:
        raise ValueError("معرّف الحصة مطلوب للحذف.")

    deleted = False
    if is_db_active():
        try:
            execute_query("DELETE FROM lessons WHERE id = %s;", (int(lesson_id),), fetch=False)
            deleted = True
        except Exception as e:
            logger.error(f"Error deleting lesson from DB: {e}")
            raise

    global _LESSONS_DB
    before = len(_LESSONS_DB)
    _LESSONS_DB = [l for l in _LESSONS_DB if l["id"] != int(lesson_id)]
    if len(_LESSONS_DB) < before:
        deleted = True
    return deleted
