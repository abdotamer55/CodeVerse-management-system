"""
Comprehensive Test Suite for CodeVerse LMS Flask Application
Tests route availability, authentication guards, role-based access, and template rendering.
"""
import unittest
from app import create_app

TEST_STUDENT_ID = "b0000000-0000-0000-0000-000000000001"


class CodeVerseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()

    def test_landing_page(self):
        """Verify root route returns landing page."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("كودفيرس".encode("utf-8"), res.data)
        self.assertIn("بيئة تعلم هندسة البرمجيات".encode("utf-8"), res.data)

    def test_login_page_get(self):
        """Verify login page renders correctly."""
        res = self.client.get("/login")
        self.assertEqual(res.status_code, 200)
        self.assertIn("تسجيل الدخول".encode("utf-8"), res.data)
        self.assertIn("identifier".encode("utf-8"), res.data)

    def test_unauthenticated_guards(self):
        """Unauthenticated requests to protected areas must redirect to /login."""
        admin_res = self.client.get("/admin/dashboard")
        self.assertEqual(admin_res.status_code, 302)
        self.assertIn("/login", admin_res.headers["Location"])

        student_res = self.client.get("/student/dashboard")
        self.assertEqual(student_res.status_code, 302)
        self.assertIn("/login", student_res.headers["Location"])

    def test_invalid_login(self):
        """Invalid credentials must return 401 and error message."""
        res = self.client.post("/login", data={
            "identifier": "wrong@codeverse.edu",
            "password": "wrongpassword",
        })
        self.assertEqual(res.status_code, 401)
        self.assertIn("غير صحيحة".encode("utf-8"), res.data)

    def test_student_authentication_flow(self):
        """Student login should establish session and redirect to /student/dashboard."""
        res = self.client.post("/login", data={
            "identifier": "student@codeverse.edu",
            "password": "student123",
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("لوحة الطالب".encode("utf-8"), res.data)
        self.assertIn("زياد حسام الدين".encode("utf-8"), res.data)

    def test_admin_authentication_flow(self):
        """Admin login should establish session and redirect to /admin/dashboard."""
        res = self.client.post("/login", data={
            "identifier": "admin@codeverse.edu",
            "password": "admin123",
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("لوحة التحكم".encode("utf-8"), res.data)
        self.assertIn("أستاذ د. طارق الحارثي".encode("utf-8"), res.data)

    def test_role_enforcement_student_blocked_from_admin(self):
        """Student session must not access admin endpoints."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = TEST_STUDENT_ID
            sess["role"] = "student"
            sess["user_name"] = "زياد حسام الدين"

        res = self.client.get("/admin/dashboard", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        # Should be redirected back to student dashboard with error
        self.assertIn("لوحة الطالب".encode("utf-8"), res.data)

    def test_all_admin_routes(self):
        """Verify all 11 Admin routes return 200 OK for admin session."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = "ad-001"
            sess["role"] = "admin"
            sess["user_name"] = "أستاذ د. طارق الحارثي"

        routes = [
            "/admin/dashboard",
            "/admin/students",
            "/admin/students/1",
            "/admin/lessons",
            "/admin/homework",
            "/admin/exams",
            "/admin/questions",
            "/admin/results",
            "/admin/files",
            "/admin/notifications",
            "/admin/settings",
        ]

        for r in routes:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Route {r} failed with status {res.status_code}")

    def test_all_student_routes(self):
        """Verify all 10 Student routes return 200 OK for student session."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = TEST_STUDENT_ID
            sess["role"] = "student"
            sess["user_name"] = "زياد حسام الدين"

        routes = [
            "/student/dashboard",
            "/student/lessons",
            "/student/lessons/1",
            "/student/homework",
            "/student/exams",
            "/student/exams/1",
            "/student/results",
            "/student/files",
            "/student/notifications",
            "/student/profile",
        ]

        for r in routes:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Route {r} failed with status {res.status_code}")

    def test_admin_exam_builder_exposes_question_bank(self):
        """Admin assessment builder should allow manual and bank-based question insertion."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = "ad-001"
            sess["role"] = "admin"
            sess["user_name"] = "أستاذ د. طارق الحارثي"

        res = self.client.get("/admin/exams/1/builder")
        self.assertEqual(res.status_code, 200)
        self.assertIn("بنك الأسئلة".encode("utf-8"), res.data)
        self.assertIn("إضافة من بنك الأسئلة".encode("utf-8"), res.data)
        self.assertIn("إضافة سؤال جديد".encode("utf-8"), res.data)

    def test_admin_exams_exposes_create_exam_button(self):
        """The admin exams page must expose the existing create-exam modal trigger."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = "ad-001"
            sess["role"] = "admin"
            sess["user_name"] = "أستاذ د. طارق الحارثي"

        res = self.client.get("/admin/exams")
        self.assertEqual(res.status_code, 200)
        self.assertIn("إنشاء امتحان جديد".encode("utf-8"), res.data)
        self.assertIn(b'data-open="#exam-modal"', res.data)

    def test_admin_exam_preview_looks_like_student_without_submit(self):
        """Admin preview exposes student questions but never posts a real attempt."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = "ad-001"
            sess["role"] = "admin"
            sess["user_name"] = "أستاذ د. طارق الحارثي"

        res = self.client.get("/admin/exams/1/preview")
        self.assertEqual(res.status_code, 200)
        self.assertIn("وضع معاينة الطالب".encode("utf-8"), res.data)
        self.assertIn("هذه المعاينة مطابقة لشكل الاختبار".encode("utf-8"), res.data)
        self.assertNotIn(b"/student/exams/1/submit", res.data)

    def test_logout_clears_session(self):
        """Logout must clear session and redirect to /login."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = "st-001"
            sess["role"] = "student"

        res = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("تسجيل الدخول".encode("utf-8"), res.data)

        # Trying to access protected route again must redirect
        res2 = self.client.get("/student/dashboard")
        self.assertEqual(res2.status_code, 302)

    def test_404_error_page(self):
        """Non-existent route must return 404 with Arabic error template."""
        res = self.client.get("/non-existent-page-url")
        self.assertEqual(res.status_code, 404)
        self.assertIn("الصفحة المطلوبة غير موجودة".encode("utf-8"), res.data)


if __name__ == "__main__":
    unittest.main()
