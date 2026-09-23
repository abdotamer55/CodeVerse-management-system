# One-off static page builder. Not part of runtime.
from pathlib import Path

ROOT = Path(__file__).resolve().parent

HEAD = """<!DOCTYPE html>
<html class="dark" dir="rtl" lang="ar">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} | كودفيرس</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&family=Tajawal:wght@400;500;700&family=Inter:wght@400;500;600;700;800&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet" />
  <link rel="stylesheet" href="{root}css/variables.css" />
  <link rel="stylesheet" href="{root}css/global.css" />
  <link rel="stylesheet" href="{root}css/components.css" />
  <link rel="stylesheet" href="{root}css/layout.css" />
  <link rel="stylesheet" href="{root}css/pages.css" />
  <link rel="stylesheet" href="{root}css/responsive.css" />
</head>
"""

SCRIPTS = """
  <script src="{root}js/components.js"></script>
  <script src="{root}js/navigation.js"></script>
  <script src="{root}js/ui.js"></script>
  <script src="{root}js/forms.js"></script>
  <script src="{root}js/exams.js"></script>
  <script src="{root}js/main.js"></script>
"""


def shell_page(path, title, role, page, root, content, extra=""):
    html = HEAD.format(title=title, root=root)
    html += f'<body data-root="{root}" data-role="{role}" data-page="{page}">\n'
    html += '  <div id="sidebar-root"></div>\n'
    html += '  <div class="app-frame">\n'
    html += '    <div id="navbar-root"></div>\n'
    html += '    <main class="page stack">\n'
    html += content
    html += "\n    </main>\n"
    html += '    <div id="footer-root"></div>\n'
    html += "  </div>\n"
    html += extra
    html += SCRIPTS.format(root=root)
    html += "</body>\n</html>\n"
    (ROOT / path).write_text(html, encoding="utf-8")


def bare_page(path, title, root, body_attrs, content):
    html = HEAD.format(title=title, root=root)
    html += f"<body {body_attrs}>\n"
    html += content
    html += SCRIPTS.format(root=root)
    html += "</body>\n</html>\n"
    (ROOT / path).write_text(html, encoding="utf-8")


stat = """
<div class="card stat-card">
  <div class="between">
    <div class="stat-icon {tone}"><span class="material-symbols-outlined">{icon}</span></div>
    {badge}
  </div>
  <div>
    <span class="label-sm muted">{label}</span>
    <div class="row" style="align-items:baseline;margin-top:6px">
      <span class="display-hero">{value}</span>
      <span class="label-md muted">{unit}</span>
    </div>
  </div>
  <div class="stat-foot"><span>{foot_l}</span><strong>{foot_r}</strong></div>
</div>
"""


def S(tone, icon, badge, label, value, unit, foot_l, foot_r):
    return stat.format(tone=tone, icon=icon, badge=badge, label=label, value=value, unit=unit, foot_l=foot_l, foot_r=foot_r)


# ---------- public ----------
bare_page(
    "index.html",
    "منصة كودفيرس",
    "./",
    'data-root="./" class="auth-body"',
    """
<div class="gateway-card stack">
  <div class="card card-lg" style="position:relative">
    <div class="glow glow-a"></div>
    <div class="glow glow-b"></div>
    <div class="row" style="margin-bottom:1rem">
      <img src="./assets/icons/logo.svg" alt="كودفيرس" style="height:40px" />
    </div>
    <span class="pill"><span class="dot pulse"></span> النظام متصل 99.9%</span>
    <h1 class="headline-xl" style="margin-top:12px">كودفيرس — بيئة تعليم البرمجيات الاحترافية</h1>
    <p class="body-lg muted">منصة عربية RTL لإدارة الحصص، الواجبات، الامتحانات التفاعلية، وملفات المسار الأكاديمي بواجهة داكنة احترافية.</p>
    <div class="hero-actions" style="margin-top:1.5rem">
      <a class="btn btn-primary" href="./pages/login.html"><span class="material-symbols-outlined">login</span> تسجيل الدخول للمنصة</a>
      <a class="btn btn-secondary" href="./pages/landing.html">استعراض المنصة</a>
    </div>
  </div>
  <div class="grid-2">
    <a class="card card-hover" href="./pages/login.html">
      <div class="stat-icon green"><span class="material-symbols-outlined">school</span></div>
      <h2 class="headline-sm" style="margin-top:12px">بوابة الطالب</h2>
      <p class="body-sm muted">متابعة الحصص، تسليم التكاليف، دخول الاختبارات ورصد النتائج.</p>
    </a>
    <a class="card card-hover" href="./pages/login.html">
      <div class="stat-icon blue"><span class="material-symbols-outlined">verified_user</span></div>
      <h2 class="headline-sm" style="margin-top:12px">بوابة المعلم والإدارة</h2>
      <p class="body-sm muted">إدارة الطلاب، المحتوى، التصحيح، بنك الأسئلة والتقارير.</p>
    </a>
  </div>
</div>
""",
)

bare_page(
    "pages/landing.html",
    "المنصة التعليمية",
    "../",
    'data-root="../"',
    """
<header class="landing-nav">
  <div class="row">
    <img src="../assets/icons/logo.svg" alt="كودفيرس" style="height:36px" />
  </div>
  <div class="wrap">
    <a class="btn btn-ghost" href="../pages/login.html">تسجيل الدخول</a>
    <a class="btn btn-primary" href="../pages/login.html">ابدأ الآن</a>
  </div>
</header>
<section class="landing-hero stack">
  <div class="page-hero">
    <div class="glow glow-a"></div>
    <span class="badge badge-info">الفصل الدراسي الأول 2024 / 2025</span>
    <h1 class="headline-xl" style="margin-top:12px">بيئة تعلم هندسة البرمجيات بواجهة عربية احترافية</h1>
    <p class="body-lg muted" style="max-width:48rem">رصد فوري للنشاط الصفي، اختبارات مؤقتة، بنك أسئلة، ومكتبة ملفات سحابية — بنفس الهوية البصرية الداكنة لتصاميم كودفيرس.</p>
    <div class="hero-actions" style="margin-top:1rem">
      <a class="btn btn-primary" href="./login.html">دخول تجريبي</a>
      <a class="btn btn-secondary" href="../admin/dashboard.html">معاينة لوحة الإدارة</a>
      <a class="btn btn-secondary" href="../student/dashboard.html">معاينة لوحة الطالب</a>
    </div>
  </div>
  <div class="landing-grid">
    <article class="card"><div class="stat-icon blue"><span class="material-symbols-outlined">play_lesson</span></div><h3 class="headline-sm" style="margin-top:12px">حصص ومسارات</h3><p class="body-sm muted">محاضرات مسجلة ومباشرة مع مذكرات PDF وروابط فيديو.</p></article>
    <article class="card"><div class="stat-icon amber"><span class="material-symbols-outlined">quiz</span></div><h3 class="headline-sm" style="margin-top:12px">امتحانات ذكية</h3><p class="body-sm muted">مؤقت صارم، تنقل بين الأسئلة، ومعاينة واجهة الطالب.</p></article>
    <article class="card"><div class="stat-icon green"><span class="material-symbols-outlined">insights</span></div><h3 class="headline-sm" style="margin-top:12px">نتائج وتقارير</h3><p class="body-sm muted">معدلات الإنجاز، لوحة الشرف، وتنبيهات الدعم الأكاديمي.</p></article>
  </div>
</section>
""",
)

