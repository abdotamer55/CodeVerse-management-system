"""
Live Integration Test Suite for Supabase PostgreSQL
Verifies live reading and writing operations against all 10 schema tables.
"""
from datetime import date, datetime
import unittest
from database import check_connection, execute_query
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


class SupabaseLiveIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ok, host, tables, err = check_connection(force=True)
        if not ok:
            raise unittest.SkipTest(f"Supabase database unreachable: {err}")
        cls.tables = tables

    def test_01_all_ten_tables_exist_in_supabase(self):
        """Verify all 10 core tables are active in Supabase."""
        required = [
            "users", "students", "lessons", "homework", "submissions",
            "exams", "questions", "results", "files", "notifications"
        ]
        for tbl in required:
            self.assertIn(tbl, self.tables, f"Table {tbl} must exist in Supabase")

    def test_02_authentication_from_real_database(self):
        """Verify login queries users table and checks real password hashes."""
        # Query directly from DB
        user_row = execute_query(
            "SELECT email, role, full_name, password_hash FROM users WHERE email = %s;",
            ("student@codeverse.edu",)
        )
        self.assertEqual(len(user_row), 1)
        self.assertEqual(user_row[0]["role"], "student")

        # Authenticate via service
        user, err = auth_service.authenticate("student@codeverse.edu", "student123")
        self.assertIsNone(err)
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "student")
        self.assertEqual(user["id"], "b0000000-0000-0000-0000-000000000001")

        # Admin authenticate
        admin, err = auth_service.authenticate("admin@codeverse.edu", "admin123")
        self.assertIsNone(err)
        self.assertEqual(admin["role"], "admin")

    def test_03_students_read_from_real_database(self):
        """Verify students list and profiles read live from students table."""
        students = student_service.get_all_students()
        self.assertTrue(students)
        required_fields = {"id", "code", "name", "email", "track", "level", "status"}
        for student in students:
            self.assertTrue(required_fields.issubset(student.keys()))
            self.assertTrue(student["id"])
            self.assertTrue(student["code"])
            self.assertTrue(student["name"])
            self.assertTrue(student["email"])

        profile = student_service.get_student_by_id(students[0]["code"])
        self.assertIsNotNone(profile)
        self.assertEqual(profile["id"], students[0]["id"])
        self.assertEqual(profile["code"], students[0]["code"])

    def test_04_lessons_read_from_real_database(self):
        """Verify lessons curriculum reads live from lessons table."""
        lessons = lesson_service.get_all_lessons()
        self.assertTrue(lessons)
        required_fields = {"id", "code", "title", "track", "duration_minutes", "order_num"}
        for lesson in lessons:
            self.assertTrue(required_fields.issubset(lesson.keys()))
            self.assertIsNotNone(lesson["id"])
            self.assertTrue(lesson["code"])
            self.assertTrue(lesson["title"])
            self.assertGreaterEqual(lesson["duration_minutes"], 0)
            self.assertIsInstance(lesson.get("lesson_date"), (type(None), str, date, datetime))

        lesson = lesson_service.get_lesson_by_id(lessons[0]["id"])
        self.assertIsNotNone(lesson)
        self.assertEqual(lesson["id"], lessons[0]["id"])

    def test_05_homework_read_from_real_database(self):
        """Verify homework assignments read live from homework table."""
        homework = homework_service.get_all_homework()
        self.assertGreaterEqual(len(homework), 3)
        codes = [h["code"] for h in homework]
        self.assertIn("HW-118", codes)

    def test_06_exams_and_questions_read_from_real_database(self):
        """Verify exams and question bank read live from database."""
        exams = exam_service.get_all_exams()
        self.assertTrue(exams)
        self.assertTrue(all(exam.get("id") is not None and exam.get("title") for exam in exams))

        questions = exam_service.get_question_bank()
        self.assertTrue(questions)
        self.assertTrue(all(question.get("id") is not None and question.get("prompt") for question in questions))

        existing_exam_id = exams[0]["id"]
        exam = exam_service.get_exam_by_id(existing_exam_id)
        self.assertIsNotNone(exam)
        self.assertEqual(exam["id"], existing_exam_id)

        linked_rows = execute_query(
            "SELECT question_id, question_order, points FROM exam_questions WHERE exam_id=%s ORDER BY question_order, id;",
            (existing_exam_id,),
            fetch=True,
        ) or []
        if linked_rows:
            loaded_questions = exam.get("questions", [])
            self.assertEqual(
                [question["id"] for question in loaded_questions],
                [row["question_id"] for row in linked_rows],
            )
            self.assertEqual(
                [question.get("question_order") for question in loaded_questions],
                [row["question_order"] for row in linked_rows],
            )
        else:
            self.assertEqual(exam.get("questions", []), [])

    def test_07_results_read_from_real_database(self):
        """Verify results table records read live from database."""
        results = result_service.get_all_results()
        self.assertTrue(results)
        result_ids = [result.get("id") for result in results]
        self.assertEqual(len(result_ids), len(set(result_ids)))
        required_fields = {"id", "student_id", "student_code", "assessment", "score_percent", "status"}
        for result in results:
            self.assertTrue(required_fields.issubset(result.keys()))
            self.assertIsNotNone(result["id"])
            self.assertTrue(result["student_id"])
            self.assertTrue(result["student_code"])
            self.assertTrue(result["assessment"])
            self.assertGreaterEqual(float(result["score_percent"]), 0)
            self.assertLessEqual(float(result["score_percent"]), 100)
        summary = result_service.get_results_summary()
        self.assertIn("cohort_average", summary)
        self.assertIn("pass_rate", summary)

    def test_08_files_read_from_real_database(self):
        """Verify files metadata repository reads live from database."""
        files = file_service.get_all_files()
        self.assertGreaterEqual(len(files), 4)
        f_names = [f["file_name"] for f in files]
        self.assertIn("data-structures-algorithms-guide.pdf", f_names)

    def test_09_notifications_read_and_write_in_real_database(self):
        """Verify notifications table reads live and supports write operations."""
        initial_notifs = notification_service.get_all_notifications()
        self.assertGreaterEqual(len(initial_notifs), 3)

        # Test live write operation
        insert_sql = """
            INSERT INTO notifications (title, content, type, icon, is_read)
            VALUES (%s, %s, 'announcement', 'campaign', false)
            RETURNING id;
        """
        res = execute_query(insert_sql, ("اختبار كتابة الاتصال الحي", "رسالة تحقق من الكتابة في قاعدة بيانات سوبابيس"), fetch=True)
        self.assertTrue(len(res) > 0 and "id" in res[0])
        new_id = res[0]["id"]

        # Verify read back
        read_back = execute_query("SELECT id, title FROM notifications WHERE id = %s;", (new_id,), fetch=True)
        self.assertEqual(len(read_back), 1)
        self.assertEqual(read_back[0]["title"], "اختبار كتابة الاتصال الحي")

        # Clean up test row
        execute_query("DELETE FROM notifications WHERE id = %s;", (new_id,), fetch=False)

    def test_10_homework_submission_workflow(self):
        """Verify homework submission and grading write workflow against live database."""
        # 1. Get first homework
        hw_list = homework_service.get_all_homework()
        self.assertGreaterEqual(len(hw_list), 1)
        hw_id = hw_list[0]["id"]

        # 2. Get first student's real UUID
        student_row = execute_query(
            "SELECT id FROM students LIMIT 1;",
            fetch=True
        )
        self.assertTrue(len(student_row) >= 1)
        student_uuid = str(student_row[0]["id"])

        # 3. Submit homework (insert/update)
        repo = "https://github.com/test-user/integration-test-repo"
        sub = homework_service.submit_homework(
            homework_id=hw_id,
            student_id=student_uuid,
            repo_url=repo,
            code_snippet="# integration test",
        )
        self.assertIsNotNone(sub)
        self.assertEqual(sub["homework_id"], hw_id)
        submission_id = sub["id"]

        # 4. Verify submission is persisted in DB
        saved = homework_service.get_student_submission(hw_id, student_uuid)
        self.assertIsNotNone(saved)
        self.assertIn("repo_url", saved)

        # 5. Grade the submission
        graded = homework_service.grade_submission(
            submission_id=submission_id,
            grade="39 / 40",
            feedback="اختبار تكامل ناجح",
        )
        self.assertIsNotNone(graded)
        self.assertEqual(graded["grade"], "39 / 40")
        self.assertEqual(graded["status"], "graded")

        # 6. Get all submissions for this homework
        subs = homework_service.get_homework_submissions(homework_id=hw_id)
        self.assertGreaterEqual(len(subs), 1)


if __name__ == "__main__":
    unittest.main()
