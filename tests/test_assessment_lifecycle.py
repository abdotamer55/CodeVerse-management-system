import time
import unittest

from database import check_connection, execute_query
from services import exam_service, homework_service


class AssessmentLifecycleIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ok, _, _, error = check_connection(force=True)
        if not ok:
            raise unittest.SkipTest(f"Live database unavailable: {error}")
        students = execute_query("SELECT id FROM students ORDER BY id LIMIT 1;", fetch=True) or []
        if not students:
            raise unittest.SkipTest("No student available for isolated assessment tests")
        cls.student_id = students[0]["id"]
        cls.prefix = f"TEST-LIFECYCLE-{int(time.time())}"

    def setUp(self):
        self.question_ids = []
        self.exam_ids = []
        self.homework_ids = []
        self.attempt_ids = []

    def tearDown(self):
        for attempt_id in self.attempt_ids:
            execute_query("DELETE FROM student_answers WHERE attempt_id=%s;", (attempt_id,), fetch=False)
            execute_query("DELETE FROM assessment_attempts WHERE id=%s;", (attempt_id,), fetch=False)
        for exam_id in self.exam_ids:
            execute_query("DELETE FROM exam_questions WHERE exam_id=%s;", (exam_id,), fetch=False)
        for homework_id in self.homework_ids:
            execute_query("DELETE FROM homework_questions WHERE homework_id=%s;", (homework_id,), fetch=False)
        for question_id in self.question_ids:
            execute_query("DELETE FROM questions WHERE id=%s;", (question_id,), fetch=False)
        for exam_id in self.exam_ids:
            execute_query("DELETE FROM exams WHERE id=%s;", (exam_id,), fetch=False)
        for homework_id in self.homework_ids:
            execute_query("DELETE FROM homework WHERE id=%s;", (homework_id,), fetch=False)

    def _create_questions(self):
        mcq = exam_service.create_question({
            "category": "mcq", "prompt": f"{self.prefix} MCQ",
            "options": ["A", "B", "C", "D"], "correct_index": 2, "points": 2,
        })
        boolean = exam_service.create_question({
            "category": "boolean", "prompt": f"{self.prefix} Boolean",
            "options": ["صح", "خطأ"], "correct_index": 1, "points": 1,
        })
        essay = exam_service.create_question({
            "category": "essay", "prompt": f"{self.prefix} Essay",
            "options": [], "points": 3,
        })
        self.question_ids.extend([mcq["id"], boolean["id"], essay["id"]])
        return mcq, boolean, essay

    def test_question_indexes_and_exam_lifecycle(self):
        mcq, boolean, essay = self._create_questions()
        stored = execute_query(
            "SELECT id, category, correct_index FROM questions WHERE id IN (%s,%s,%s) ORDER BY id;",
            (mcq["id"], boolean["id"], essay["id"]), fetch=True,
        )
        stored_by_id = {row["id"]: row for row in stored}
        self.assertEqual(stored_by_id[mcq["id"]]["correct_index"], 2)
        self.assertEqual(stored_by_id[boolean["id"]]["correct_index"], 1)
        self.assertIsNone(stored_by_id[essay["id"]]["correct_index"])

        exam = exam_service.create_exam({
            "title": f"{self.prefix} Exam", "duration_minutes": 10, "total_questions": 3,
        })
        self.exam_ids.append(exam["id"])
        questions = [
            {**mcq, "type": "mcq"},
            {**boolean, "type": "boolean"},
            {**essay, "type": "essay"},
        ]
        exam_service.save_exam_questions(exam["id"], questions)
        exam_service.publish_exam(exam["id"])

        started = exam_service.start_exam_attempt(exam["id"], self.student_id)
        self.attempt_ids.append(started["id"])
        self.assertEqual(started["status"], "in_progress")
        self.assertFalse(started["locked"])
        self.assertEqual(started["id"], exam_service.start_exam_attempt(exam["id"], self.student_id)["id"])
        self.assertEqual(execute_query("SELECT COUNT(*) AS c FROM student_answers WHERE attempt_id=%s;", (started["id"],), fetch=True)[0]["c"], 0)

        submitted = exam_service.submit_exam(exam["id"], self.student_id, {
            str(mcq["id"]): "2", str(boolean["id"]): "1", str(essay["id"]): "essay response",
        })
        self.assertEqual(submitted["id"], started["id"])
        self.assertEqual(submitted["status"], "submitted")
        self.assertTrue(submitted["locked"])
        self.assertEqual(submitted["score"], 3)
        self.assertEqual(submitted["total_score"], 6)
        answers = execute_query("SELECT * FROM student_answers WHERE attempt_id=%s;", (started["id"],), fetch=True)
        self.assertEqual(len(answers), 3)
        essay_answers = [row for row in answers if row["answer_type"] == "essay"]
        self.assertEqual(essay_answers[0]["marks_awarded"], 0)
        self.assertIsNone(essay_answers[0]["feedback"])
        with self.assertRaises(ValueError):
            exam_service.start_exam_attempt(exam["id"], self.student_id)
        with self.assertRaises(ValueError):
            exam_service.submit_exam(exam["id"], self.student_id, {})

    def test_expired_attempt_restarts_same_row_and_homework_lifecycle(self):
        question = exam_service.create_question({
            "category": "mcq", "prompt": f"{self.prefix} Homework MCQ",
            "options": ["A", "B", "C", "D"], "correct_index": 3, "points": 4,
        })
        self.question_ids.append(question["id"])
        homework = homework_service.create_homework({
            "code": f"{self.prefix}-HW", "title": f"{self.prefix} Homework",
            "due_date": "2099-01-01", "max_grade": 4,
        })
        self.homework_ids.append(homework["id"])
        homework_service.save_homework_questions(homework["id"], [{**question, "type": "mcq"}])
        homework_service.publish_homework(homework["id"])

        started = homework_service.start_homework_attempt(homework["id"], self.student_id)
        self.attempt_ids.append(started["id"])
        self.assertEqual(started["status"], "in_progress")
        self.assertEqual(execute_query("SELECT COUNT(*) AS c FROM student_answers WHERE attempt_id=%s;", (started["id"],), fetch=True)[0]["c"], 0)

        execute_query("UPDATE assessment_attempts SET status='expired', locked=TRUE WHERE id=%s;", (started["id"],), fetch=False)
        restarted = homework_service.start_homework_attempt(homework["id"], self.student_id)
        self.assertEqual(restarted["id"], started["id"])
        self.assertEqual(restarted["status"], "in_progress")

        submitted = homework_service.submit_homework_answers(homework["id"], self.student_id, {str(question["id"]): "3"})
        self.assertEqual(submitted["id"], started["id"])
        self.assertEqual(submitted["status"], "submitted")
        self.assertTrue(submitted["locked"])
        self.assertEqual(submitted["score"], 4)
        answer = execute_query("SELECT * FROM student_answers WHERE attempt_id=%s;", (started["id"],), fetch=True)[0]
        self.assertEqual(answer["attempt_id"], started["id"])
        self.assertEqual(answer["marks_awarded"], 4)
        with self.assertRaises(ValueError):
            homework_service.submit_homework_answers(homework["id"], self.student_id, {})


if __name__ == "__main__":
    unittest.main()