bare_page(
    "pages/login.html",
    "تسجيل الدخول",
    "../",
    'data-root="../" data-login-role="student" class="auth-body"',
    """
<main class="login-card">
  <div class="login-inner">
    <div class="glow glow-a"></div>
    <div class="glow glow-b"></div>
    <div class="between" style="position:relative;z-index:1;margin-bottom:1rem">
      <span class="pill"><span class="dot pulse"></span> النظام متصل 99.9%</span>
      <button class="btn btn-ghost label-sm" type="button"><span class="material-symbols-outlined">language</span> English</button>
    </div>
    <div class="brand-lockup" style="position:relative;z-index:1">
      <div class="brand-icon"><span class="material-symbols-outlined icon-fill" style="font-size:32px">terminal</span></div>
      <div class="row"><span class="headline-sm">كودفيرس</span><span class="badge badge-info">النسخة الخاصة</span></div>
      <h1 class="headline-md">تسجيل الدخول إلى المنصة</h1>
      <p class="body-sm muted">أدخل بيانات حسابك المعتمدة للوصول إلى بيئتك التعليمية التفاعلية</p>
    </div>
    <div class="role-tabs" style="position:relative;z-index:1">
      <button class="role-btn is-active" type="button" data-role="student"><span class="material-symbols-outlined">school</span> طالب (Student)</button>
      <button class="role-btn" type="button" data-role="staff"><span class="material-symbols-outlined">verified_user</span> معلم / إدارة (Admin)</button>
    </div>
    <form id="login-form" class="stack" style="gap:1rem;position:relative;z-index:1;margin-top:1.25rem">
      <div class="field">
        <label for="identifier">اسم المستخدم أو البريد الأكاديمي</label>
        <div class="input-wrap">
          <span class="leading-icon material-symbols-outlined">alternate_email</span>
          <input class="input" id="identifier" required placeholder="مثال: student@codeverse.edu أو الاسم التعريفي" style="padding-right:2.5rem" />
        </div>
      </div>
      <div class="field">
        <div class="between"><label for="password">كلمة المرور الأمنية</label><a class="label-sm accent" href="#">نسيت كلمة المرور؟</a></div>
        <div class="input-wrap">
          <span class="leading-icon material-symbols-outlined">lock</span>
          <input class="input" id="password" type="password" required placeholder="••••••••••••" style="padding:0.65rem 2.5rem" />
          <button class="trailing-btn" type="button" data-password-toggle aria-label="إظهار كلمة المرور"><span class="material-symbols-outlined" id="password-toggle-icon">visibility_off</span></button>
        </div>
      </div>
      <div class="between">
        <label class="row"><input type="checkbox" /> <span class="label-md muted">تذكرني في هذا الجهاز الموثوق</span></label>
        <span class="label-sm success row"><span class="material-symbols-outlined" style="font-size:14px">shield</span> اتصال مشفر</span>
      </div>
      <button class="btn btn-primary" type="submit" style="width:100%;padding:0.85rem">تسجيل الدخول إلى حسابي <span class="material-symbols-outlined">arrow_back</span></button>
    </form>
    <div style="margin-top:1.5rem;position:relative;z-index:1">
      <p class="label-sm muted" style="text-align:center;margin-bottom:8px">جلسات تجريبية سريعة للمعاينة</p>
      <div class="demo-grid">
        <button class="btn btn-secondary" type="button" data-demo="student"><span class="material-symbols-outlined">code</span> دخول تجريبي كطالب</button>
        <button class="btn btn-secondary" type="button" data-demo="staff"><span class="material-symbols-outlined">dashboard_customize</span> دخول كمعلم / مسؤول</button>
      </div>
      <div class="alert" style="margin-top:12px"><span class="material-symbols-outlined">gavel</span><p>هذه المنصة خاصة بالطلاب والمعلمين المسجلين رسمياً. الواجهة الحالية للعرض فقط دون مصادقة خلفية.</p></div>
    </div>
  </div>
</main>
""",
)

