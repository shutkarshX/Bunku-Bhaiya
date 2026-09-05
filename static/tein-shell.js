(() => {
  "use strict";

  function setupLogin() {
    const manualFields = document.getElementById("manual-login-fields");
    const generateFields = document.getElementById("generate-login-fields");
    const manualButton = document.getElementById("manual-login-button");
    const generateButton = document.getElementById("generate-login-button");
    const manualInput = document.getElementById("manual-username");
    const generatedInput = document.getElementById("generated-username-input");
    const manualHidden = document.getElementById("manual-username-input");
    const yearEl = document.getElementById("admission-year");
    const branchEl = document.getElementById("branch");
    const numberEl = document.getElementById("student-number");
    if (!manualFields || !generateFields) return;

    const updateGeneratedUsername = () => {
      if (!yearEl || !branchEl || !numberEl) return;
      const year = yearEl.value;
      const branch = branchEl.value.trim().toLowerCase();
      const number = numberEl.value.trim();
      const valid = /^\d{3}$/.test(number) && /^\d+$/.test(year) && branch.length > 0;
      const yearCode = "0" + String(Number(year) + 1).slice(-2) + "1";
      const username = valid ? `${yearCode}${branch}${number}@niet.co.in` : "—";
      const display = document.getElementById("generated-username");
      if (display) display.textContent = username;
      if (generatedInput) generatedInput.value = valid ? username : "";
    };

    const setMethod = (method) => {
      const manual = method === "manual";
      manualFields.style.setProperty("display", manual ? "block" : "none", "important");
      generateFields.style.setProperty("display", manual ? "none" : "block", "important");
      if (manualButton) manualButton.classList.toggle("is-selected", manual);
      if (generateButton) generateButton.classList.toggle("is-selected", !manual);
      if (manualInput) manualInput.required = manual;
      if (manualHidden) manualHidden.disabled = !manual;
      if (generatedInput) generatedInput.disabled = manual;
      if (!manual) updateGeneratedUsername();
    };

    window.setLoginMethod = setMethod;
    window.updateGeneratedUsername = updateGeneratedUsername;
    window.updateManualUsername = () => {
      if (!manualInput || !manualHidden) return;
      let value = manualInput.value.trim();
      if (value && !value.includes("@")) value += "@niet.co.in";
      manualHidden.value = value;
    };

    if (yearEl) yearEl.addEventListener("change", updateGeneratedUsername);
    if (branchEl) branchEl.addEventListener("input", updateGeneratedUsername);
    if (numberEl) numberEl.addEventListener("input", updateGeneratedUsername);
    setMethod("generate");
  }

  function loadStyle(href) {
    if (document.querySelector(`link[href="${href}"]`)) return;
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }

  async function loadAlphaVideo(video) {
    const response = await fetch("/static/tein-zenitsu-alpha.webm", { cache: "force-cache" });
    if (!response.ok) throw new Error("Zenitsu asset unavailable");
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    video.src = url;
    video.dataset.objectUrl = url;
    await new Promise((resolve, reject) => {
      video.addEventListener("loadedmetadata", resolve, { once: true });
      video.addEventListener("error", reject, { once: true });
      video.load();
    });
  }

  function setupLoginScene() {
    const loginSection = document.getElementById("login-section");
    const form = loginSection?.querySelector('form[action="/get-attendance"]');
    if (!loginSection || !form || document.querySelector(".tein-login-scene")) return;

    loadStyle("/static/tein-login.css");
    loadStyle("/static/tein-login-zenitsu.css");

    const scene = document.createElement("div");
    scene.className = "tein-login-scene";
    scene.setAttribute("aria-label", "TEIN login");

    const character = document.createElement("video");
    character.className = "tein-login-character";
    character.muted = true;
    character.playsInline = true;
    character.preload = "auto";
    character.setAttribute("aria-hidden", "true");

    const veil = document.createElement("div"); veil.className = "tein-login-veil";
    const noise = document.createElement("div"); noise.className = "tein-login-noise";
    const glow = document.createElement("div"); glow.className = "tein-login-glow";
    const status = document.createElement("div"); status.className = "tein-login-status";
    const content = document.createElement("div"); content.className = "tein-login-content";

    loginSection.className = "tein-login-card";
    const brand = document.createElement("div"); brand.className = "tein-login-brand"; brand.textContent = "TEIN / ATTENDANCE";
    loginSection.insertBefore(brand, loginSection.firstChild);
    if (!loginSection.querySelector(".tein-login-tagline")) {
      const tagline = document.createElement("div"); tagline.className = "tein-login-tagline"; tagline.textContent = "Discipline today. Freedom tomorrow."; loginSection.appendChild(tagline);
    }
    form.querySelector('button[type="submit"]')?.classList.add("tein-login-submit");
    content.appendChild(loginSection);
    scene.append(veil, character, glow, noise, content, status);
    document.body.appendChild(scene);
    document.documentElement.style.overflow = "hidden";
    document.body.style.overflow = "hidden";

    let clipLoaded = false;
    let clipPromise = loadAlphaVideo(character).then(() => { clipLoaded = true; }).catch(() => false);

    let started = false;
    const setStatus = (text) => { status.textContent = text; status.classList.add("is-visible"); };
    const restoreOnError = (message) => {
      scene.classList.remove("is-loading", "is-dashing", "is-restoring");
      scene.style.pointerEvents = "auto";
      started = false;
      character.pause();
      setStatus(message);
      setTimeout(() => status.classList.remove("is-visible"), 2600);
    };

    const playBurst = async () => {
      await clipPromise;
      if (!clipLoaded) return;
      try { character.currentTime = 0; await character.play(); } catch (_) {}
      setTimeout(() => character.pause(), Math.max(1200, ((character.duration || 1.8) * 1000) - 40));
    };

    const startSequence = () => {
      if (started) return;
      started = true;
      setStatus("Connecting to the NIET portal");
      scene.classList.add("is-loading");
      scene.style.pointerEvents = "none";

      const responsePromise = fetch(form.action, {
        method: "POST", body: new FormData(form), credentials: "same-origin",
        headers: { "X-Requested-With": "TEIN" }
      }).then(async response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.text();
      });

      setTimeout(() => {
        setStatus("Focus awakened");
        scene.classList.add("is-dashing");
        playBurst();
      }, 140);

      const minimumSequence = new Promise(resolve => setTimeout(resolve, 2050));
      Promise.all([responsePromise, minimumSequence]).then(([html]) => {
        setStatus("Attendance retrieved");
        scene.classList.remove("is-dashing");
        scene.classList.add("is-restoring");
        setTimeout(() => { document.open(); document.write(html); document.close(); }, 620);
      }).catch(() => restoreOnError("Could not reach the portal — try again"));
    };

    window.showLoading = startSequence;
    form.addEventListener("submit", event => { event.preventDefault(); startSequence(); });
  }

  function setupCalculatorInteractions() {
    document.querySelectorAll('form[action^="/sessional-"]').forEach(form => {
      if (form.dataset.teinCalcBound) return;
      form.dataset.teinCalcBound = "true";
      const refresh = () => window.updateLeavePreview?.(form);
      form.querySelectorAll("input").forEach(input => input.addEventListener("input", refresh));
      refresh();
    });
  }

  function setupShell() {
    const nav = document.querySelector(".tein-app-nav");
    if (!nav) return;
    const navButtons = [...nav.querySelectorAll("button")];
    const viewNames = ["home", "plan", "subjects"];
    navButtons.slice(0, 3).forEach((button, index) => { if (!button.dataset.view) button.dataset.view = viewNames[index]; });
    const initialViews = [...document.querySelectorAll(".tein-app-view[data-view]")];
    if (!viewNames.every(name => initialViews.some(view => view.dataset.view === name))) return;

    let moreButton = nav.querySelector('button[data-view="more"]');
    let moreView = document.querySelector('.tein-app-view[data-view="more"]');
    if (!moreButton) { moreButton = document.createElement("button"); moreButton.type = "button"; moreButton.dataset.view = "more"; moreButton.setAttribute("aria-selected", "false"); moreButton.textContent = "More"; nav.appendChild(moreButton); }
    if (!moreView) { moreView = document.createElement("section"); moreView.className = "tein-app-view tein-more-view"; moreView.dataset.view = "more"; moreView.setAttribute("aria-label", "More"); moreView.hidden = true; nav.parentNode.insertBefore(moreView, nav.nextElementSibling); }

    const allButtons = [...nav.querySelectorAll("button[data-view]")];
    const allViews = [...document.querySelectorAll(".tein-app-view[data-view]")];
    if (!moreView.dataset.ready) {
      moreView.dataset.ready = "true";
      moreView.innerHTML = `<div class="tein-more-header"><span class="tein-eyebrow">TEIN controls</span><h2>More</h2><p>Keep secondary controls here so Home stays focused on attendance.</p></div><div class="tein-more-grid"><div class="tein-more-panel"><div><strong>Appearance</strong><span>Auto follows your device. You can also force Light or Dark.</span></div><div class="tein-more-control" data-control="theme"></div></div><div class="tein-more-panel"><div><strong>Interface sound</strong><span>Tactile feedback for important interactions.</span></div><div class="tein-more-control" data-control="sound"></div></div></div><div class="tein-more-note"><strong>Portal data</strong><span>Attendance and subject history shown in TEIN come from the existing NIET portal data.</span></div>`;
      const theme = document.querySelector(".tein-theme-toggle"); const sound = document.querySelector(".tein-sound-toggle");
      moreView.querySelector('[data-control="theme"]')?.appendChild(theme); moreView.querySelector('[data-control="sound"]')?.appendChild(sound);
    }
    const activate = (viewName, updateHash = true) => {
      allButtons.forEach(button => { const active = button.dataset.view === viewName; button.classList.toggle("is-active", active); button.setAttribute("aria-selected", String(active)); });
      allViews.forEach(view => { const active = view.dataset.view === viewName; view.classList.toggle("is-active", active); view.hidden = !active; });
      if (updateHash) history.replaceState?.(null, "", `#${viewName}`);
      window.TEIN?.tick?.("soft");
    };
    allButtons.forEach(button => { if (button.dataset.teinShellBound) return; button.dataset.teinShellBound = "true"; button.addEventListener("click", () => activate(button.dataset.view)); });
    document.querySelectorAll(".tein-open-plan, .tein-focus-action").forEach(button => { if (button.dataset.teinShellBound) return; button.dataset.teinShellBound = "true"; button.addEventListener("click", () => activate("plan")); });
    const requested = location.hash.replace(/^#/, ""); activate(allButtons.some(button => button.dataset.view === requested) ? requested : "home", false);
  }

  document.addEventListener("DOMContentLoaded", () => { setupLogin(); setupLoginScene(); setupCalculatorInteractions(); setupShell(); });
})();
