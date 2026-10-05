/* ==========================================================================
   CampusFix - student.js
   Handles interactive behaviour on student-facing pages:
     - dashboard.html   : search box filters the service category tiles
     - services.html    : search box + category dropdown filter service cards
     - request-service.html : validates the request form before submitting
     - my-requests.html : status dropdown filters the requests table
   ========================================================================== */

document.addEventListener("DOMContentLoaded", function () {

  setupDashboardSearch();
  setupServicesSearchAndFilter();
  setupRequestServiceValidation();
  setupMyRequestsFilter();

});

/* ---------------------------------------------------------------------
   Dashboard: search box filters the service category tiles
--------------------------------------------------------------------- */
function setupDashboardSearch() {
  var searchInput = document.getElementById("dashboardSearch");
  if (!searchInput) return;

  var items = document.querySelectorAll(".dashboard-service-item");

  searchInput.addEventListener("input", function () {
    var keyword = searchInput.value.trim().toLowerCase();

    items.forEach(function (item) {
      var name = item.getAttribute("data-name");
      var matches = name.indexOf(keyword) !== -1;
      item.classList.toggle("d-none", !matches);
    });
  });
}

/* ---------------------------------------------------------------------
   Services page: search box + category filter dropdown
--------------------------------------------------------------------- */
function setupServicesSearchAndFilter() {
  var searchInput = document.getElementById("serviceSearch");
  var filterSelect = document.getElementById("serviceFilter");
  var noResultsBox = document.getElementById("noServiceResults");
  if (!searchInput || !filterSelect) return;

  var cards = document.querySelectorAll(".service-card-item");

  function applyFilters() {
    var keyword = searchInput.value.trim().toLowerCase();
    var category = filterSelect.value;
    var visibleCount = 0;

    cards.forEach(function (card) {
      var name = card.getAttribute("data-name");
      var matchesKeyword = name.indexOf(keyword) !== -1;
      var matchesCategory = category === "all" || name === category;
      var isVisible = matchesKeyword && matchesCategory;

      card.classList.toggle("d-none", !isVisible);
      if (isVisible) visibleCount++;
    });

    if (noResultsBox) {
      noResultsBox.classList.toggle("d-none", visibleCount !== 0);
    }
  }

  searchInput.addEventListener("input", applyFilters);
  filterSelect.addEventListener("change", applyFilters);
}

/* ---------------------------------------------------------------------
   Request Service form: simple validation before submitting
--------------------------------------------------------------------- */
function setupRequestServiceValidation() {
  var form = document.getElementById("requestServiceForm");
  if (!form) return;

  form.addEventListener("submit", function (event) {
    var errorBox = document.getElementById("requestErrorBox");
    hideFormError(errorBox);

    var service = form.service.value;
    var location = form.location.value.trim();
    var roomNumber = form.room_number.value.trim();
    var description = form.description.value.trim();

    if (service === "") {
      event.preventDefault();
      showFormError(errorBox, "Please select a service.");
      return;
    }

    if (location === "" || roomNumber === "") {
      event.preventDefault();
      showFormError(errorBox, "Please enter both the location and room number.");
      return;
    }

    if (description.length < 10) {
      event.preventDefault();
      showFormError(errorBox, "Please describe the problem in a bit more detail (at least 10 characters).");
      return;
    }

    // Valid - the form submits normally to Flask from here.
  });
}

/* ---------------------------------------------------------------------
   My Requests page: status dropdown filters the table rows
--------------------------------------------------------------------- */
function setupMyRequestsFilter() {
  var filterSelect = document.getElementById("statusFilter");
  if (!filterSelect) return;

  var rows = document.querySelectorAll(".my-request-row");

  filterSelect.addEventListener("change", function () {
    var selectedStatus = filterSelect.value;

    rows.forEach(function (row) {
      var status = row.getAttribute("data-status");
      var isVisible = selectedStatus === "all" || status === selectedStatus;
      row.classList.toggle("d-none", !isVisible);
    });
  });
}