# ---------- admin dashboard ----------
shell_page(
    "admin/dashboard.html",
    "لوحة التحكم",
    "admin",
    "dashboard",
    "../",
    f"""
<section class="page-hero">
  <div class="glow glow-a"></div>
  <div class="between" style="flex-wrap:wrap;position:relative;z-index:1">
    <div class="stack" style="gap:8px">
      <div class="wrap">
        <span class="pill"><span class="dot pulse"></span> الفصل الدراسي الأول 2024 / 2025</span>
        <span class="badge badge-neutral ltr">TERM-ID: CV-FA24-MTR</span>
      </div>
      <h1 class="headline-lg">أهلاً بك، أستاذ د. طارق الحارثي 👋</h1>
      <p class="body-md muted">لوحة المتابعة الإدارية والأكاديمية الموحدة لمنصة كودفيرس | رصد فوري للنشاط الصفي، تصحيح الاختبارات التفاعلية، وتحليل مستويات الإتقان البرمجي للطلاب.</p>
    </div>
    <div class="hero-actions">
      <a class="btn btn-primary" href="lessons.html"><span class="material-symbols-outlined">add_circle</span> إضافة حصة جديدة</a>
      <a class="btn btn-secondary" href="exams.html"><span class="material-symbols-outlined">quiz</span> إنشاء اختبار جديد</a>
      <a class="btn btn-ghost" href="files.html"><span class="material-symbols-outlined">upload_file</span> رفع مذكرة/ملف</a>
    </div>
  </div>
</section>
<section class="grid-4">
{S("blue","groups",'<span class="badge badge-success"><span class="material-symbols-outlined" style="font-size:14px">trending_up</span> +12 هذا الأسبوع</span>',"إجمالي الطلاب المسجلين","348","طالباً معتمداً","نسبة السعة المقعدية","87% من إجمالي السيرفر")}
{S("green","bolt",'<span class="badge badge-success">92.4% تفاعل نشط</span>',"الطلاب النشطون حالياً","312","متواجد اليوم","في المختبر البرمجي","64 جلسة فورية")}
{S("amber","video_library",'<span class="badge badge-warn">4 مسارات تدريبية</span>',"إجمالي الحصص المنشورة","84","حصة ومحاضرة","إجمالي الساعات","142 ساعة مسجلة")}
{S("blue","assignment_turned_in",'<span class="badge badge-info">معدل عام: 87.6%</span>',"الامتحانات والواجبات المنفذة","32","تقييماً رسمياً","واجبات قيد الرصد",'<span class="danger">14 تسليم جديد</span>')}
</section>
<div class="grid-12">
  <section class="card card-lg span-8">
    <h2 class="headline-sm">معدل الحضور وتسليم التكاليف البرمجية</h2>
    <p class="body-sm muted">مقارنة نسب حضور المحاضرات الرقمية ومعدل تسليم كود الواجبات خلال الأسابيع الستة السابقة</p>
    <div class="chart-bars">
      {''.join(f'<div class="chart-col"><div class="bars"><span class="bar primary" style="height:{a}%"></span><span class="bar secondary" style="height:{b}%"></span></div><span class="label-sm muted">أ{i}</span></div>' for i,(a,b) in enumerate([(62,48),(70,55),(66,72),(80,68),(74,81),(88,79)],1))}
    </div>
  </section>
  <section class="card card-lg span-4">
    <span class="badge badge-info">مباشر اليوم 07:00 م</span>
    <h2 class="headline-sm" style="margin:8px 0">البث القادم</h2>
    <div class="live-card" style="position:relative;border-radius:12px;overflow:hidden;background:var(--surface-lowest)">
      <div class="video-stage" style="min-height:140px">
        <span class="material-symbols-outlined" style="font-size:40px;color:var(--primary)">live_tv</span>
        <strong>معمل الخوارزميات الحي #14</strong>
        <p class="body-sm muted">حل معضلات البرمجة الديناميكية Dynamic Programming</p>
      </div>
    </div>
    <div class="between" style="margin-top:12px">
      <span class="body-sm muted">المسجلون في البث: 184 طالب</span>
      <button class="btn btn-primary" type="button">تجهيز الغرفة</button>
    </div>
  </section>
</div>
<section class="card card-lg">
  <div class="toolbar">
    <div>
      <h2 class="headline-md">أحدث الطلاب المنضمين والتسجيلات الأكاديمية</h2>
      <p class="body-sm muted">متابعة مستمرة لمعدل تقدم الطلاب في المسار البرمجي وتسليم المهام الحسابية</p>
    </div>
    <a class="btn btn-secondary" href="students.html">إدارة الدليل الكامل</a>
  </div>
  <div class="table-wrap" style="margin-top:1rem">
    <table class="data-table">
      <thead><tr><th>اسم الطالب</th><th>المعرف</th><th>المسار</th><th>الحصص</th><th>تسليم الواجبات</th><th>الحالة</th></tr></thead>
      <tbody>
        <tr><td><div class="person"><span class="avatar">ع.س</span><div><strong>عبدالله سامي القحطاني</strong><div class="body-sm muted">abdullah.s@codeverse.edu</div></div></div></td><td class="ltr">CV-24901</td><td><span class="badge badge-success">هندسة النظم الخلفية</span></td><td class="ltr">42 / 44</td><td><div class="progress success" style="max-width:100px"><span style="width:98%"></span></div></td><td><span class="badge badge-success">متميز وأول الدفعة</span></td></tr>
        <tr><td><div class="person"><span class="avatar">ف.ن</span><div><strong>فاطمة ناصر الزهراني</strong><div class="body-sm muted">fatima.n@codeverse.edu</div></div></div></td><td class="ltr">CV-24918</td><td><span class="badge badge-info">تطبيقات الجوال Flutter</span></td><td class="ltr">31 / 44</td><td><div class="progress" style="max-width:100px"><span style="width:82%"></span></div></td><td><span class="badge badge-info">نشط ومنتظم</span></td></tr>
        <tr><td><div class="person"><span class="avatar">ز.ح</span><div><strong>زياد حسام الدين</strong><div class="body-sm muted">ziad.h@codeverse.dev</div></div></div></td><td class="ltr">#ST-2024-089</td><td><span class="badge badge-success">هندسة برمجيات الأنظمة</span></td><td class="ltr">27 / 28</td><td><div class="progress success" style="max-width:100px"><span style="width:96%"></span></div></td><td><span class="badge badge-success">متصل الآن</span></td></tr>
      </tbody>
    </table>
  </div>
</section>
""",
)

STUDENTS_MODALS = """
<div class="drawer-backdrop" id="student-drawer">
  <aside class="drawer">
    <div class="modal-header">
      <div>
        <h3 class="headline-sm" id="drawer-name">زياد حسام الدين</h3>
        <span class="ltr accent" id="drawer-id">#ST-2024-089</span>
      </div>
      <button class="btn-icon" type="button" data-close="#student-drawer"><span class="material-symbols-outlined">close</span></button>
    </div>
    <div class="modal-body">
      <span class="badge badge-success">نشط ومتصل الآن</span>
      <p class="body-sm muted">هندسة برمجيات الأنظمة · المستوى المتقدم</p>
      <p class="ltr">ziad.h@codeverse.dev</p>
      <div class="stat-foot"><span>المعدل</span><strong class="success">98.4%</strong></div>
      <a class="btn btn-primary" href="student-profile.html">فتح الملف الأكاديمي</a>
    </div>
  </aside>
</div>
<div class="modal-backdrop" id="new-student-modal">
  <div class="modal">
    <div class="modal-header"><h2 class="headline-sm">إضافة طالب جديد</h2><button class="btn-icon" data-close="#new-student-modal" type="button"><span class="material-symbols-outlined">close</span></button></div>
    <form class="modal-body" data-validate data-close-on-submit="#new-student-modal">
      <div class="form-grid">
        <div class="field"><label>الاسم الكامل</label><input class="input" required placeholder="مثال: زياد حسام الدين" /></div>
        <div class="field"><label>البريد الأكاديمي</label><input class="input" required placeholder="student@codeverse.edu" /></div>
        <div class="field"><label>المسار</label><select class="select"><option>هندسة برمجيات الأنظمة</option><option>تطوير واجهات React</option><option>تطوير الخوادم Node.js</option></select></div>
        <div class="field"><label>المستوى</label><select class="select"><option>الأول</option><option>الثاني</option><option>المتقدم</option></select></div>
      </div>
      <div class="modal-footer" style="padding:0">
        <button class="btn btn-ghost" type="button" data-close="#new-student-modal">إلغاء</button>
        <button class="btn btn-primary" type="submit">حفظ السجل</button>
      </div>
    </form>
  </div>
</div>
"""

