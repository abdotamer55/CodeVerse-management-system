-- ==============================================================================
-- CodeVerse LMS: PostgreSQL / Supabase Seed Data Migration
-- Version: 002
-- Description: Realistic initial data for testing and local/cloud development
-- ==============================================================================

-- 1. SEED USERS
INSERT INTO users (id, username, email, password_hash, role, full_name, title, initials)
VALUES 
    ('a0000000-0000-0000-0000-000000000001', 'admin', 'admin@codeverse.edu', 'scrypt:32768:8:1$80qvz2tMRXDxUQOp$3c6d4467420c7f0ed9d40f6bca4f29ddc3ea21e424f2b54316e57165c1088e63f7da59294eee4bb29d494886ecceec0d5ec7b40582bc98a5e1fec923be540019', 'admin', 'أستاذ د. طارق الحارثي', 'مشرف المنصة الأكاديمية', 'ط.ح'),
    ('b0000000-0000-0000-0000-000000000001', 'ziad', 'student@codeverse.edu', 'scrypt:32768:8:1$8FDinmbiTkKWq1mQ$05ec5e3351de833ebd0e38771dfaf6ee57ee85eab34713e933c8843b9f5ab4cf653d7210f69869d34de52e35d8ba0282d014eecd58079a65dac8f9ec34c5046c', 'student', 'زياد حسام الدين', 'طالب مسار هندسة البرمجيات', 'ز.ح'),
    ('b0000000-0000-0000-0000-000000000002', 'sara', 'sara.m@codeverse.edu', 'scrypt:32768:8:1$8FDinmbiTkKWq1mQ$05ec5e3351de833ebd0e38771dfaf6ee57ee85eab34713e933c8843b9f5ab4cf653d7210f69869d34de52e35d8ba0282d014eecd58079a65dac8f9ec34c5046c', 'student', 'سارة طارق المنصور', 'طالبة تطوير واجهات React', 'س.م'),
    ('b0000000-0000-0000-0000-000000000003', 'omar', 'omar.d@codeverse.edu', 'scrypt:32768:8:1$8FDinmbiTkKWq1mQ$05ec5e3351de833ebd0e38771dfaf6ee57ee85eab34713e933c8843b9f5ab4cf653d7210f69869d34de52e35d8ba0282d014eecd58079a65dac8f9ec34c5046c', 'student', 'عمر خالد الدوسري', 'طالب تطوير خوادم Node.js', 'ع.د')
ON CONFLICT (id) DO NOTHING;

-- 2. SEED STUDENTS
INSERT INTO students (id, student_code, track, level, overall_grade, status, status_label, is_honor, completed_lessons, total_lessons, completed_homework, total_homework, last_active)
VALUES 
    ('b0000000-0000-0000-0000-000000000001', '#ST-2024-089', 'هندسة برمجيات الأنظمة', 'المستوى المتقدم L3', 98.40, 'online', 'متصل الآن', TRUE, 27, 28, 14, 14, 'قبل دقيقتين'),
    ('b0000000-0000-0000-0000-000000000002', '#ST-2024-114', 'تطوير واجهات React', 'المستوى الثاني', 93.00, 'active', 'نشط ومنتظم', FALSE, 24, 28, 13, 14, 'اليوم 04:15 م'),
    ('b0000000-0000-0000-0000-000000000003', '#ST-2024-032', 'تطوير الخوادم Node.js', 'المستوى الأول', 64.20, 'risk', 'متأخر دراسياً', FALSE, 14, 28, 6, 14, 'قبل 3 أيام')
ON CONFLICT (id) DO NOTHING;

