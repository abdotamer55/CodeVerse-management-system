(function () {
  document.addEventListener("DOMContentLoaded", () => {
    if (window.CVComponents) CVComponents.mountShell();
    if (window.CVNav) CVNav.bindNavigation();
    if (window.CVUi) CVUi.bindUi();
    if (window.CVForms) CVForms.bindForms();
    if (window.CVExams) CVExams.bindExam();
  });
})();