shell_page(
    "admin/students.html",
    "إدارة الطلاب",
    "admin",
    "students",
    "../",
    f"""
<div class="toolbar">
  <div>
    <h1 class="headline-lg">إدارة شؤون الطلاب والمتابعة الأكاديمية</h1>
    <p class="body-md muted">رصد التفاعل البرمجي، نسب تسليم الأكواد والمشاريع، وسجل الحضور الفوري لطلاب المنصة.</p>
  </div>
  <div class="wrap">
    <button class="btn btn-secondary" type="button" data-open="#generic-modal"><span class="material-symbols-outlined">upload_file</span> استيراد CSV</button>
    <button class="btn btn-primary" type="button" data-open="#new-student-modal"><span class="material-symbols-outlined">person_add</span> إضافة طالب جديد</button>
  </div>
</div>
<section class="grid-4">
{S("blue","groups","","إجمالي الطلاب المقيدين","348","","82% نشاط","+12 هذا الشهر")}
{S("green","military_tech","","الطلاب المتميزون","14","معدل ≥ 95%","لوحة الشرف","مسار تنافسي")}
{S("red","warning","","بحاجة لدعم أكاديمي","08","تأخر واجبين","خطط تعويضية","5 طلاب")}
{S("amber","analytics","","متوسط الحضور التفاعلي","91.4%","","42 متصل الآن","+3.2%")}
</section>
<div class="card">
  <div class="toolbar">
    <div class="navbar-search" style="max-width:none;flex:1">
      <span class="material-symbols-outlined">search</span>
      <input class="search-input" data-table-search="#students-table" placeholder="بحث باسم الطالب، رقم القيد الأكاديمي، أو البريد..." />
    </div>
    <select class="select" data-filter-select="#students-table" style="max-width:220px">
      <option value="all">الحالة: الكل</option>
      <option value="online">متصل</option>
      <option value="active">نشط</option>
      <option value="risk">متأخر</option>
    </select>
  </div>
</div>
<div class="table-wrap">
  <table class="data-table" id="students-table">
    <thead><tr><th></th><th>بيانات الطالب</th><th>المسار</th><th>إنجاز الحصص</th><th>الواجبات</th><th>المعدل</th><th>الحالة</th><th></th></tr></thead>
    <tbody>
      <tr data-filter="online">
        <td><input type="checkbox" /></td>
        <td><div class="person"><span class="avatar">ز.ح</span><div><strong>زياد حسام الدين</strong><div class="ltr accent">#ST-2024-089</div></div></div></td>
        <td>هندسة برمجيات الأنظمة<br /><span class="body-sm muted">المتقدم L3</span></td>
        <td><div class="progress success"><span style="width:96%"></span></div><span class="ltr">27/28</span></td>
        <td><span class="badge badge-success">14/14 مكتمل</span></td>
        <td><span class="badge badge-success">98.4%</span></td>
        <td><span class="badge badge-success">متصل الآن</span></td>
        <td><a class="btn-icon" href="student-profile.html"><span class="material-symbols-outlined">badge</span></a></td>
      </tr>
      <tr data-filter="active">
        <td><input type="checkbox" /></td>
        <td><div class="person"><span class="avatar">س.م</span><div><strong>سارة طارق المنصور</strong><div class="ltr accent">#ST-2024-114</div></div></div></td>
        <td>تطوير واجهات React<br /><span class="body-sm muted">الثاني</span></td>
        <td><div class="progress"><span style="width:85%"></span></div><span class="ltr">24/28</span></td>
        <td><span class="badge badge-success">13/14 مكتمل</span></td>
        <td><span class="badge badge-info">93.0%</span></td>
        <td><span class="badge badge-info">نشط</span></td>
        <td><a class="btn-icon" href="student-profile.html"><span class="material-symbols-outlined">badge</span></a></td>
      </tr>
      <tr data-filter="risk">
        <td><input type="checkbox" /></td>
        <td><div class="person"><span class="avatar">ع.د</span><div><strong>عمر خالد الدوسري</strong> <span class="badge badge-danger">إنذار</span><div class="ltr danger">#ST-2024-032</div></div></div></td>
        <td>تطوير الخوادم Node.js<br /><span class="body-sm muted">الأول</span></td>
        <td><div class="progress danger"><span style="width:50%"></span></div><span class="ltr">14/28</span></td>
        <td><span class="badge badge-danger">6/14 متأخر</span></td>
        <td><span class="badge badge-danger">64.2%</span></td>
        <td><span class="badge badge-danger">متأخر دراسياً</span></td>
        <td><a class="btn-icon" href="student-profile.html"><span class="material-symbols-outlined">badge</span></a></td>
      </tr>
    </tbody>
  </table>
</div>
""",
    STUDENTS_MODALS + open(ROOT / "components/modals.html", encoding="utf-8").read(),
)

shell_page(
    "admin/student-profile.html",
    "ملف الطالب",
    "admin",
    "students",
    "../",
    """
<nav class="crumb"><a href="students.html">الطلاب</a><span class="material-symbols-outlined">chevron_left</span><span>زياد حسام الدين</span></nav>
<section class="page-hero">
  <div class="between" style="flex-wrap:wrap">
    <div class="person">
      <span class="avatar" style="width:64px;height:64px">ز.ح</span>
      <div>
        <h1 class="headline-lg">زياد حسام الدين</h1>
        <p class="ltr accent">#ST-2024-089 · ziad.h@codeverse.dev</p>
        <div class="wrap" style="margin-top:8px"><span class="badge badge-success">نشط ومتصل</span><span class="badge badge-warn">لوحة الشرف</span></div>
      </div>
    </div>
    <div class="wrap">
      <button class="btn btn-secondary" type="button" data-open="#generic-modal">إرسال تنبيه</button>
      <button class="btn btn-primary" type="button" data-open="#generic-modal">تعديل السجل</button>
    </div>
  </div>
</section>
<section class="grid-4">
  <div class="card"><span class="label-sm muted">المعدل</span><div class="headline-lg success">98.4%</div></div>
  <div class="card"><span class="label-sm muted">الحصص</span><div class="headline-lg">27/28</div></div>
  <div class="card"><span class="label-sm muted">الواجبات</span><div class="headline-lg">14/14</div></div>
  <div class="card"><span class="label-sm muted">المسار</span><div class="headline-sm">هندسة برمجيات الأنظمة</div></div>
</section>
<section class="card card-lg">
  <h2 class="headline-sm">سجل النشاط الأخير</h2>
  <div class="stack" style="margin-top:12px">
    <div class="notif-item"><span class="material-symbols-outlined">quiz</span><div><strong>اجتاز اختبار هياكل البيانات</strong><p class="body-sm muted">درجة 96% · أمس 09:40 م</p></div></div>
    <div class="notif-item"><span class="material-symbols-outlined">assignment</span><div><strong>تسليم مشروع REST API</strong><p class="body-sm muted">قبل 2 ساعة</p></div></div>
  </div>
</section>
""",
    open(ROOT / "components/modals.html", encoding="utf-8").read(),
)

