/* ==========================================================================
   CampusFix - main.js
   Small helpers shared by every page. Page-specific logic lives in
   auth.js (login/register), student.js (student pages) and staff.js
   (staff pages) so each file stays easy to read.
   ========================================================================== */

document.addEventListener("DOMContentLoaded", function () {

  // Automatically close alert boxes (like error messages) after 5 seconds,
  // so old error messages don't stay on screen forever.
  var alerts = document.querySelectorAll(".alert:not(.d-none)");
  alerts.forEach(function (alertBox) {
    setTimeout(function () {
      // Only auto-dismiss alerts that Bootstrap knows how to close
      var closeBtn = alertBox.querySelector(".btn-close");
      if (closeBtn) {
        closeBtn.click();
      }
    }, 5000);
  });

});

/**
 * Small reusable helper: shows a message inside an alert box element.
 * Used by auth.js and student.js for client-side validation messages.
 */
function showFormError(boxElement, message) {
  if (!boxElement) return;
  boxElement.textContent = message;
  boxElement.classList.remove("d-none");
}

function hideFormError(boxElement) {
  if (!boxElement) return;
  boxElement.classList.add("d-none");
  boxElement.textContent = "";
}