-- 3. SEED LESSONS
INSERT INTO lessons (id, code, title, short_title, track, track_slug, duration_minutes, duration_text, attendees, progress, is_live, live_time, instructor, description, topics, pdf_name, repo_name)
VALUES 
    (1, 'LES-014', 'معمارية الـ Microservices وتدفق الرسائل عبر NestJS & RabbitMQ', 'معمارية الـ Microservices وRabbitMQ', 'هندسة النظم الخلفية (Backend)', 'backend', 95, 'ساعة و 35 دقيقة', 184, 70, TRUE, 'اليوم 07:00 م', 'د. طارق الحارثي', 'دراسة تفصيلية لبناء بيئات الخدمات المصغرة المستقلة، أنماط معالجة الأحداث غير المتزامنة، وإعداد وسيط الرسائل الموزع RabbitMQ في إنتاجية عالية.', '["مفهوم Event-Driven Architecture", "تهيئة بروتوكول AMQP في NestJS", "إدارة رسائل الفشل ومستودعات Dead Letter Exchange", "تطبيق عملي لمزامنة بيانات الدفع والطلبات"]'::jsonb, 'microservices-rabbitmq-guide.pdf', 'cv-microservices-starter'),
    (2, 'LES-022', 'فهرسة قواعد البيانات واستراتيجيات تسريع استعلامات الـ SQL المركبة', 'فهرسة قواعد البيانات واستعلامات SQL', 'هندسة النظم الخلفية (Backend)', 'backend', 80, 'ساعة و 20 دقيقة', 142, 100, FALSE, 'مسجلة بالكامل', 'م. ريان السعيد', 'فهم خوارزميات B-Tree و Hash Indexes في محركات PostgreSQL، قراءة خطة التنفيذ EXPLAIN ANALYZE وتحسين استعلامات الربط JOIN المعقدة.', '["كيف تفكر محركات التخزين عند قراءة الأقراص", "أنواع الفهارس المركبة Composite Indexes", "تحليل كلفة الاستعلام Cost Metrics في Postgres", "تمارين عملية لتخفيض زمن الاستعلام من 3 ثوانٍ إلى 12ms"]'::jsonb, 'postgres-indexing-mastery.pdf', 'sql-performance-lab'),
    (3, 'LES-030', 'أسرار React 19: بنية Server Actions ودورة حياة مكونات RSC', 'أسرار React 19 و Server Components', 'تطوير الواجهات المتقدمة (Frontend)', 'frontend', 110, 'ساعة و 50 دقيقة', 196, 40, FALSE, 'غداً 08:30 م', 'م. أروى الحمدان', 'التحول الجذري في نموذج عتاد React: التمييز بين مكونات الخادم ومكونات العميل، استدعاء الدوال الخلفية مباشرة دون كتابة نقاط REST يدوية.', '["معمارية React Server Components", "معالجة النماذج عبر useActionState", "Optimistic Updates وتجربة المستخدم الفورية", "إدارة الكاش و revalidatePath"]'::jsonb, 'react19-server-actions.pdf', 'nextjs15-react19-playground')
ON CONFLICT (id) DO NOTHING;

-- 4. SEED HOMEWORK
INSERT INTO homework (id, code, title, short_title, track, lesson_id, instructions, due_date, status, status_label, submissions_count, total_students, auto_tests_pass_rate, max_grade)
VALUES
    (1, 'HW-118', 'مشروع بناء REST API عالي الاعتمادية بنظام التخزين المؤقت Redis', 'مشروع REST API و Redis', 'هندسة النظم الخلفية (Backend)', 1, 'بناء خادم معتمد على بنية Repository مع تفعيل استراتيجية Cache Aside باستخدام Redis.', '18 سبتمبر 2024', 'grading', 'تصحيح جارٍ', 312, 348, '89.4%', 40),
    (2, 'HW-121', 'حل معضلات البرمجة الديناميكية: خوارزمية حقيبة الظهر (0/1 Knapsack)', 'خوارزميات البرمجة الديناميكية (DP)', 'خوارزميات وهياكل البيانات', 1, 'حل مسألة حقيبة الظهر عبر تقنية Memoization و Bottom-Up Tabulation.', '21 سبتمبر 2024', 'open', 'مفتوح للتسليم', 280, 348, '76.2%', 40),
    (3, 'HW-109', 'تطبيق إدارة الحالة المتكامل باستخدام Zustand و React Query', 'إدارة الحالة بـ Zustand', 'تطوير واجهات React', 3, 'إدارة استهلاك واجهات برمجة التطبيقات مع التخزين المؤقت وتحديث البيانات تلقائياً.', '10 سبتمبر 2024', 'completed', 'مكتمل ومرصود', 340, 348, '95.1%', 40)