shell_page(
    "admin/lessons.html",
    "إدارة الحصص",
    "admin",
    "lessons",
    "../",
    f"""
<div class="toolbar">
  <div>
    <span class="badge badge-info">نظام إدارة المحتوى الأكاديمي</span>
    <h1 class="headline-xl">إدارة الحصص والمحاضرات البرمجية</h1>
    <p class="body-md muted">جدولة الحصص المباشرة والمسجلة، إدارة روابط الفيديو، مذكرات PDF، وسكربتات الأكواد لكل مستوى.</p>
  </div>
  <button class="btn btn-primary" type="button" data-open="#lesson-modal"><span class="material-symbols-outlined">add_circle</span> إضافة حصة جديدة / درس</button>
</div>
<section class="grid-4">
{S("blue","video_library","","إجمالي الحصص المنشورة","84","+6 هذا الشهر","مسارات","4")}
{S("green","schedule","","ساعات البث والتدريب","142","ساعة","اكتمال الخطة","78%")}
{S("amber","play_circle","","حصص مباشرة هذا الأسبوع","6","","اليوم","معمل DP")}
{S("blue","picture_as_pdf","","مذكرات مرفقة","52","","PDF","نشط")}
</section>
<div class="card">
  <input class="input" data-table-search="#lessons-grid" placeholder="ابحث بالعنوان، كود الدرس (LES-XXX)، أو التقنية..." />
</div>
<div class="grid-2" id="lessons-grid">
  <article class="course-card">
    <div class="course-card-media video-stage" style="min-height:140px"><span class="material-symbols-outlined" style="font-size:36px">play_circle</span></div>
    <div class="course-card-body">
      <span class="ltr accent">LES-014</span>
      <h3 class="headline-sm">البرمجة الديناميكية Dynamic Programming</h3>
      <p class="body-sm muted">معمل الخوارزميات · 95 دقيقة · 184 مسجلاً</p>
      <div class="progress"><span style="width:70%"></span></div>
      <div class="wrap"><a class="btn btn-secondary" href="#">تعديل</a><button class="btn btn-ghost" data-open="#lesson-modal" type="button">المحتوى</button></div>
    </div>
  </article>
  <article class="course-card">
    <div class="course-card-media video-stage" style="min-height:140px"><span class="material-symbols-outlined" style="font-size:36px">terminal</span></div>
    <div class="course-card-body">
      <span class="ltr accent">LES-022</span>
      <h3 class="headline-sm">بناء واجهات REST باستخدام Node.js</h3>
      <p class="body-sm muted">المسار الخلفي · 80 دقيقة · 126 مشاهدة</p>
      <div class="progress success"><span style="width:100%"></span></div>
      <div class="wrap"><span class="badge badge-success">منشور</span></div>
    </div>
  </article>
</div>
""",
    """
<div class="modal-backdrop" id="lesson-modal">
  <div class="modal">
    <div class="modal-header"><h2 class="headline-sm">إضافة / تعديل حصة</h2><button class="btn-icon" data-close="#lesson-modal" type="button"><span class="material-symbols-outlined">close</span></button></div>
    <form class="modal-body" data-validate data-close-on-submit="#lesson-modal">
      <div class="field"><label>عنوان الحصة</label><input class="input" required placeholder="مثال: مقدمة في الخوارزميات" /></div>
      <div class="form-grid">
        <div class="field"><label>كود الدرس</label><input class="input ltr" placeholder="LES-030" /></div>
        <div class="field"><label>المدة (دقيقة)</label><input class="input" type="number" value="90" /></div>
      </div>
      <div class="field"><label>مصدر الفيديو</label><input class="input ltr" placeholder="https://..." /></div>
      <div class="modal-footer" style="padding:0"><button class="btn btn-ghost" type="button" data-close="#lesson-modal">إلغاء</button><button class="btn btn-primary" type="submit">حفظ الحصة</button></div>
    </form>
  </div>
</div>
""",
)

shell_page(
    "admin/homework.html",
    "الواجبات",
    "admin",
    "homework",
    "../",
    f"""
<section class="page-hero">
  <div class="between" style="flex-wrap:wrap">
    <div>
      <h1 class="headline-lg">إدارة وتصحيح التكاليف والواجبات البرمجية</h1>
      <p class="body-md muted">متابعة تسليمات أكواد الطلاب، مراجعة المشاريع، ورصد الدرجات الأكاديمية (واجهة فقط).</p>
    </div>
    <button class="btn btn-primary" type="button" data-open="#hw-modal"><span class="material-symbols-outlined">add_task</span> إنشاء تكليف جديد</button>
  </div>
</section>
<section class="grid-4">
{S("blue","code_blocks","","التكاليف النشطة","14","واجب مفتوح","المسارات","مغطاة")}
{S("amber","pending_actions","","تنتظر التصحيح","38","مشروعاً","يدوي","مطلوب")}
{S("green","flaky","","تصحيح آلي","284","نجاح 89%","Unit Tests","جاهز")}
{S("red","event_busy","","تجاوز الموعد","11","تسليم","متابعة","عاجلة")}
</section>
<div class="table-wrap">
  <table class="data-table" id="hw-table">
    <thead><tr><th>التكليف</th><th>المسار</th><th>التسليمات</th><th>الموعد</th><th>الحالة</th></tr></thead>
    <tbody>
      <tr><td><strong>مشروع REST API</strong><div class="ltr muted">HW-118</div></td><td>Backend</td><td>312 / 348</td><td>18 سبتمبر</td><td><span class="badge badge-warn">تصحيح جارٍ</span></td></tr>
      <tr><td><strong>خوارزميات DP</strong><div class="ltr muted">HW-121</div></td><td>Algorithms</td><td>280 / 348</td><td>21 سبتمبر</td><td><span class="badge badge-info">مفتوح</span></td></tr>
    </tbody>
  </table>
</div>
""",
    """
<div class="modal-backdrop" id="hw-modal"><div class="modal"><div class="modal-header"><h2 class="headline-sm">تكليف جديد</h2><button class="btn-icon" data-close="#hw-modal" type="button"><span class="material-symbols-outlined">close</span></button></div>
<form class="modal-body" data-validate data-close-on-submit="#hw-modal">
  <div class="field"><label>عنوان التكليف</label><input class="input" required /></div>
  <div class="field"><label>التعليمات</label><textarea class="textarea" placeholder="وصف المهمة ومعايير التقييم"></textarea></div>
  <button class="btn btn-primary" type="submit">حفظ</button>
</form></div></div>
""",
)

shell_page(
    "admin/exams.html",
    "الامتحانات",
    "admin",
    "exams",
    "../",
    f"""
<section class="page-hero">
  <div class="glow glow-a"></div>
  <div class="between" style="flex-wrap:wrap;position:relative;z-index:1">
    <div>
      <span class="badge badge-info">نظام الاختبارات المركزية الذكي</span>
      <h1 class="headline-xl">إدارة الامتحانات وبنك الأسئلة التفاعلي</h1>
      <p class="body-md muted">بناء قاعات الاختبارات، ضبط المؤقتات، وإدارة بنوك الأسئلة الأكاديمية.</p>
    </div>
    <div class="wrap">
      <a class="btn btn-secondary" href="../student/exam.html">معاينة كطالب</a>
      <a class="btn btn-primary" href="questions.html">بنك الأسئلة</a>
    </div>
  </div>
</section>
<section class="grid-4">
{S("blue","timer","","امتحانات نشطة","8","","اليوم","3 جارية")}
{S("green","groups","","مشاركون","312","","قاعات","2")}
{S("amber","hourglass","","بانتظار الرصد","5","","يدوي","نعم")}
{S("blue","help_center","","أسئلة البنك","640","","جاهزة","للاستخدام")}
</section>
<div class="grid-2">
  <article class="exam-card"><div class="exam-card-body"><span class="badge badge-success">جارٍ</span><h3 class="headline-sm">اختبار هياكل البيانات</h3><p class="body-sm muted">90 دقيقة · 40 سؤالاً · نزاهة مفعّلة</p><div class="progress"><span style="width:55%"></span></div><a class="btn btn-secondary" href="results.html">رصد النتائج</a></div></article>
  <article class="exam-card"><div class="exam-card-body"><span class="badge badge-info">مجدول</span><h3 class="headline-sm">نهائي مسار الويب</h3><p class="body-sm muted">120 دقيقة · 22 سبتمبر 08:00 م</p><button class="btn btn-primary" type="button" data-open="#exam-modal">ضبط القاعة</button></div></article>
</div>
""",
    """
<div class="modal-backdrop" id="exam-modal"><div class="modal"><div class="modal-header"><h2 class="headline-sm">إنشاء اختبار</h2><button class="btn-icon" data-close="#exam-modal" type="button"><span class="material-symbols-outlined">close</span></button></div>
<form class="modal-body" data-validate data-close-on-submit="#exam-modal">
  <div class="field"><label>عنوان الاختبار</label><input class="input" required /></div>
  <div class="form-grid"><div class="field"><label>المدة بالدقائق</label><input class="input" type="number" value="90" /></div><div class="field"><label>عدد الأسئلة</label><input class="input" type="number" value="20" /></div></div>
  <button class="btn btn-primary" type="submit">حفظ الجدول</button>
</form></div></div>
""",
)

