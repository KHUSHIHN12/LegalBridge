const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CURRENT_USER_KEY = "legalbridgeCurrentUser";
const LOGGED_IN_KEY = "legalbridge_logged_in";
const API_BASE_URL = window.location.hostname === "localhost"
  ? "http://localhost:5000"
  : "http://127.0.0.1:5000";

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

async function sendAuthRequest(path, payload) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));

  if (!response.ok || data.success === false) {
    throw new Error(data.message || "Authentication request failed.");
  }

  return data;
}

function setButtonLoading(button, loading, label) {
  if (!button) return;

  const text = button.querySelector("span");
  button.disabled = loading;
  button.classList.toggle("is-loading", loading);
  if (text) text.textContent = label;
}

function handleSubmit(form) {
  const type = form.dataset.authForm;
  const button = form.querySelector(".primary-button");
  const originalLabel = button?.dataset.submitLabel || "";

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!validateForm(form)) {
      showToast("Please review the highlighted fields.");
      return;
    }

    setButtonLoading(button, true, type === "signup" ? "Creating Account..." : "Signing In...");

    try {
      if (type === "signup") {
        const fullname = form.querySelector('input[name="fullName"]')?.value.trim() || "";
        const email = form.querySelector('input[name="email"]')?.value.trim() || "";
        const password = form.querySelector('input[name="password"]')?.value || "";

        await sendAuthRequest("/api/signup", { fullname, email, password });
        showToast("Account created successfully. Redirecting to sign in...");
        window.setTimeout(() => {
          window.location.href = "./signin.html";
        }, 1000);
      } else {
        const email = form.querySelector('input[name="email"]')?.value.trim() || "";
        const password = form.querySelector('input[name="password"]')?.value || "";
        const data = await sendAuthRequest("/api/login", { email, password });

        if (data.success !== true) {
          throw new Error(data.message || "Invalid email or password.");
        }

        window.localStorage.setItem(LOGGED_IN_KEY, "true");
        setCurrentUser(data.user || { fullName: buildUserNameFromEmail(email), email });
        window.location.href = "index.html";
      }
    } catch (error) {
      showToast(error.message || "Invalid credentials.");
    } finally {
      setButtonLoading(button, false, originalLabel);
    }
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

function initProtectedPlatformLinks() {
  document.querySelectorAll("[data-platform-link]").forEach((link) => {
    link.addEventListener("click", (event) => {
      if (window.localStorage.getItem(LOGGED_IN_KEY) === "true") return;

      event.preventDefault();
      showToast("Please sign in before opening the platform dashboard.");
      window.setTimeout(() => {
        window.location.href = "./signin.html";
      }, 800);
    });
  });
}

async function logoutUser() {
  try {
    await fetch(`${API_BASE_URL}/api/logout`, {
      method: "POST",
      credentials: "include",
    });
  } catch (error) {
    // Local logout should still proceed if the backend is temporarily unavailable.
  }
  window.localStorage.removeItem(LOGGED_IN_KEY);
  window.localStorage.removeItem(CURRENT_USER_KEY);
  window.location.href = "./signin.html";
}

document.addEventListener("DOMContentLoaded", () => {
  initNavToggle();
  initPasswordToggles();
  initAuthForms();
  initProtectedPlatformLinks();
  updateCurrentUserUI();
});