ON CONFLICT (id) DO NOTHING;

-- 5. SEED EXAMS
INSERT INTO exams (id, title, short_title, duration_minutes, duration_seconds, total_questions, scheduled_date, status, status_label, progress)
VALUES
    (1, 'اختبار هياكل البيانات والخوارزميات المتقدمة (Midterm Exam)', 'اختبار هياكل البيانات', 90, 5400, 4, '16 سبتمبر 2024', 'active', 'جارٍ الآن', 55),
    (2, 'الاختبار النهائي الشامل: هندسة الويب وتطبيقات React 19', 'نهائي مسار الويب React 19', 120, 7200, 40, '22 سبتمبر 2024 · 08:00 م', 'scheduled', 'مجدول', 0)
ON CONFLICT (id) DO NOTHING;

-- 6. SEED QUESTIONS
INSERT INTO questions (id, exam_id, category, difficulty, difficulty_badge, track, prompt, options, correct_index, correct_answer, answer_preview)
VALUES
    (1, 1, 'mcq', 'متوسط', 'badge-info', 'الخوارزميات', 'ما هو أفضل تعقيد زمني ممكن لخوارزمية البحث الثنائي (Binary Search) على مصفوفة مرتبة؟', '["O(n)", "O(log n)", "O(n log n)", "O(1)"]'::jsonb, 1, 'O(log n)', 'O(log n)'),
    (2, 1, 'mcq', 'مبتدئ', 'badge-info', 'هياكل البيانات', 'أي هيكل بيانات يعتمد مبدأ LIFO (Last In, First Out) في إدارة عناصره؟', '["الطابور Queue", "المكدس Stack", "الشجرة Tree", "الرسم البياني Graph"]'::jsonb, 1, 'المكدس Stack', 'المكدس Stack'),
    (3, 1, 'mcq', 'متوسط', 'badge-info', 'هياكل البيانات', 'تتميز جداول الهاش (Hash Tables) بقدرتها الفائقة على تحقيق زمن بحث بمتوسط:', '["O(n)", "O(log n)", "O(1)", "O(n²)"]'::jsonb, 2, 'O(1)', 'O(1)'),
    (4, 1, 'mcq', 'متقدم', 'badge-warn', 'معالجة الذاكرة', 'تتفوق القائمة المرتبطة (Linked List) على المصفوفة ذات الحجم الثابت في:', '["الوصول المباشر والفوري لأي عنصر برقم الفهرس", "مرونة إدراج وحذف العناصر دون الحاجة لإزاحة الذاكرة", "استهلاك أقل لحجم الذاكرة لكل عنصر", "دعم الترتيب الثنائي التلقائي"]'::jsonb, 1, 'مرونة إدراج وحذف العناصر دون الحاجة لإزاحة الذاكرة', 'مرونة إدراج وحذف العناصر دون الحاجة لإزاحة الذاكرة'),
    (101, NULL, 'mcq', 'متوسط', 'badge-info', 'الخوارزميات', 'ما تعقيد البحث الثنائي في أسوأ الحالات (Worst-case)؟', '["O(1)", "O(n)", "O(log n)", "O(n²)"]'::jsonb, 2, 'O(log n)', 'O(log n)'),
    (102, NULL, 'mcq', 'متقدم', 'badge-warn', 'هياكل البيانات', 'ما ناتج استدعاء دالة RecursionTrace() في الشجرة الثنائية الموضحة؟', '[]'::jsonb, 0, 'Post-order Traversal: [4, 5, 2, 3, 1]', 'Post-order Traversal: [4, 5, 2, 3, 1]'),
    (103, NULL, 'code', 'تحدي برمجي', 'badge-danger', 'معالجة الذاكرة', 'اكتب دالة بلغة JavaScript لعكس قائمة أحادية الارتباط In-place:', '[]'::jsonb, 0, 'function reverseList(head) { ... }', 'function reverseList(head) { let prev = null, curr = head; while (curr) { const next = curr.next; curr.next = prev; prev = curr; curr = next; } return prev; }')