shell_page(
    "admin/questions.html",
    "بنك الأسئلة",
    "admin",
    "questions",
    "../",
    """
<div class="toolbar">
  <div>
    <h1 class="headline-lg">مستودع بنك الأسئلة الأكاديمي</h1>
    <p class="body-md muted">أسئلة اختيار من متعدد، صح/خطأ، ومسائل برمجية قصيرة.</p>
  </div>
  <button class="btn btn-primary" type="button" data-open="#q-modal">إضافة سؤال</button>
</div>
<div class="tabs">
  <button class="tab is-active" data-tab-group="q" data-tab="mcq" type="button">اختيار من متعدد</button>
  <button class="tab" data-tab-group="q" data-tab="code" type="button">مسائل برمجية</button>
</div>
<section data-tab-panel-group="q" data-tab-panel="mcq" class="stack">
  <article class="card"><span class="badge badge-info">متوسط</span><h3 class="headline-sm">ما تعقيد البحث الثنائي؟</h3><p class="body-sm muted ltr">O(log n)</p></article>
  <article class="card"><span class="badge badge-warn">متقدم</span><h3 class="headline-sm">أي هيكل يناسب LIFO؟</h3><p class="body-sm muted">المكدس Stack</p></article>
</section>
<section class="hidden stack" data-tab-panel-group="q" data-tab-panel="code">
  <article class="card"><h3 class="headline-sm">اكتب دالة لعكس قائمة مرتبطة</h3><pre class="code-block">function reverse(head) { /* ... */ }</pre></article>
</section>
""",
    """
<div class="modal-backdrop" id="q-modal"><div class="modal"><div class="modal-header"><h2 class="headline-sm">سؤال جديد</h2><button class="btn-icon" data-close="#q-modal" type="button"><span class="material-symbols-outlined">close</span></button></div>
<form class="modal-body" data-validate data-close-on-submit="#q-modal">
  <div class="field"><label>نص السؤال</label><textarea class="textarea" required></textarea></div>
  <button class="btn btn-primary" type="submit">إضافة للبنك</button>
</form></div></div>
""",
)

shell_page(
    "admin/results.html",
    "النتائج",
    "admin",
    "results",
    "../",
    """
<h1 class="headline-lg">رصد النتائج والتقارير</h1>
<p class="body-md muted">تحليل درجات الاختبارات والواجبات حسب المسار والمستوى.</p>
<section class="grid-4">
  <div class="card"><span class="label-sm muted">متوسط الدفعة</span><div class="headline-lg">87.6%</div></div>
  <div class="card"><span class="label-sm muted">نسبة النجاح</span><div class="headline-lg success">91%</div></div>
  <div class="card"><span class="label-sm muted">يحتاجون إعادة</span><div class="headline-lg warning">14</div></div>
  <div class="card"><span class="label-sm muted">اختبارات مرصودة</span><div class="headline-lg">32</div></div>
</section>
<div class="table-wrap">
  <table class="data-table">
    <thead><tr><th>الطالب</th><th>الاختبار</th><th>الدرجة</th><th>الحالة</th></tr></thead>
    <tbody>
      <tr><td>زياد حسام الدين</td><td>هياكل البيانات</td><td>96%</td><td><span class="badge badge-success">ممتاز</span></td></tr>
      <tr><td>سارة طارق المنصور</td><td>هياكل البيانات</td><td>91%</td><td><span class="badge badge-success">جيد جداً</span></td></tr>
      <tr><td>عمر خالد الدوسري</td><td>هياكل البيانات</td><td>58%</td><td><span class="badge badge-danger">إعادة</span></td></tr>
    </tbody>
  </table>
</div>
""",
)

shell_page(
    "admin/files.html",
    "مكتبة الملفات",
    "admin",
    "files",
    "../",
    f"""
<div class="toolbar">
  <div>
    <span class="label-sm accent">Cloud Repository Engine v2.4</span>
    <h1 class="headline-xl">مكتبة الملفات والمذكرات الدراسية</h1>
    <p class="body-md muted">المستودع السحابي الموحد للمذكرات PDF، أكواد المشاريع، والعروض.</p>
  </div>
  <div class="wrap">
    <button class="btn btn-primary" data-open="#upload-modal" type="button"><span class="material-symbols-outlined">cloud_upload</span> رفع ملف جديد</button>
    <button class="btn btn-secondary" data-open="#generic-modal" type="button"><span class="material-symbols-outlined">create_new_folder</span> مجلد جديد</button>
  </div>
</div>
<section class="grid-4">
{S("blue","folder_copy","","إجمالي الملفات","168","ملف نشط","مسارات","4")}
{S("green","cloud","","المساحة المستخدمة","4.8","/ 50 GB","مستهلك","9.6%")}
{S("blue","downloading","","تنزيلات الطلاب","3,420","","هذا الشهر","+18%")}
{S("amber","fiber_new","","منشور حديثاً","12","هذا الأسبوع","آخر إضافة","40 د")}
</section>
<div class="grid-2">
  <article class="file-card"><div class="file-card-body"><span class="material-symbols-outlined">picture_as_pdf</span><h3 class="headline-sm">مذكرة هياكل البيانات.pdf</h3><p class="body-sm muted">2.4 MB · 640 تنزيلاً</p><button class="btn btn-ghost" type="button">تفاصيل</button></div></article>
  <article class="file-card"><div class="file-card-body"><span class="material-symbols-outlined">folder_zip</span><h3 class="headline-sm">starter-rest-api.zip</h3><p class="body-sm muted">1.1 MB · مشروع الأسبوع</p><button class="btn btn-ghost" type="button">تفاصيل</button></div></article>
</div>
""",
    """
<div class="modal-backdrop" id="upload-modal"><div class="modal"><div class="modal-header"><h2 class="headline-sm">رفع ملف (واجهة فقط)</h2><button class="btn-icon" data-close="#upload-modal" type="button"><span class="material-symbols-outlined">close</span></button></div>
<form class="modal-body" data-validate data-close-on-submit="#upload-modal">
  <div class="field"><label>اسم العرض</label><input class="input" required /></div>
  <div class="field"><label>نوع الملف</label><select class="select"><option>PDF</option><option>ZIP</option><option>فيديو</option></select></div>
  <p class="body-sm muted">لا يتم تنفيذ رفع حقيقي في هذه المرحلة.</p>
  <button class="btn btn-primary" type="submit">حفظ السجل</button>
</form></div></div>
"""
    + open(ROOT / "components/modals.html", encoding="utf-8").read(),
)

