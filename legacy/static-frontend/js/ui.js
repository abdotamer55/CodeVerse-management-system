(function () {
  function toast(message) {
    let host = document.querySelector(".toast-host");
    if (!host) {
      host = document.createElement("div");
      host.className = "toast-host";
      document.body.appendChild(host);
    }
    const el = document.createElement("div");
    el.className = "toast";
    el.textContent = message;
    host.appendChild(el);
    setTimeout(() => el.remove(), 2800);
  }

  function openTarget(selector) {
    const el = document.querySelector(selector);
    if (el) el.classList.add("is-open");
  }

  function closeTarget(selector) {
    const el = document.querySelector(selector);
    if (el) el.classList.remove("is-open");
  }

  function bindUi() {
    document.addEventListener("click", (event) => {
      const opener = event.target.closest("[data-open]");
      if (opener) openTarget(opener.dataset.open);

      const closer = event.target.closest("[data-close]");
      if (closer) closeTarget(closer.dataset.close);

      const backdrop = event.target.closest(".modal-backdrop, .drawer-backdrop");
      if (backdrop && event.target === backdrop) backdrop.classList.remove("is-open");

      const tab = event.target.closest("[data-tab]");
      if (tab) {
        const group = tab.dataset.tabGroup;
        document.querySelectorAll(`[data-tab-group="${group}"]`).forEach((btn) => btn.classList.remove("is-active"));
        tab.classList.add("is-active");
        document.querySelectorAll(`[data-tab-panel-group="${group}"]`).forEach((panel) => {
          panel.classList.toggle("hidden", panel.dataset.tabPanel !== tab.dataset.tab);
        });
      }

      const option = event.target.closest("[data-option]");
      if (option) {
        option.parentElement.querySelectorAll("[data-option]").forEach((item) => item.classList.remove("is-selected"));
        option.classList.add("is-selected");
      }
    });

    document.querySelectorAll("[data-table-search]").forEach((input) => {
      input.addEventListener("input", () => {
        const q = input.value.trim();
        const table = document.querySelector(input.dataset.tableSearch);
        if (!table) return;
        table.querySelectorAll("tbody tr").forEach((row) => {
          row.style.display = row.textContent.includes(q) || !q ? "" : "none";
        });
      });
    });

    document.querySelectorAll("[data-filter-select]").forEach((select) => {
      select.addEventListener("change", () => {
        const value = select.value;
        const table = document.querySelector(select.dataset.filterSelect);
        if (!table) return;
        table.querySelectorAll("tbody tr").forEach((row) => {
          const hay = row.getAttribute("data-filter") || "";
          row.style.display = value === "all" || hay.includes(value) ? "" : "none";
        });
      });
    });
  }

  window.CVUi = { toast, openTarget, closeTarget, bindUi };
})();
