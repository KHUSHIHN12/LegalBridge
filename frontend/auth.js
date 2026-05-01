const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const REGISTERED_USER_KEY = "legalbridgeRegisteredUser";
const CURRENT_USER_KEY = "legalbridgeCurrentUser";

function readStoredJson(key) {
  try {
    const value = window.localStorage.getItem(key);
    return value ? JSON.parse(value) : null;
  } catch (error) {
    return null;
  }
}

function writeStoredJson(key, value) {
  window.localStorage.setItem(key, JSON.stringify(value));
}

function buildUserNameFromEmail(email) {
  const base = (email || "LegalBridge User").split("@")[0].replace(/[._-]+/g, " ").trim();
  return base
    .split(" ")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ") || "LegalBridge User";
}

function setCurrentUser(user) {
  writeStoredJson(CURRENT_USER_KEY, user);
}

function getCurrentUser() {
  return readStoredJson(CURRENT_USER_KEY);
}

function updateCurrentUserUI() {
  const userSlot = document.querySelector("[data-current-user]");
  if (!userSlot) return;

  const currentUser = getCurrentUser();
  userSlot.textContent = currentUser?.fullName || currentUser?.email || "Guest";
}

function initNavToggle() {
  const toggle = document.querySelector("[data-nav-toggle]");
  const menu = document.querySelector("[data-nav-menu]");

  if (!toggle || !menu) return;

  toggle.addEventListener("click", () => {
    menu.classList.toggle("open");
  });
}

function togglePasswordVisibility(button) {
  const input = button.closest(".input-shell")?.querySelector("input");
  const icon = button.querySelector("i");

  if (!input || !icon) return;

  const nextType = input.type === "password" ? "text" : "password";
  input.type = nextType;
  icon.className = nextType === "password" ? "fa-regular fa-eye" : "fa-regular fa-eye-slash";
}

function getStrengthDetails(password) {
  let score = 0;
  if (password.length >= 8) score += 1;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;

  if (!password) return { score: 0, label: "Choose a strong password", tone: "weak" };
  if (score <= 1) return { score, label: "Weak password", tone: "weak" };
  if (score <= 3) return { score, label: "Moderate password", tone: "medium" };
  return { score, label: "Strong password", tone: "strong" };
}

function updateStrengthMeter(form) {
  const passwordInput = form.querySelector("[data-password-source]");
  const strengthCopy = form.querySelector("[data-password-strength]");
  const segments = form.querySelectorAll(".strength-meter span");

  if (!passwordInput || !strengthCopy || !segments.length) return;

  const { score, label, tone } = getStrengthDetails(passwordInput.value);
  strengthCopy.textContent = label;

  segments.forEach((segment, index) => {
    segment.className = "";
    if (index < score) {
      segment.classList.add("active", tone);
    }
  });
}

function setFieldState(fieldGroup, message, valid) {
  const messageSlot = fieldGroup.querySelector(".field-message");
  fieldGroup.classList.remove("is-valid", "is-invalid");
  fieldGroup.classList.add(valid ? "is-valid" : "is-invalid");
  if (messageSlot) messageSlot.textContent = message;
}

function clearFieldState(fieldGroup) {
  if (!fieldGroup) return;
  const messageSlot = fieldGroup.querySelector(".field-message");
  fieldGroup.classList.remove("is-valid", "is-invalid");
  if (messageSlot) messageSlot.textContent = "";
}

function validateInput(input, form) {
  const fieldGroup = input.closest(".field-group");
  const type = input.dataset.validate;
  const value = input.type === "checkbox" ? input.checked : input.value.trim();

  if (type === "terms") {
    const message = form.querySelector(".checkbox-message");
    if (!input.checked) {
      if (message) message.textContent = "You must accept the Terms & Conditions.";
      return false;
    }
    if (message) message.textContent = "";
    return true;
  }

  if (!fieldGroup) return true;

  if (!value) {
    setFieldState(fieldGroup, "This field is required.", false);
    return false;
  }

  if (type === "name" && String(value).length < 3) {
    setFieldState(fieldGroup, "Please enter your full name.", false);
    return false;
  }

  if (type === "email" && !EMAIL_PATTERN.test(String(value))) {
    setFieldState(fieldGroup, "Enter a valid email address.", false);
    return false;
  }

  if (type === "password" && String(value).length < 8) {
    setFieldState(fieldGroup, "Password must be at least 8 characters.", false);
    return false;
  }

  if (type === "confirm-password") {
    const password = form.querySelector("[data-password-source]")?.value || "";
    if (value !== password) {
      setFieldState(fieldGroup, "Passwords do not match.", false);
      return false;
    }
  }

  setFieldState(fieldGroup, "Looks good.", true);
  return true;
}