shell_page(
    "admin/notifications.html",
    "الإشعارات",
    "admin",
    "notifications",
    "../",
    """
<div class="toolbar">
  <h1 class="headline-lg">الإشعارات والتعاميم</h1>
  <button class="btn btn-primary" data-open="#generic-modal" type="button">تعميم جديد</button>
</div>
<div class="stack">
  <article class="notif-item unread"><span class="material-symbols-outlined">campaign</span><div><strong>تذكير بموعد اختبار هياكل البيانات</strong><p class="body-sm muted">أُرسل إلى 348 طالباً · اليوم 11:20 ص</p></div></article>
  <article class="notif-item"><span class="material-symbols-outlined">assignment</span><div><strong>فتح تكليف مشروع REST API</strong><p class="body-sm muted">أمس</p></div></article>
</div>
""",
    open(ROOT / "components/modals.html", encoding="utf-8").read(),
)

shell_page(
    "admin/settings.html",
    "الإعدادات",
    "admin",
    "settings",
    "../",
    """
<h1 class="headline-lg">الإعدادات العامة</h1>
<p class="body-md muted">ضبط مظهر المنصة والفصل الدراسي — بدون حفظ خلفي.</p>
<form class="card card-lg stack" data-validate>
  <div class="form-grid">
    <div class="field"><label>اسم المؤسسة</label><input class="input" value="كودفيرس" required /></div>
    <div class="field"><label>رمز الفصل</label><input class="input ltr" value="CV-FA24-MTR" /></div>
    <div class="field"><label>لغة الواجهة</label><select class="select"><option>العربية RTL</option><option>English</option></select></div>
    <div class="field"><label>المنطقة الزمنية</label><select class="select"><option>Asia/Riyadh</option></select></div>
  </div>
  <div class="setting-row"><div><strong>تفعيل الإشعارات الفورية</strong><p class="body-sm muted">عرض شارة التنبيه في الشريط العلوي</p></div><input type="checkbox" checked /></div>
  <button class="btn btn-primary" type="submit">حفظ الإعدادات</button>
</form>
""",
)

# ---------- student ----------
shell_page(
    "student/dashboard.html",
    "لوحة الطالب",
    "student",
    "dashboard",
    "../",
    f"""
<section class="page-hero">
  <div class="glow glow-b"></div>
  <h1 class="headline-lg">مرحباً زياد، استمر في مسار الإتقان 👋</h1>
  <p class="body-md muted">تقدمك الحالي في هندسة برمجيات الأنظمة · المستوى المتقدم</p>
  <div class="progress success" style="margin-top:12px;max-width:420px"><span style="width:96%"></span></div>
</section>
<section class="grid-4">
{S("blue","play_lesson","","حصص مكتملة","27","/ 28","المتبقي","حصة واحدة")}
{S("green","task_alt","","واجبات مسلّمة","14","/ 14","التزام","100%")}
{S("amber","quiz","","اختبار قادم","1","هياكل البيانات","المدة","90 د")}
{S("blue","emoji_events","","المعدل","98.4%","","لوحة الشرف","نعم")}
</section>
<div class="grid-2">
  <article class="course-card"><div class="course-card-body"><span class="badge badge-info">التالي</span><h3 class="headline-sm">معمل البرمجة الديناميكية</h3><p class="body-sm muted">اليوم 07:00 م</p><a class="btn btn-primary" href="lesson.html">دخول الحصة</a></div></article>
  <article class="exam-card"><div class="exam-card-body"><span class="badge badge-warn">خلال 48 ساعة</span><h3 class="headline-sm">اختبار هياكل البيانات</h3><a class="btn btn-secondary" href="exam.html">تعليمات الاختبار</a></div></article>
</div>
""",
)

shell_page(
    "student/lessons.html",
    "الحصص",
    "student",
    "lessons",
    "../",
    """
<h1 class="headline-lg">الحصص والدروس</h1>
<p class="body-md muted">مسارك الأكاديمي مرتب حسب مستوى الإكمال.</p>
<div class="grid-2">
  <article class="course-card"><div class="course-card-body"><span class="ltr accent">LES-014</span><h3 class="headline-sm">البرمجة الديناميكية</h3><div class="progress"><span style="width:40%"></span></div><a class="btn btn-primary" href="lesson.html">متابعة</a></div></article>
  <article class="course-card"><div class="course-card-body"><span class="ltr accent">LES-022</span><h3 class="headline-sm">واجهات REST وNode.js</h3><div class="progress success"><span style="width:100%"></span></div><span class="badge badge-success">مكتمل</span></div></article>
</div>
""",
)

shell_page(
    "student/lesson.html",
    "تفاصيل الحصة",
    "student",
    "lessons",
    "../",
    """
<nav class="crumb"><a href="lessons.html">الحصص</a><span class="material-symbols-outlined">chevron_left</span><span>LES-014</span></nav>
<div class="grid-12">
  <section class="span-8 stack">
    <div class="video-stage">
      <span class="material-symbols-outlined" style="font-size:64px;color:var(--primary)">play_circle</span>
      <h1 class="headline-md">حل معضلات Dynamic Programming</h1>
      <p class="body-sm muted">معمل الخوارزميات الحي #14</p>
    </div>
    <article class="card"><h2 class="headline-sm">وصف الحصة</h2><p class="body-md muted">تطبيق أمثلة Memoization وTabulation مع تمارين قصيرة داخل المختبر.</p></article>
    <pre class="code-block">function fib(n, memo = {}) {\n  if (n in memo) return memo[n];\n  if (n <= 1) return n;\n  return memo[n] = fib(n - 1, memo) + fib(n - 2, memo);\n}</pre>
  </section>
  <aside class="span-4 stack">
    <div class="card"><h3 class="headline-sm">محتويات المسار</h3><a class="nav-link is-active" href="lesson.html">1. Memoization</a><a class="nav-link" href="lesson.html">2. Tabulation</a><a class="nav-link" href="homework.html">3. واجب الأسبوع</a></div>
    <a class="btn btn-secondary" href="files.html">تحميل المذكرة PDF</a>
  </aside>
</div>
""",
)

shell_page(
    "student/homework.html",
    "واجبات الطالب",
    "student",
    "homework",
    "../",
    """
<h1 class="headline-lg">الواجبات والتكاليف</h1>
<div class="grid-2">
  <article class="card"><span class="badge badge-success">مُسلَّم</span><h3 class="headline-sm">مشروع REST API</h3><p class="body-sm muted">تم التسليم · بانتظار الرصد النهائي</p></article>
  <article class="card"><span class="badge badge-info">مفتوح</span><h3 class="headline-sm">تمارين DP</h3><p class="body-sm muted">الموعد: 21 سبتمبر</p><button class="btn btn-primary" data-open="#generic-modal" type="button">تسليم تجريبي</button></article>
</div>
""",
    open(ROOT / "components/modals.html", encoding="utf-8").read(),
)

