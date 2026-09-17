
# API.md — Routes & Endpoint Specification

## 1. Authentication Endpoints (`auth_bp`)

| Method | Route | Description | Auth Required | Role | Service Backing |
|---|---|---|---|---|---|
| GET | `/login` | Render login page | No | Public | — |
| POST | `/login` | Authenticate user & set session | No | Public | `auth_service.authenticate` |
| GET | `/logout` | Clear session & redirect to login | Yes | Any | — |

---

## 2. Public / Landing (`main`)

| Method | Route | Description | Auth Required | Role | Service Backing |
|---|---|---|---|---|---|
| GET | `/` | Platform landing & gateway | No | Public | — |

---

## 3. Admin / Staff Portal (`admin_bp`, prefix `/admin`)

| Method | Route | Description | Auth Required | Role | Service Backing |
|---|---|---|---|---|---|
| GET | `/admin` | Redirects to `/admin/dashboard` | Yes | admin | — |
| GET | `/admin/dashboard` | Admin dashboard overview | Yes | admin | `student_service` |
| GET | `/admin/students` | Students management & directory | Yes | admin | `student_service` |
| GET | `/admin/students/<int:student_id>` | Detailed student profile | Yes | admin | `student_service` |
| GET | `/admin/lessons` | Lesson & course management | Yes | admin | `lesson_service` |
| GET | `/admin/homework` | Assignment review & grading | Yes | admin | `homework_service` |
| GET | `/admin/exams` | Exam management & rooms | Yes | admin | `exam_service` |
| GET | `/admin/questions` | Question bank repository | Yes | admin | `exam_service` |
| GET | `/admin/results` | Academic grades & analytics | Yes | admin | `result_service` |
| GET | `/admin/files` | Cloud files & library | Yes | admin | `file_service` |
| GET | `/admin/notifications` | Announcements & broadcasts | Yes | admin | `notification_service` |
| GET | `/admin/settings` | General platform configuration | Yes | admin | — |

---

## 4. Student Portal (`student_bp`, prefix `/student`)

| Method | Route | Description | Auth Required | Role | Service Backing |
|---|---|---|---|---|---|
| GET | `/student` | Redirects to `/student/dashboard` | Yes | student | — |
| GET | `/student/dashboard` | Student learning dashboard | Yes | student | `student_service` |
| GET | `/student/lessons` | List of enrolled lessons | Yes | student | `lesson_service` |
| GET | `/student/lessons/<int:lesson_id>` | Interactive lesson view | Yes | student | `lesson_service` |
| GET | `/student/homework` | Homework tasks & submissions | Yes | student | `homework_service` |
| GET | `/student/exams` | List of available exams | Yes | student | `exam_service` |
| GET | `/student/exams/<int:exam_id>` | Interactive timed exam room | Yes | student | `exam_service` |
| GET | `/student/results` | Student academic results | Yes | student | `result_service` |
| GET | `/student/files` | Download course files & notes | Yes | student | `file_service` |
| GET | `/student/notifications` | Personal & general notifications | Yes | student | `notification_service` |
| GET | `/student/profile` | Student profile & settings | Yes | student | `student_service` |
