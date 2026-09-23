"""
Database and Service Layer Test Suite for CodeVerse LMS
Tests database connection diagnostics, schema migration validation,
and all 8 domain service modules in live or dev fallback mode.
"""
import os
import unittest
from database import get_database_url, get_sanitized_db_host, check_connection
from services import (
    auth_service,
    student_service,
    lesson_service,
    homework_service,
    exam_service,
    result_service,
    file_service,
    notification_service,
)


class DatabaseAndServicesTestCase(unittest.TestCase):
    def test_database_url_and_sanitization(self):
        """Verify sanitized DB host protects credentials."""
        host = get_sanitized_db_host()
        self.assertIsInstance(host, str)
        # Sanitized host must NOT contain passwords or connection strings with @ credentials
        self.assertNotIn("password", host.lower())
        self.assertNotIn("postgres://", host.lower())
        self.assertNotIn("postgresql://", host.lower())

    def test_check_connection_structure(self):
        """Verify check_connection returns standard (success, host, tables, error) tuple."""
        ok, host, tables, err = check_connection()
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(host, str)
        self.assertIsInstance(tables, list)
        if not ok:
            self.assertIsNotNone(err)
            self.assertIsInstance(err, str)
        else:
            self.assertIsNone(err)

    def test_migration_files_exist_and_cover_entities(self):
        """Ensure migration scripts exist and declare all 10 required database tables."""
        m1_path = os.path.join("supabase", "migrations", "001_initial_schema.sql")
        m2_path = os.path.join("supabase", "migrations", "002_seed_data.sql")
        self.assertTrue(os.path.exists(m1_path), "001_initial_schema.sql must exist")
        self.assertTrue(os.path.exists(m2_path), "002_seed_data.sql must exist")

        with open(m1_path, "r", encoding="utf-8") as f:
            sql1 = f.read().lower()

        required_tables = [
            "users",
            "students",
            "lessons",
            "homework",
            "submissions",
            "exams",
            "questions",
            "results",
            "files",
            "notifications",
        ]
        for tbl in required_tables:
            self.assertIn(f"create table if not exists {tbl}", sql1, f"Table {tbl} must be created in migration")

    def test_schema_extension_migration_adds_question_units_and_material_links(self):
        """The workflow requires reusable question-bank units and lesson-to-file mappings."""
        migration_path = os.path.join("supabase", "migrations", "005_question_bank_and_materials.sql")
        self.assertTrue(os.path.exists(migration_path), "Missing schema extension migration for question bank and lesson materials")

        with open(migration_path, "r", encoding="utf-8") as f:
            sql = f.read().lower()

        required_tables = [
            "question_units",
            "lesson_files",
            "homework_questions",
            "exam_questions",
            "student_answers",
        ]
        for table in required_tables:
            self.assertIn(f"create table if not exists {table}", sql, f"Table {table} must be created in migration")

        self.assertIn("lesson_id", sql)
        self.assertIn("question_id", sql)
        self.assertIn("unit_id", sql)

    def test_auth_service(self):
        """Verify authentication service login logic with valid and invalid users."""
        # Valid student
        user, err = auth_service.authenticate("student@codeverse.edu", "student123")
        self.assertIsNone(err)
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "student")

        # Valid admin
        admin, err = auth_service.authenticate("admin@codeverse.edu", "admin123")
        self.assertIsNone(err)
        self.assertIsNotNone(admin)
        self.assertEqual(admin["role"], "admin")

        # Invalid password
        bad_user, err = auth_service.authenticate("student@codeverse.edu", "badpass")
        self.assertIsNone(bad_user)
        self.assertIsNotNone(err)

        # Invalid user
        unknown_user, err = auth_service.authenticate("nonexistent@domain.com", "anypass")
        self.assertIsNone(unknown_user)
        self.assertIsNotNone(err)

    def test_student_service(self):
        """Verify student service summary and queries."""
        summary = student_service.get_students_summary()
        self.assertIn("total_count", summary)
        self.assertIn("active_today", summary)
        self.assertIn("attendance_rate", summary)

        students = student_service.get_all_students()
        self.assertGreater(len(students), 0)

        student1 = student_service.get_student_by_id(1)
        self.assertIsNotNone(student1)
        # Verify the student record has a non-empty name (avoids hardcoded name that may differ in live DB)
        self.assertIn("name", student1)
        self.assertIsInstance(student1["name"], str)
        self.assertGreater(len(student1["name"]), 0)

    def test_lesson_service(self):
        """Verify lesson service summary and queries."""
        summary = lesson_service.get_lessons_summary()
        self.assertIn("published_count", summary)
        self.assertIn("training_hours", summary)

        lessons = lesson_service.get_all_lessons()
        self.assertGreater(len(lessons), 0)

        lesson1 = lesson_service.get_lesson_by_id(1)
        self.assertIsNotNone(lesson1)
        self.assertIn("title", lesson1)

    def test_homework_service(self):
        """Verify homework service summary and queries."""
        summary = homework_service.get_homework_summary()
        self.assertIn("active_count", summary)
        self.assertIn("pending_reviews", summary)

        homework = homework_service.get_all_homework()
        self.assertGreater(len(homework), 0)

    def test_exam_service(self):
        """Verify exam service summary, list, and question bank."""
        summary = exam_service.get_exams_summary()
        self.assertIn("active_exams", summary)
        self.assertIn("total_participants", summary)

        exams = exam_service.get_all_exams()
        self.assertGreater(len(exams), 0)

        questions = exam_service.get_question_bank()
        self.assertGreater(len(questions), 0)

    def test_result_service(self):
        """Verify results service."""
        summary = result_service.get_results_summary()
        self.assertIn("cohort_average", summary)
        self.assertIn("pass_rate", summary)

        results = result_service.get_all_results()
        self.assertGreater(len(results), 0)

    def test_file_service(self):
        """Verify file service."""
        summary = file_service.get_files_summary()
        self.assertIn("total_files", summary)

        files = file_service.get_all_files()
        self.assertGreater(len(files), 0)

    def test_notification_service(self):
        """Verify notification service."""
        admin_notifs = notification_service.get_all_notifications()
        self.assertGreater(len(admin_notifs), 0)

        student_notifs = notification_service.get_student_notifications()
        self.assertGreater(len(student_notifs), 0)

        unread_count = notification_service.get_unread_count()
        self.assertIsInstance(unread_count, int)


if __name__ == "__main__":
    unittest.main()