shell_page(
    "student/exams.html",
    "امتحانات الطالب",
    "student",
    "exams",
    "../",
    """
<h1 class="headline-lg">الامتحانات</h1>
<div class="grid-2">
  <article class="exam-card"><div class="exam-card-body"><span class="badge badge-warn">متاح قريباً</span><h3 class="headline-sm">اختبار هياكل البيانات</h3><p class="body-sm muted">90 دقيقة · 40 سؤالاً</p><a class="btn btn-primary" href="exam.html">دخول قاعة الاختبار</a></div></article>
  <article class="exam-card"><div class="exam-card-body"><span class="badge badge-success">مكتمل</span><h3 class="headline-sm">اختبار أساسيات الخوارزميات</h3><p class="body-sm muted">درجتك: 96%</p><a class="btn btn-secondary" href="results.html">عرض التصحيح</a></div></article>
</div>
""",
)

shell_page(
    "student/exam.html",
    "قاعة الاختبار",
    "student",
    "exams",
    "../",
    """
<div class="between"><h1 class="headline-lg">اختبار هياكل البيانات</h1><div class="timer" data-exam-timer="5400">90:00</div></div>
<div class="exam-layout">
  <section class="card card-lg stack">
    <article data-question-panel="1">
      <p class="label-sm muted">سؤال 1 من 4</p>
      <h2 class="headline-sm">ما هو أفضل تعقيد زمني للبحث الثنائي على مصفوفة مرتبة؟</h2>
      <div class="stack" style="margin-top:12px">
        <button class="option" data-option type="button">O(n)</button>
        <button class="option is-selected" data-option type="button">O(log n)</button>
        <button class="option" data-option type="button">O(n log n)</button>
        <button class="option" data-option type="button">O(1)</button>
      </div>
    </article>
    <article class="hidden" data-question-panel="2">
      <p class="label-sm muted">سؤال 2 من 4</p>
      <h2 class="headline-sm">أي هيكل بيانات يناسب سياسة LIFO؟</h2>
      <div class="stack" style="margin-top:12px">
        <button class="option" data-option type="button">الطابور Queue</button>
        <button class="option" data-option type="button">المكدس Stack</button>
        <button class="option" data-option type="button">الشجرة Tree</button>
      </div>
    </article>
    <article class="hidden" data-question-panel="3">
      <p class="label-sm muted">سؤال 3 من 4</p>
      <h2 class="headline-sm">Hash Table تستخدم بشكل أساسي لـ:</h2>
      <div class="stack" style="margin-top:12px">
        <button class="option" data-option type="button">البحث بالترتيب</button>
        <button class="option" data-option type="button">الوصول السريع بالمفتاح</button>
      </div>
    </article>
    <article class="hidden" data-question-panel="4">
      <p class="label-sm muted">سؤال 4 من 4</p>
      <h2 class="headline-sm">القائمة المرتبطة Linked List تتميز بـ:</h2>
      <div class="stack" style="margin-top:12px">
        <button class="option" data-option type="button">حجم ثابت في الذاكرة</button>
        <button class="option" data-option type="button">إدراج مرن دون إزاحة العناصر</button>
      </div>
    </article>
    <div class="between">
      <button class="btn btn-secondary" data-exam-nav="prev" type="button">السابق</button>
      <button class="btn btn-primary" data-exam-nav="next" type="button">التالي</button>
    </div>
  </section>
  <aside class="card stack">
    <h3 class="headline-sm">خريطة الأسئلة</h3>
    <div class="q-nav">
      <button class="current" data-question="1" type="button">1</button>
      <button data-question="2" type="button">2</button>
      <button data-question="3" type="button">3</button>
      <button data-question="4" type="button">4</button>
    </div>
    <p class="body-sm muted">التسليم هنا للمعاينة فقط ولن يُحفظ في خادم.</p>
    <button class="btn btn-primary" type="button" data-open="#generic-modal">إنهاء الاختبار</button>
  </aside>
</div>
""",
    open(ROOT / "components/modals.html", encoding="utf-8").read(),
)

shell_page(
    "student/results.html",
    "نتائج الطالب",
    "student",
    "results",
    "../",
    """
<h1 class="headline-lg">نتائجي</h1>
<section class="grid-4">
  <div class="card"><span class="label-sm muted">المعدل التراكمي</span><div class="headline-lg success">98.4%</div></div>
  <div class="card"><span class="label-sm muted">آخر اختبار</span><div class="headline-lg">96%</div></div>
</section>
<div class="table-wrap">
  <table class="data-table">
    <thead><tr><th>التقييم</th><th>الدرجة</th><th>التاريخ</th></tr></thead>
    <tbody>
      <tr><td>اختبار أساسيات الخوارزميات</td><td>96%</td><td>10 سبتمبر</td></tr>
      <tr><td>مشروع REST API</td><td>38 / 40</td><td>12 سبتمبر</td></tr>
    </tbody>
  </table>
</div>
""",
)

shell_page(
    "student/files.html",
    "ملفات الطالب",
    "student",
    "files",
    "../",
    """
<h1 class="headline-lg">الملفات والمذكرات</h1>
<div class="grid-2">
  <article class="file-card"><div class="file-card-body"><h3 class="headline-sm">مذكرة هياكل البيانات.pdf</h3><p class="body-sm muted">2.4 MB</p><button class="btn btn-secondary" type="button">تنزيل (واجهة)</button></div></article>
  <article class="file-card"><div class="file-card-body"><h3 class="headline-sm">starter-rest-api.zip</h3><p class="body-sm muted">1.1 MB</p><button class="btn btn-secondary" type="button">تنزيل (واجهة)</button></div></article>
</div>
""",
)

shell_page(
    "student/notifications.html",
    "إشعارات الطالب",
    "student",
    "notifications",
    "../",
    """
<h1 class="headline-lg">الإشعارات</h1>
<div class="stack">
  <article class="notif-item unread"><span class="material-symbols-outlined">quiz</span><div><strong>اختبار هياكل البيانات خلال 48 ساعة</strong><p class="body-sm muted">الآن</p></div></article>
  <article class="notif-item"><span class="material-symbols-outlined">task_alt</span><div><strong>تم استلام تسليم مشروع REST API</strong><p class="body-sm muted">أمس</p></div></article>
</div>
""",
)

shell_page(
    "student/profile.html",
    "الملف الشخصي",
    "student",
    "profile",
    "../",
    """
<h1 class="headline-lg">الملف الشخصي والإعدادات</h1>
<section class="page-hero"><div class="person"><span class="avatar" style="width:64px;height:64px">ز.ح</span><div><h2 class="headline-md">زياد حسام الدين</h2><p class="ltr muted">ziad.h@codeverse.dev · #ST-2024-089</p></div></div></section>
<form class="card card-lg stack" data-validate>
  <div class="form-grid">
    <div class="field"><label>الاسم</label><input class="input" value="زياد حسام الدين" required /></div>
    <div class="field"><label>البريد</label><input class="input" value="ziad.h@codeverse.dev" /></div>
  </div>
  <div class="setting-row"><div><strong>إشعارات الاختبارات</strong><p class="body-sm muted">تذكير قبل بدء القاعة</p></div><input type="checkbox" checked /></div>
  <button class="btn btn-primary" type="submit">حفظ الملف</button>
</form>
""",
)

print("built pages")
