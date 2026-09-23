(function () {
  function toggleSidebar(force) {
    document.body.classList.toggle("sidebar-open", force);
  }

  function bindNavigation() {
    document.addEventListener("click", (event) => {
      if (event.target.closest("[data-sidebar-toggle]")) {
        toggleSidebar();
      }
      if (event.target.closest("[data-sidebar-close]")) {
        toggleSidebar(false);
      }
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth >= 1280) toggleSidebar(false);
    });
  }

  window.CVNav = { toggleSidebar, bindNavigation };
})();