function validateForm(form) {
  const inputs = form.querySelectorAll("[data-validate]");
  let valid = true;

  inputs.forEach((input) => {
    const isValid = validateInput(input, form);
    if (!isValid) valid = false;
  });

  return valid;
}

function showToast(message) {
  const toast = document.getElementById("authToast");
  const label = toast?.querySelector("[data-toast-message]");
  if (!toast || !label) return;

  label.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2600);
}

function handleSubmit(form) {
  const type = form.dataset.authForm;
  const button = form.querySelector(".primary-button");
  const originalLabel = button?.dataset.submitLabel || "";

  form.addEventListener("submit", (event) => {
    event.preventDefault();

    if (!validateForm(form)) {
      showToast("Please review the highlighted fields.");
      return;
    }

    if (button) {
      button.classList.add("is-loading");
      const label = button.querySelector("span");
      if (label) label.textContent = type === "signup" ? "Creating Account..." : "Signing In...";
    }

    window.setTimeout(() => {
      if (button) {
        button.classList.remove("is-loading");
        const label = button.querySelector("span");
        if (label) label.textContent = originalLabel;
      }

      if (type === "signup") {
        const fullName = form.querySelector('input[name="fullName"]')?.value.trim() || "LegalBridge User";
        const email = form.querySelector('input[name="email"]')?.value.trim() || "";
        writeStoredJson(REGISTERED_USER_KEY, { fullName, email });
        showToast("Account created successfully. Redirecting to sign in...");
        window.setTimeout(() => {
          window.location.href = "./signin.html";
        }, 1000);
      } else {
        const email = form.querySelector('input[name="email"]')?.value.trim() || "";
        const registeredUser = readStoredJson(REGISTERED_USER_KEY);
        const matchedUser = registeredUser && registeredUser.email === email
          ? registeredUser
          : { fullName: buildUserNameFromEmail(email), email };
        setCurrentUser(matchedUser);
        showToast("Login successful. Redirecting to dashboard...");
        window.setTimeout(() => {
          window.location.href = "./index.html";
        }, 1000);
      }
    }, 1400);
  });
}

function initAuthForms() {
  document.querySelectorAll("[data-auth-form]").forEach((form) => {
    const inputs = form.querySelectorAll("[data-validate]");

    inputs.forEach((input) => {
      input.addEventListener("blur", () => validateInput(input, form));
      input.addEventListener("input", () => {
        if (input.dataset.validate !== "terms") {
          clearFieldState(input.closest(".field-group"));
        }
        if (input.matches("[data-password-source]")) {
          updateStrengthMeter(form);
          const confirmInput = form.querySelector("[data-confirm-password]");
          if (confirmInput && confirmInput.value) validateInput(confirmInput, form);
        }
      });
      input.addEventListener("change", () => {
        if (input.dataset.validate === "terms") validateInput(input, form);
      });
    });

    updateStrengthMeter(form);
    handleSubmit(form);
  });
}

function initPasswordToggles() {
  document.querySelectorAll("[data-toggle-password]").forEach((button) => {
    button.addEventListener("click", () => togglePasswordVisibility(button));
  });
}

function logoutUser() {
  window.localStorage.removeItem(CURRENT_USER_KEY);
  window.location.href = "./signin.html";
}

document.addEventListener("DOMContentLoaded", () => {
  initNavToggle();
  initPasswordToggles();
  initAuthForms();
  updateCurrentUserUI();
});
