(function () {
  function bindForms() {
    document.querySelectorAll("form[data-validate]").forEach((form) => {
      form.addEventListener("submit", (event) => {
        const missing = [...form.querySelectorAll("[required]")].find((field) => !String(field.value || "").trim());
        if (missing) {
          event.preventDefault();
          missing.focus();
          window.CVUi && CVUi.toast("يرجى تعبئة الحقول المطلوبة");
          return;
        }
        if (!form.getAttribute("action") && !form.getAttribute("method")) {
          event.preventDefault();
          window.CVUi && CVUi.toast("تم حفظ البيانات محلياً (واجهة فقط)");
          const closeSel = form.dataset.closeOnSubmit;
          if (closeSel) CVUi.closeTarget(closeSel);
        }
      });
    });

    const toggle = document.querySelector("[data-password-toggle]");
    if (toggle) {
      toggle.addEventListener("click", () => {
        const input = document.getElementById("password");
        const icon = document.getElementById("password-toggle-icon");
        const show = input.type === "password";
        input.type = show ? "text" : "password";
        if (icon) icon.textContent = show ? "visibility" : "visibility_off";
      });
    }

    document.querySelectorAll("[data-role]").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll("[data-role]").forEach((el) => el.classList.remove("is-active", "is-staff"));
        btn.classList.add("is-active");
        if (btn.dataset.role === "staff") btn.classList.add("is-staff");
        const input = document.getElementById("identifier");
        if (input) {
          input.placeholder =
            btn.dataset.role === "staff"
              ? "مثال: admin@codeverse.edu أو المعرف الإداري"
              : "مثال: student@codeverse.edu أو الاسم التعريفي";
        }
        document.body.dataset.loginRole = btn.dataset.role;
      });
    });

    document.querySelectorAll("[data-demo]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const type = btn.dataset.demo;
        const roleBtn = document.querySelector(`[data-role="${type === "student" ? "student" : "staff"}"]`);
        if (roleBtn) roleBtn.click();
        const idInput = document.getElementById("identifier");
        const passInput = document.getElementById("password");
        if (idInput) {
          idInput.value = type === "student" ? "student@codeverse.edu" : "admin@codeverse.edu";
        }
        if (passInput) {
          passInput.value = type === "student" ? "student123" : "admin123";
        }
      });
    });

    const loginForm = document.getElementById("login-form");
    if (loginForm && loginForm.hasAttribute("data-static-redirect")) {
      loginForm.addEventListener("submit", (event) => {
        event.preventDefault();
        const role = document.body.dataset.loginRole || "student";
        const btn = loginForm.querySelector("[type=submit]");
        btn.disabled = true;
        btn.innerHTML = '<span class="material-symbols-outlined">progress_activity</span><span>جاري التحقق الآمن...</span>';
        setTimeout(() => {
          const root = document.body.dataset.root || "/";
          window.location.href = role === "staff" ? `${root}admin/dashboard` : `${root}student/dashboard`;
        }, 800);
      });
    }
  }

  window.CVForms = { bindForms };
})();
