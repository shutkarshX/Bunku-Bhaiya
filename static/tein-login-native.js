(() => {
  "use strict";

  function boot() {
    const original = document.querySelector('#login-section form[action="/get-attendance"]');
    if (!original || original.dataset.teinNativeLogin) return;

    // tein-shell previously intercepted this form with fetch() + document.write().
    // That can leave the login scene stuck when the portal takes longer than the
    // animation or returns an error page. Let the browser perform the real POST.
    const form = original.cloneNode(true);
    original.replaceWith(form);
    form.dataset.teinNativeLogin = "true";

    const manualFields = form.querySelector("#manual-login-fields");
    const generateFields = form.querySelector("#generate-login-fields");
    const manualButton = form.querySelector("#manual-login-button");
    const generateButton = form.querySelector("#generate-login-button");
    const manualInput = form.querySelector("#manual-username");
    const generatedInput = form.querySelector("#generated-username-input");
    const manualHidden = form.querySelector("#manual-username-input");
    const yearEl = form.querySelector("#admission-year");
    const branchEl = form.querySelector("#branch");
    const numberEl = form.querySelector("#student-number");
    const display = form.querySelector("#generated-username");

    const updateGenerated = () => {
      if (!yearEl || !branchEl || !numberEl) return;
      const year = yearEl.value.trim();
      const branch = branchEl.value.trim().toUpperCase();
      const number = numberEl.value.trim();
      const valid = /^\d{4}$/.test(year) && /^[A-Z0-9]+$/.test(branch) && /^\d{3}$/.test(number);
      const username = valid ? `0${year.slice(-2)}1${branch}${number}@niet.co.in` : "—";
      if (display) display.textContent = username;
      if (generatedInput) {
        generatedInput.value = valid ? username : "";
        generatedInput.disabled = !valid;
      }
    };

    const setMethod = (method) => {
      const manual = method === "manual";
      if (manualFields) manualFields.style.display = manual ? "block" : "none";
      if (generateFields) generateFields.style.display = manual ? "none" : "block";
      manualButton?.classList.toggle("is-selected", manual);
      generateButton?.classList.toggle("is-selected", !manual);
      if (manualInput) manualInput.required = manual;
      if (manualHidden) manualHidden.disabled = !manual;
      if (generatedInput) generatedInput.disabled = manual;
      if (!manual) updateGenerated();
    };

    window.setLoginMethod = setMethod;
    window.updateGeneratedUsername = updateGenerated;
    window.updateManualUsername = () => {
      if (!manualInput || !manualHidden) return;
      let value = manualInput.value.trim();
      if (value && !/@niet\.co\.in$/i.test(value)) value += "@niet.co.in";
      manualHidden.value = value;
      manualHidden.disabled = !value;
    };

    yearEl?.addEventListener("change", updateGenerated);
    branchEl?.addEventListener("input", updateGenerated);
    numberEl?.addEventListener("input", updateGenerated);

    setMethod("generate");

    // Keep the cinematic scene, but do not block the actual form navigation.
    window.showLoading = () => {
      const scene = document.querySelector(".tein-login-scene");
      if (!scene) return true;
      scene.classList.add("is-loading", "is-dashing");
      scene.style.pointerEvents = "none";
      const status = scene.querySelector(".tein-login-status");
      if (status) {
        status.textContent = "Connecting to the NIET portal";
        status.classList.add("is-visible");
      }
      return true;
    };
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
