(function () {
  function bindExam() {
    const timerEl = document.querySelector("[data-exam-timer]");
    if (timerEl) {
      let remaining = Math.max(0, Number(timerEl.dataset.examTimer || 3600));
      const examForm = document.querySelector("form[data-assessment-submit]");
      let hasAutoSubmitted = false;

      const tick = () => {
        const m = String(Math.floor(remaining / 60)).padStart(2, "0");
        const s = String(remaining % 60).padStart(2, "0");
        timerEl.textContent = `${m}:${s}`;

        if (remaining <= 60) {
          timerEl.style.color = "var(--red, #ef4444)";
          timerEl.style.borderColor = "rgba(239, 68, 68, 0.4)";
        } else if (remaining <= 300) {
          timerEl.style.color = "var(--warning, #f59e0b)";
        }

        if (remaining <= 0) {
          timerEl.textContent = "00:00";
          if (examForm && !hasAutoSubmitted) {
            hasAutoSubmitted = true;
            if (window.CVUi) {
              CVUi.toast("انتهى وقت الاختبار المحدد! جاري إرسال وتسليم إجاباتك تلقائياً...");
            }
            // Disable all interactive radio/text inputs to freeze state
            examForm.querySelectorAll("input, textarea").forEach((el) => {
              el.readOnly = true;
            });
            setTimeout(() => {
              examForm.requestSubmit ? examForm.requestSubmit() : examForm.submit();
            }, 600);
          }
          return;
        }
        remaining -= 1;
        setTimeout(tick, 1000);
      };
      tick();
    }

    const buttons = document.querySelectorAll("[data-question]");
    const panels = document.querySelectorAll("[data-question-panel]");
    if (!buttons.length) return;

    function show(id) {
      buttons.forEach((btn) => btn.classList.toggle("current", btn.dataset.question === id));
      panels.forEach((panel) => panel.classList.toggle("hidden", panel.dataset.questionPanel !== id));
    }

    buttons.forEach((btn) => {
      btn.addEventListener("click", () => show(btn.dataset.question));
    });

    // Mark questions as done whenever answered
    panels.forEach((panel) => {
      const qId = panel.dataset.questionPanel;
      const navBtn = document.querySelector(`.q-nav button[data-question="${qId}"]`);

      const checkAnswered = () => {
        const checkedRadio = panel.querySelector("input[type=radio]:checked");
        const textarea = panel.querySelector("textarea");
        const isAnswered = checkedRadio || (textarea && textarea.value.trim().length > 0);
        if (navBtn) {
          navBtn.classList.toggle("done", Boolean(isAnswered));
        }
      };

      panel.querySelectorAll("input[type=radio]").forEach((radio) => {
        radio.addEventListener("change", checkAnswered);
      });
      const textarea = panel.querySelector("textarea");
      if (textarea) {
        textarea.addEventListener("input", checkAnswered);
      }
      checkAnswered();
    });

    document.querySelectorAll("[data-exam-nav]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const current = document.querySelector(".q-nav button.current");
        const all = [...buttons];
        const index = all.indexOf(current);
        const next = btn.dataset.examNav === "next" ? all[index + 1] : all[index - 1];
        if (next) {
          next.click();
        }
      });
    });

    document.querySelectorAll("form[data-assessment-submit]").forEach((form) => {
      form.addEventListener("submit", () => {
        const submitButtons = form.querySelectorAll("button[type=submit]");
        submitButtons.forEach((button) => {
          button.disabled = true;
          button.setAttribute("aria-disabled", "true");
          button.style.opacity = "0.8";
          button.style.pointerEvents = "none";
          button.innerHTML = '<span class="material-symbols-outlined" style="font-size:18px;vertical-align:middle;margin-left:6px">sync</span> جاري الإرسال وحفظ الإجابات...';
        });
      });
    });
  }

  window.CVExams = { bindExam };
})();
