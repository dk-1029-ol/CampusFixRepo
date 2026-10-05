/* ==========================================================================
   CampusFix - auth.js
   Handles the login and register pages:
     - Show/hide password
     - Basic client-side validation before the form is submitted
   The form still submits normally to Flask - we only stop it (preventDefault)
   when something is invalid, so the user can fix it first.
   ========================================================================== */

document.addEventListener("DOMContentLoaded", function () {

  setupPasswordToggle("togglePassword", "password", "togglePasswordIcon");
  setupPasswordToggle("toggleConfirmPassword", "confirm_password", "toggleConfirmPasswordIcon");

  var loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", handleLoginSubmit);
  }

  var registerForm = document.getElementById("registerForm");
  if (registerForm) {
    registerForm.addEventListener("submit", handleRegisterSubmit);
  }

});

/**
 * Toggles a password field between hidden (type="password") and
 * visible (type="text"), and swaps the eye icon to match.
 */
function setupPasswordToggle(buttonId, inputId, iconId) {
  var button = document.getElementById(buttonId);
  var input = document.getElementById(inputId);
  var icon = document.getElementById(iconId);
  if (!button || !input || !icon) return;

  button.addEventListener("click", function () {
    var isHidden = input.getAttribute("type") === "password";
    input.setAttribute("type", isHidden ? "text" : "password");
    icon.classList.toggle("bi-eye");
    icon.classList.toggle("bi-eye-slash");
  });
}

function handleLoginSubmit(event) {
  var form = event.target;
  var errorBox = document.getElementById("loginErrorBox");
  hideFormError(errorBox);

  var email = form.email.value.trim();
  var password = form.password.value;

  if (!isValidEmail(email)) {
    event.preventDefault();
    showFormError(errorBox, "Please enter a valid email address.");
    return;
  }

  if (password.length === 0) {
    event.preventDefault();
    showFormError(errorBox, "Please enter your password.");
    return;
  }

  // If we reach here, the form is valid and will submit normally to Flask.
}

function handleRegisterSubmit(event) {
  var form = event.target;
  var errorBox = document.getElementById("registerErrorBox");
  hideFormError(errorBox);

  var fullName = form.full_name.value.trim();
  var studentId = form.student_id.value.trim();
  var email = form.email.value.trim();
  var phone = form.phone.value.trim();
  var department = form.department.value;
  var year = form.year.value;
  var password = form.password.value;
  var confirmPassword = form.confirm_password.value;

  if (fullName === "" || studentId === "") {
    event.preventDefault();
    showFormError(errorBox, "Please fill in your name and student ID.");
    return;
  }

  if (!isValidEmail(email)) {
    event.preventDefault();
    showFormError(errorBox, "Please enter a valid college email address.");
    return;
  }

  if (!isValidPhone(phone)) {
    event.preventDefault();
    showFormError(errorBox, "Please enter a valid 10-digit phone number.");
    return;
  }

  if (department === "" || year === "") {
    event.preventDefault();
    showFormError(errorBox, "Please select your department and year.");
    return;
  }

  if (password.length < 6) {
    event.preventDefault();
    showFormError(errorBox, "Password must be at least 6 characters long.");
    return;
  }

  if (password !== confirmPassword) {
    event.preventDefault();
    showFormError(errorBox, "Passwords do not match.");
    return;
  }

  // If we reach here, the form is valid and will submit normally to Flask.
}

function isValidEmail(email) {
  // Simple, beginner-friendly email pattern - good enough for form validation.
  var pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return pattern.test(email);
}

function isValidPhone(phone) {
  // Expects exactly 10 digits.
  var pattern = /^[0-9]{10}$/;
  return pattern.test(phone);
}