ON CONFLICT (id) DO NOTHING;

-- 7. SEED RESULTS
INSERT INTO results (id, student_id, student_name, student_code, exam_id, assessment, score_percent, score_display, date, status, grade_badge, grade_label)
VALUES
    (1, 'b0000000-0000-0000-0000-000000000001', 'زياد حسام الدين', '#ST-2024-089', 1, 'اختبار هياكل البيانات والخوارزميات', 96.00, '96%', '10 سبتمبر 2024', 'passed', 'badge-success', 'ممتاز ومتميز'),
    (2, 'b0000000-0000-0000-0000-000000000002', 'سارة طارق المنصور', '#ST-2024-114', 1, 'اختبار هياكل البيانات والخوارزميات', 91.00, '91%', '10 سبتمبر 2024', 'passed', 'badge-success', 'جيد جداً مرتفع'),
    (3, 'b0000000-0000-0000-0000-000000000003', 'عمر خالد الدوسري', '#ST-2024-032', 1, 'اختبار هياكل البيانات والخوارزميات', 58.00, '58%', '10 سبتمبر 2024', 'repeat', 'badge-danger', 'فرصة إعادة'),
    (4, 'b0000000-0000-0000-0000-000000000001', 'زياد حسام الدين', '#ST-2024-089', NULL, 'مشروع REST API وتخزين Redis', 95.00, '38 / 40', '12 سبتمبر 2024', 'passed', 'badge-success', 'ممتاز')
ON CONFLICT (id) DO NOTHING;

-- 8. SEED FILES
INSERT INTO files (id, name, file_name, category, icon, size_display, downloads_count, updated_at, description)
VALUES
    (1, 'مذكرة هياكل البيانات والخوارزميات الشاملة.pdf', 'data-structures-algorithms-guide.pdf', 'pdf', 'picture_as_pdf', '2.4 MB', 640, '14 سبتمبر 2024', 'مرجع مكتوب باللغة العربية يشمل مفاهيم Big-O، القوائم المرتبطة، والأشجار الثنائية.'),
    (2, 'starter-rest-api-redis.zip', 'starter-rest-api-redis.zip', 'zip', 'folder_zip', '1.1 MB', 428, '12 سبتمبر 2024', 'كود البداية الجاهز لمشروع بناء خادم REST API مع إعدادات Docker Compose لـ Redis.'),
    (3, 'معمارية الخدمات المصغرة وطوابير RabbitMQ.pdf', 'microservices-rabbitmq-slides.pdf', 'pdf', 'picture_as_pdf', '4.6 MB', 310, '08 سبتمبر 2024', 'شرائح العرض التقديمي لمعمل البث الحي رقم 14.'),
    (4, 'react19-server-actions-cheatsheet.pdf', 'react19-server-actions-cheatsheet.pdf', 'pdf', 'picture_as_pdf', '850 KB', 512, '05 سبتمبر 2024', 'ورقة مرجعية سريعة لأهم دوال وهوكس React 19.')
ON CONFLICT (id) DO NOTHING;

-- 9. SEED NOTIFICATIONS
INSERT INTO notifications (id, user_id, title, content, type, icon, is_read)
VALUES
    (1, NULL, 'تذكير أكاديمي: موعد الاختبار النصفي لهياكل البيانات والخوارزميات', 'أُرسل إلى جميع طلاب مسار هندسة برمجيات الأنظمة (348 طالباً)', 'exam', 'campaign', FALSE),
    (2, NULL, 'فتح باب تسليم التكليف البرمجي: مشروع REST API و Redis', 'الموعد النهائي للتسليم: 18 سبتمبر 2024', 'assignment', 'assignment', TRUE),
    (3, NULL, 'رابط معمل البث الحي المباشر #14: حل مسائل الـ Dynamic Programming', 'يبدأ البث اليوم في تمام الساعة 07:00 مساءً مع د. طارق الحارثي', 'live', 'live_tv', TRUE)
ON CONFLICT (id) DO NOTHING;
