(function (global) {
  const ADMIN_NAV = [
    { id: "dashboard", icon: "grid_view", label: "لوحة التحكم", href: "dashboard.html" },
    { id: "students", icon: "group", label: "إدارة الطلاب", href: "students.html" },
    { id: "lessons", icon: "play_lesson", label: "إدارة الحصص والدروس", href: "lessons.html" },
    { id: "homework", icon: "assignment", label: "الواجبات والتكاليف", href: "homework.html" },
    { id: "exams", icon: "quiz", label: "إدارة الامتحانات", href: "exams.html" },
    { id: "questions", icon: "help_center", label: "بنك الأسئلة", href: "questions.html" },
    { id: "results", icon: "insights", label: "رصد النتائج والتقارير", href: "results.html" },
    { id: "files", icon: "folder_open", label: "مكتبة الملفات والمذكرات", href: "files.html" },
    { id: "notifications", icon: "campaign", label: "الإشعارات والتعاميم", href: "notifications.html" },
    { id: "settings", icon: "settings", label: "الإعدادات العامة", href: "settings.html" }
  ];

  const STUDENT_NAV = [
    { id: "dashboard", icon: "grid_view", label: "لوحة التحكم", href: "dashboard.html" },
    { id: "lessons", icon: "play_lesson", label: "الحصص والدروس", href: "lessons.html" },
    { id: "homework", icon: "assignment", label: "الواجبات", href: "homework.html" },
    { id: "exams", icon: "quiz", label: "الامتحانات", href: "exams.html" },
    { id: "results", icon: "insights", label: "نتائجي", href: "results.html" },
    { id: "files", icon: "folder_open", label: "الملفات والمذكرات", href: "files.html" },
    { id: "notifications", icon: "notifications", label: "الإشعارات", href: "notifications.html" },
    { id: "profile", icon: "person", label: "الملف الشخصي", href: "profile.html" }
  ];

  function root() {
    return document.body.getAttribute("data-root") || "./";
  }

  function icon(name, extra) {
    return `<span class="material-symbols-outlined ${extra || ""}">${name}</span>`;
  }

  function sidebarHTML(role, page) {
    const items = role === "student" ? STUDENT_NAV : ADMIN_NAV;
    const gate = role === "student" ? "بوابة الطالب" : "بوابة المعلم والإدارة";
    const loginHref = `${root()}pages/login.html`;
    const links = items
      .map((item) => {
        const active = item.id === page ? "is-active" : "";
        return `<a class="nav-link ${active}" href="${item.href}" data-nav="${item.id}">${icon(item.icon)}<span>${item.label}</span></a>`;
      })
      .join("");

    return `
      <aside class="sidebar" id="app-sidebar">
        <div class="sidebar-brand">
          <img src="${root()}assets/icons/logo.svg" alt="كودفيرس" />
          <div>
            <div class="brand-title">كودفيرس</div>
            <div class="brand-sub">نظام الإدارة التعليمية</div>
          </div>
        </div>
        <div class="sidebar-gate">
          <div class="sidebar-gate-inner">
            <div class="row">
              <span class="dot"></span>
              <span class="label-sm success" style="font-weight:700">${gate}</span>
            </div>
            <span class="badge badge-neutral">v2.4</span>
          </div>
        </div>
        <nav class="sidebar-nav">${links}</nav>
        <div class="sidebar-foot">
          <a class="nav-link logout" href="${loginHref}">${icon("logout")}<span>تسجيل الخروج</span></a>
        </div>
      </aside>
      <div class="overlay" data-sidebar-close></div>
    `;
  }

  function navbarHTML(role) {
    const isStudent = role === "student";
    const name = isStudent ? "زياد حسام الدين" : "أ. مروان الشامي";
    const title = isStudent ? "طالب مسار هندسة البرمجيات" : "مشرف المنصة التعليمية";
    const badge = isStudent ? "لوحة الطالب" : "لوحة المعلم والإدارة";
    const badgeIcon = isStudent ? "school" : "shield_person";
    const notifHref = "notifications.html";
    const profileHref = isStudent ? "profile.html" : "settings.html";

    return `
      <header class="navbar">
        <button class="menu-toggle" type="button" data-sidebar-toggle aria-label="القائمة">${icon("menu")}</button>
        <div class="navbar-search">
          ${icon("search")}
          <input class="search-input" type="search" placeholder="بحث عن طالب، حصة، امتحان..." data-global-search />
        </div>
        <div class="navbar-actions">
          <span class="gate-badge">${icon(badgeIcon)} ${badge}</span>
          <a class="btn-icon" href="${notifHref}" aria-label="الإشعارات" style="position:relative">
            ${icon("notifications")}
            <span class="dot" style="position:absolute;top:8px;right:8px;background:var(--error);width:8px;height:8px"></span>
          </a>
          <a class="row" href="${profileHref}" style="padding-right:8px;border-right:1px solid rgba(66,71,84,.4);gap:8px">
            <div class="user-meta">
              <div class="label-md" style="font-weight:700">${name}</div>
              <div class="label-sm muted">${title}</div>
            </div>
            <span class="avatar">${icon("person")}</span>
          </a>
        </div>
      </header>
    `;
  }

  function footerHTML() {
    return `<footer class="page-footer">كودفيرس · نظام الإدارة التعليمية · النسخة الخاصة · 2024 / 2025</footer>`;
  }

  function mountShell() {
    const role = document.body.dataset.role;
    const page = document.body.dataset.page;
    if (!role) return;

    const sidebarRoot = document.getElementById("sidebar-root");
    const navbarRoot = document.getElementById("navbar-root");
    const footerRoot = document.getElementById("footer-root");
    if (sidebarRoot) sidebarRoot.innerHTML = sidebarHTML(role, page);
    if (navbarRoot) navbarRoot.innerHTML = navbarHTML(role);
    if (footerRoot) footerRoot.innerHTML = footerHTML();
  }

  global.CVComponents = {
    ADMIN_NAV,
    STUDENT_NAV,
    root,
    icon,
    sidebarHTML,
    navbarHTML,
    footerHTML,
    mountShell
  };
})(window);
