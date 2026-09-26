"""
Lesson Service for CodeVerse LMS
Supports live PostgreSQL queries via DATABASE_URL with graceful fallback.
"""
import json
import logging
from database import execute_query, check_connection

logger = logging.getLogger(__name__)

# Empty — all lessons come from the Supabase DB.
# Do NOT add mock lessons here; if DB is offline, the page will show an empty list
# which is correct behavior (no fake data).
_LESSONS_DB = []



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
                    COALESCE(ROUND(SUM(duration_minutes)/60.0, 1), 0) as training_hours,
                    COUNT(CASE WHEN is_live = true THEN 1 END) as live_this_week,
                    COUNT(CASE WHEN pdf_name IS NOT NULL THEN 1 END) as pdf_count,
                    COUNT(DISTINCT track) as tracks_count,
                    COALESCE(
                        ROUND(
                            (
                                (SELECT COUNT(DISTINCT student_id || '-' || lesson_id::text) FROM lesson_completions)::numeric 
                                / NULLIF(((SELECT COUNT(*) FROM students) * (SELECT GREATEST(COUNT(*), 1) FROM lessons)), 0)
                            ) * 100
                        ),
                        0
                    ) as plan_completion
                FROM lessons;
            """
            rows = execute_query(sql, fetch=True)
            if rows:
                r = rows[0]
                # Fetch lessons for chart data with live attendance and progress
                lesson_rows = execute_query(
                    """
                    SELECT 
                        l.id, l.code, l.title, l.track, l.is_live, l.live_time,
                        COALESCE((SELECT COUNT(DISTINCT student_id) FROM lesson_completions WHERE lesson_id = l.id), 0) as attendees,
                        COALESCE(
                            CASE 
                                WHEN (SELECT COUNT(*) FROM students) > 0 
                                THEN LEAST(100, ROUND(((SELECT COUNT(DISTINCT student_id) FROM lesson_completions WHERE lesson_id = l.id)::numeric / (SELECT COUNT(*) FROM students)::numeric) * 100))
                                ELSE 0 
                            END,
                            0
                        ) as progress
                    FROM lessons l
                    ORDER BY l.order_num ASC;
                    """,
                    fetch=True
                )
                lessons_data = [dict(lr) for lr in (lesson_rows or [])]
                # Find next live lesson
                live_lesson = next((l for l in lessons_data if l.get("is_live")), None)
                live_this_week = int(r["live_this_week"] or 0)
                if live_lesson:
                    live_today_text = live_lesson.get("title", "")[:28]
                    live_status_label = live_lesson.get("live_time") or "مباشر اليوم"
                else:
                    live_today_text = "لا توجد حصص مباشرة اليوم"
                    live_status_label = "حالة البث"

                tracks_count = max(int(r.get("tracks_count") or 0), 2)
                plan_val = int(r.get("plan_completion") or 0)
                training_h = float(r["training_hours"] or 0)
                training_hours_disp = int(training_h) if training_h.is_integer() else training_h

                return {
                    "published_count": r["published_count"],
                    "training_hours": training_hours_disp,
                    "live_this_week": live_this_week,
                    "pdf_count": r["pdf_count"],
                    "lessons_data": lessons_data,
                    "live_lesson": live_lesson,
                    "live_today_text": live_today_text,
                    "live_status_label": live_status_label,
                    "tracks_count": tracks_count,
                    "plan_completion": f"{plan_val}%",
                    "plan_completion_num": plan_val,
                }
        except Exception as e:
            logger.warning(f"Error querying lesson summary: {e}")

    lessons_data = _LESSONS_DB
    live_lesson = next((l for l in lessons_data if l.get("is_live")), None)
    return {
        "published_count": len(_LESSONS_DB),
        "training_hours": sum(l.get("duration_minutes", 0) for l in _LESSONS_DB) // 60,
        "live_this_week": sum(1 for l in _LESSONS_DB if l.get("is_live")),
        "pdf_count": sum(1 for l in _LESSONS_DB if l.get("pdf_name")),
        "lessons_data": lessons_data,
        "live_lesson": live_lesson,
        "live_today_text": live_lesson.get("title", "")[:28] if live_lesson else "لا توجد حصص مباشرة اليوم",
        "live_status_label": "حالة البث",
        "tracks_count": 2,
        "plan_completion": "100%" if _LESSONS_DB else "0%",
        "plan_completion_num": 100 if _LESSONS_DB else 0,
    }


def get_all_lessons(query=None, track=None):
    """Retrieve lessons with optional filter."""
    if is_db_active():
        try:
            sql = """
                SELECT 
                    l.*,
                    COALESCE((SELECT COUNT(DISTINCT student_id) FROM lesson_completions WHERE lesson_id = l.id), 0) as attendees,
                    COALESCE(
                        CASE 
                            WHEN (SELECT COUNT(*) FROM students) > 0 
                            THEN LEAST(100, ROUND(((SELECT COUNT(DISTINCT student_id) FROM lesson_completions WHERE lesson_id = l.id)::numeric / (SELECT COUNT(*) FROM students)::numeric) * 100))
                            ELSE 0 
                        END,
                        0
                    ) as progress
                FROM lessons l
                ORDER BY l.order_num ASC;
            """
            rows = execute_query(sql, fetch=True)
            if rows is not None:
                results = [dict(r) for r in rows]
                for l in results:
                    if not l.get("instructor"):
                        l["instructor"] = "المهندس عبدالرحمن تامر"
                    if isinstance(l.get("topics"), str):
                        try:
                            l["topics"] = json.loads(l["topics"])
                        except Exception:
                            l["topics"] = [l["topics"]]
                    elif l.get("topics") is None:
                        l["topics"] = []
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
    if not lesson_id:
        return None
    if is_db_active():
        try:
            sql = """
                SELECT 
                    l.*,
                    COALESCE((SELECT COUNT(DISTINCT student_id) FROM lesson_completions WHERE lesson_id = l.id), 0) as attendees,
                    COALESCE(
                        CASE 
                            WHEN (SELECT COUNT(*) FROM students) > 0 
                            THEN LEAST(100, ROUND(((SELECT COUNT(DISTINCT student_id) FROM lesson_completions WHERE lesson_id = l.id)::numeric / (SELECT COUNT(*) FROM students)::numeric) * 100))
                            ELSE 0 
                        END,
                        0
                    ) as progress
                FROM lessons l 
                WHERE l.id = %s LIMIT 1;
            """
            rows = execute_query(sql, (lesson_id,), fetch=True)
            if rows:
                l = dict(rows[0])
                if not l.get("instructor"):
                    l["instructor"] = "المهندس عبدالرحمن تامر"
                if isinstance(l.get("topics"), str):
                    try:
                        l["topics"] = json.loads(l["topics"])
                    except Exception:
                        l["topics"] = [l["topics"]]
                elif l.get("topics") is None:
                    l["topics"] = []
                return l
        except Exception as e:
            logger.warning(f"Error querying lesson by ID: {e}")

    for l in _LESSONS_DB:
        if l["id"] == lesson_id:
            return l
    return None


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
    is_live = bool(data.get("is_live", False))
    live_time = (data.get("live_time") or ("اليوم 07:00 م" if is_live else "مسجلة")).strip()
    video_url = (data.get("video_url") or "").strip()
    live_url = (data.get("live_url") or "").strip()
    short_title = title[:50]

    instructor = (data.get("instructor") or "المهندس عبدالرحمن تامر").strip()
    description = (data.get("description") or "").strip()
    raw_topics = data.get("topics")
    if isinstance(raw_topics, str):
        topics = [t.strip() for t in raw_topics.splitlines() if t.strip()]
    elif isinstance(raw_topics, list):
        topics = raw_topics
    else:
        topics = []

    if is_db_active():
        try:
            sql = """
                INSERT INTO lessons (code, title, short_title, track, track_slug, duration_minutes, duration_text, attendees, progress, instructor, order_num, lesson_date, image_url, material_url, homework_id, is_live, live_time, video_url, live_url, description, topics)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 0, 0, %s, 10, NULLIF(%s, '')::date, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                RETURNING *;
            """
            rows = execute_query(
                sql,
                (code, title, short_title, track, track_slug, duration_minutes, duration_text, instructor, lesson_date, image_url, material_url, homework_id, is_live, live_time, video_url, live_url, description, json.dumps(topics, ensure_ascii=False)),
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
        "is_live": is_live,
        "live_time": live_time,
        "video_url": video_url,
        "live_url": live_url,
        "instructor": instructor,
        "description": description,
        "topics": topics,
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
    # Pass None when date is empty — avoids PostgreSQL ::date cast error
    _raw_date = (data.get("lesson_date") or "").strip()
    lesson_date = _raw_date if _raw_date else None
    image_url = (data.get("image_url") or "").strip()
    material_url = (data.get("material_url") or "").strip()
    homework_id = data.get("homework_id") or None
    is_live = bool(data.get("is_live", False)) if "is_live" in data else None
    live_time = data.get("live_time")
    video_url = data.get("video_url")
    live_url = data.get("live_url")
    instructor = (data.get("instructor") or "المهندس عبدالرحمن تامر").strip()
    description = data.get("description")
    raw_topics = data.get("topics")
    topics = None
    if raw_topics is not None:
        if isinstance(raw_topics, str):
            topics = [t.strip() for t in raw_topics.splitlines() if t.strip()]
        elif isinstance(raw_topics, list):
            topics = raw_topics

    if is_db_active():
        try:
            fields = [
                "title = COALESCE(NULLIF(%s, ''), title)",
                "code = COALESCE(NULLIF(%s, ''), code)",
                "track = COALESCE(NULLIF(%s, ''), track)",
                "duration_minutes = %s",
                "duration_text = %s",
                "lesson_date = %s",
                "image_url = %s",
                "material_url = %s",
                "homework_id = %s",
                "instructor = %s",
            ]
            params = [title, code, track, duration_minutes, duration_text, lesson_date, image_url, material_url, homework_id, instructor]
            if is_live is not None:
                fields.append("is_live = %s")
                params.append(is_live)
            if live_time is not None:
                fields.append("live_time = %s")
                params.append(live_time.strip())
            if video_url is not None:
                fields.append("video_url = %s")
                params.append(video_url.strip())
            if live_url is not None:
                fields.append("live_url = %s")
                params.append(live_url.strip())
            if description is not None:
                fields.append("description = %s")
                params.append(description.strip())
            if topics is not None:
                fields.append("topics = %s::jsonb")
                params.append(json.dumps(topics, ensure_ascii=False))

            params.append(int(lesson_id))
            sql = f"""
                UPDATE lessons
                SET {', '.join(fields)}
                WHERE id = %s
                RETURNING *;
            """
            rows = execute_query(sql, tuple(params), fetch=True)
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
            l["instructor"] = instructor
            if description is not None: l["description"] = description
            if topics is not None: l["topics"] = topics
            if is_live is not None: l["is_live"] = is_live
            if live_time is not None: l["live_time"] = live_time
            if video_url is not None: l["video_url"] = video_url
            if live_url is not None: l["live_url"] = live_url
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


def resolve_student_uuid(student_id):
    """Resolve any student identifier (UUID, username, code) to canonical student UUID."""
    if not student_id:
        return None
    sid_str = str(student_id).strip()
    if is_db_active():
        try:
            sql = """
                SELECT CAST(s.id AS TEXT) as uuid
                FROM students s
                LEFT JOIN users u ON s.id = u.id
                WHERE CAST(s.id AS TEXT) = %s
                   OR s.student_code = %s
                   OR lower(u.username) = lower(%s)
                LIMIT 1;
            """
            rows = execute_query(sql, (sid_str, sid_str, sid_str), fetch=True)
            if rows:
                return rows[0]["uuid"]
        except Exception as e:
            logger.warning(f"Error resolving student UUID: {e}")
    return sid_str


# In-memory tracking of completed lessons per student: student_id -> set(lesson_ids)
_COMPLETED_LESSONS_CACHE = {}


def get_completed_lesson_ids(student_id):
    """Return set of completed lesson IDs for this student."""
    if not student_id:
        return set()
    sid_str = str(student_id).strip()
    sid_uuid = resolve_student_uuid(student_id) or sid_str

    if is_db_active():
        try:
            execute_query("""
                CREATE TABLE IF NOT EXISTS lesson_completions (
                    student_id TEXT NOT NULL,
                    lesson_id INTEGER NOT NULL,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(student_id, lesson_id)
                );
            """, fetch=False, commit=True)

            rows = execute_query(
                """
                SELECT DISTINCT lesson_id 
                FROM lesson_completions 
                WHERE student_id = %s OR student_id = %s;
                """,
                (sid_uuid, sid_str), fetch=True
            )
            if rows is not None:
                return {int(r["lesson_id"]) for r in rows}
        except Exception as e:
            logger.warning(f"Error querying completed lessons from DB: {e}")

    cached = _COMPLETED_LESSONS_CACHE.get(sid_str, set())
    if not cached and sid_uuid != sid_str:
        cached = _COMPLETED_LESSONS_CACHE.get(sid_uuid, set())
    return set(cached)


def is_lesson_completed(lesson_id: int, student_id) -> bool:
    if not lesson_id or not student_id:
        return False
    return int(lesson_id) in get_completed_lesson_ids(student_id)


def get_completed_lessons_count(student_id) -> int:
    return len(get_completed_lesson_ids(student_id))


def toggle_lesson_completion(lesson_id: int, student_id) -> bool:
    """Toggle lesson completion state. Returns True if now completed, False if unmarked."""
    if not lesson_id or not student_id:
        return False
    lid = int(lesson_id)
    sid_str = str(student_id).strip()
    sid_uuid = resolve_student_uuid(student_id) or sid_str

    completed_now = True
    if is_db_active():
        try:
            execute_query("""
                CREATE TABLE IF NOT EXISTS lesson_completions (
                    student_id TEXT NOT NULL,
                    lesson_id INTEGER NOT NULL,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(student_id, lesson_id)
                );
            """, fetch=False, commit=True)

            exists = execute_query(
                "SELECT 1 FROM lesson_completions WHERE (student_id = %s OR student_id = %s) AND lesson_id = %s;",
                (sid_uuid, sid_str, lid), fetch=True
            )
            if exists:
                execute_query(
                    "DELETE FROM lesson_completions WHERE (student_id = %s OR student_id = %s) AND lesson_id = %s;",
                    (sid_uuid, sid_str, lid), fetch=False, commit=True
                )
                completed_now = False
            else:
                # Insert canonical UUID
                execute_query(
                    "INSERT INTO lesson_completions (student_id, lesson_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                    (sid_uuid, lid), fetch=False, commit=True
                )
                completed_now = True

            # Clean any duplicate or legacy rows for this student and lesson
            execute_query(
                """
                DELETE FROM lesson_completions
                WHERE (student_id = %s OR student_id = %s)
                  AND student_id != %s
                  AND lesson_id = %s;
                """,
                (sid_uuid, sid_str, sid_uuid, lid), fetch=False, commit=True
            )

            # Sync students table counts
            execute_query("""
                UPDATE students 
                SET completed_lessons = (
                    SELECT COUNT(DISTINCT lesson_id) 
                    FROM lesson_completions 
                    WHERE student_id = %s OR student_id = %s
                ),
                total_lessons = (SELECT COUNT(*) FROM lessons)
                WHERE CAST(id AS TEXT) = %s OR CAST(id AS TEXT) = %s OR student_code = %s;
            """, (sid_uuid, sid_str, sid_uuid, sid_str, sid_str), fetch=False, commit=True)

            # Sync lessons table attendees and progress for all lessons
            execute_query("""
                UPDATE lessons
                SET attendees = (
                    SELECT COUNT(DISTINCT student_id)
                    FROM lesson_completions
                    WHERE lesson_id = lessons.id
                ),
                progress = CASE
                    WHEN (SELECT COUNT(*) FROM students) > 0
                    THEN LEAST(100, ROUND(((SELECT COUNT(DISTINCT student_id) FROM lesson_completions WHERE lesson_id = lessons.id)::numeric / (SELECT COUNT(*) FROM students)::numeric) * 100))
                    ELSE 0
                END;
            """, fetch=False, commit=True)
        except Exception as e:
            logger.warning(f"Error toggling lesson completion in DB: {e}")

    # Also update in-memory cache
    for k in (sid_str, sid_uuid):
        if k not in _COMPLETED_LESSONS_CACHE:
            _COMPLETED_LESSONS_CACHE[k] = set()
        if completed_now:
            _COMPLETED_LESSONS_CACHE[k].add(lid)
        else:
            _COMPLETED_LESSONS_CACHE[k].discard(lid)

    # Sync _STUDENTS_DB and _LESSONS_DB
    try:
        from services import student_service
        total_l = len(_LESSONS_DB)
        curr_completed = len(_COMPLETED_LESSONS_CACHE.get(sid_uuid, _COMPLETED_LESSONS_CACHE.get(sid_str, set())))
        for s in student_service._STUDENTS_DB:
            if str(s.get("id")) in (sid_str, sid_uuid) or str(s.get("code")) in (sid_str, sid_uuid) or s.get("username") in (sid_str, sid_uuid):
                s["completed_lessons"] = curr_completed
                s["total_lessons"] = total_l

        tot_students = max(1, len(student_service._STUDENTS_DB))
        for l in _LESSONS_DB:
            tot_attend = sum(1 for cache_set in _COMPLETED_LESSONS_CACHE.values() if l.get("id") in cache_set)
            l["attendees"] = tot_attend
            l["progress"] = min(100, int((tot_attend / tot_students) * 100))
    except Exception as e:
        logger.debug(f"Could not sync student_db in-memory: {e}")

    return completed_now

