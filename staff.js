/* ==========================================================================
   CampusFix - staff.js
   Handles interactive behaviour on staff-facing pages:
     - staff-dashboard.html : status dropdown filters the incoming requests table
   ========================================================================== */

document.addEventListener("DOMContentLoaded", function () {
  setupStaffStatusFilter();
});

function setupStaffStatusFilter() {
  var filterSelect = document.getElementById("staffStatusFilter");
  if (!filterSelect) return;

  var rows = document.querySelectorAll(".staff-request-row");

  filterSelect.addEventListener("change", function () {
    var selectedStatus = filterSelect.value;

    rows.forEach(function (row) {
      var status = row.getAttribute("data-status");
      var isVisible = selectedStatus === "all" || status === selectedStatus;
      row.classList.toggle("d-none", !isVisible);
    });
  });
}
