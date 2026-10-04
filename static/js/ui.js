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

    function normalizeSearch(str) {
      if (!str) return "";
      return str
        .toString()
        .toLowerCase()
        .replace(/[أإآ]/g, "ا")
        .replace(/ة/g, "ه")
        .replace(/ى/g, "ي")
        .replace(/[\u064B-\u065F]/g, "")
        .trim();
    }

    function applyTableFilters(table) {
      if (!table) return;
      const searchInput = document.querySelector(`[data-table-search="#${table.id}"]`);
      const filterSelect = document.querySelector(`[data-filter-select="#${table.id}"]`);

      const q = searchInput ? normalizeSearch(searchInput.value) : "";
      const filterVal = filterSelect ? filterSelect.value : "all";

      const rows = table.querySelectorAll("tbody tr:not(.no-results-row)");
      let visibleCount = 0;

      rows.forEach((row) => {
        const rowText = normalizeSearch(row.textContent);
        const rowFilter = row.getAttribute("data-filter") || "";

        const matchesSearch = !q || rowText.includes(q);
        const matchesFilter = filterVal === "all" || rowFilter === filterVal || rowFilter.includes(filterVal);

        if (matchesSearch && matchesFilter) {
          row.style.display = "";
          visibleCount++;
        } else {
          row.style.display = "none";
        }
      });

      let noResultsRow = table.querySelector(".no-results-row");
      if (visibleCount === 0 && (q || filterVal !== "all")) {
        if (!noResultsRow) {
          noResultsRow = document.createElement("tr");
          noResultsRow.className = "no-results-row";
          const colSpan = table.querySelectorAll("thead th").length || 8;
          noResultsRow.innerHTML = `
            <td colspan="${colSpan}" style="text-align:center;padding:3rem 1rem;color:var(--muted)">
              <div style="display:flex;flex-direction:column;align-items:center;gap:0.5rem">
                <span class="material-symbols-outlined" style="font-size:2.2rem;opacity:0.4">search_off</span>
                <strong style="font-size:1.05rem">لا توجد نتائج مطابقة</strong>
                <span style="font-size:0.85rem">تأكد من كتابة الاسم أو رقم القيد بشكل صحيح، أو جرب تصفية أخرى.</span>
              </div>
            </td>
          `;
          const tbody = table.querySelector("tbody");
          if (tbody) tbody.appendChild(noResultsRow);
        }
        noResultsRow.style.display = "";
      } else if (noResultsRow) {
        noResultsRow.style.display = "none";
      }
    }

    // Bind table search inputs
    document.querySelectorAll("[data-table-search]").forEach((input) => {
      const table = document.querySelector(input.dataset.tableSearch);
      if (!table) return;

      const trigger = () => applyTableFilters(table);
      input.addEventListener("input", trigger);
      input.addEventListener("search", trigger);
      input.addEventListener("paste", () => setTimeout(trigger, 10));

      // Trigger immediately if input already has text (e.g. from server query param)
      if (input.value && input.value.trim()) {
        trigger();
      }
    });

    // Bind filter dropdowns
    document.querySelectorAll("[data-filter-select]").forEach((select) => {
      const table = document.querySelector(select.dataset.filterSelect);
      if (!table) return;
      select.addEventListener("change", () => applyTableFilters(table));
    });

    // Global Navbar Search Bar Handler
    document.querySelectorAll("[data-global-search]").forEach((input) => {
      input.addEventListener("input", () => {
        const localSearch = document.querySelector("[data-table-search]");
        if (localSearch) {
          localSearch.value = input.value;
          const table = document.querySelector(localSearch.dataset.tableSearch);
          if (table) applyTableFilters(table);
        }
      });

      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          const query = input.value.trim();
          if (!query) return;
          const localSearch = document.querySelector("[data-table-search]");
          if (localSearch) {
            localSearch.value = query;
            const table = document.querySelector(localSearch.dataset.tableSearch);
            if (table) applyTableFilters(table);
          } else {
            // Navigate to students search if in admin context, or lessons if student
            const isAdmin = window.location.pathname.startsWith("/admin");
            window.location.href = isAdmin 
              ? `/admin/students?q=${encodeURIComponent(query)}`
              : `/student/lessons?q=${encodeURIComponent(query)}`;
          }
        }
      });
    });
  }

  window.CVUi = { toast, openTarget, closeTarget, bindUi };
})();
