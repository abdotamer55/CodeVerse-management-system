(function () {
  function bindExam() {
    const timerEl = document.querySelector("[data-exam-timer]");
    if (timerEl) {
      let remaining = Number(timerEl.dataset.examTimer || 3600);
      const tick = () => {
        const m = String(Math.floor(remaining / 60)).padStart(2, "0");
        const s = String(remaining % 60).padStart(2, "0");
        timerEl.textContent = `${m}:${s}`;
        if (remaining <= 0) {
          window.CVUi && CVUi.toast("انتهى الوقت — هذه معاينة واجهة فقط");
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

    document.querySelectorAll("[data-exam-nav]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const current = document.querySelector(".q-nav button.current");
        const all = [...buttons];
        const index = all.indexOf(current);
        const next = btn.dataset.examNav === "next" ? all[index + 1] : all[index - 1];
        if (next) {
          current.classList.add("done");
          next.click();
        }
      });
    });
  }

  window.CVExams = { bindExam };
})();
