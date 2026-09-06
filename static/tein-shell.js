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

  function makeSpiderRig() {
    const rig = document.createElement("div");
    rig.className = "tein-spider-rig";
    rig.setAttribute("aria-hidden", "true");
    rig.innerHTML = `
      <svg class="tein-spider-svg" viewBox="0 0 360 430" role="presentation">
        <defs>
          <linearGradient id="teinSpiderSuit" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#343b48"/><stop offset="1" stop-color="#11151d"/>
          </linearGradient>
          <linearGradient id="teinSpiderHood" x1="0" y1="0" x2="0.9" y2="1">
            <stop offset="0" stop-color="#f3eee4"/><stop offset="1" stop-color="#b9b4ab"/>
          </linearGradient>
          <filter id="teinSpiderGlow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
        </defs>
        <g class="tein-spider-web">
          <path d="M180 0 C181 42 179 78 180 111" fill="none" stroke="rgba(235,239,242,.88)" stroke-width="2"/>
          <path d="M180 16 C156 32 143 51 137 76 M180 16 C204 32 217 51 223 76 M180 42 C155 57 145 70 141 92 M180 42 C205 57 215 70 219 92" fill="none" stroke="rgba(235,239,242,.28)" stroke-width="1"/>
        </g>
        <g class="tein-spider-body">
          <ellipse cx="180" cy="239" rx="66" ry="82" fill="url(#teinSpiderSuit)" stroke="#535b69" stroke-width="2"/>
          <path d="M125 213 Q85 195 72 161 M235 213 Q275 195 288 161 M125 250 Q82 253 62 231 M235 250 Q278 253 298 231 M132 278 Q96 307 82 337 M228 278 Q264 307 278 337" fill="none" stroke="#202631" stroke-width="20" stroke-linecap="round"/>
          <path d="M124 213 Q84 194 72 161 M236 213 Q276 194 288 161 M124 250 Q82 252 62 231 M236 250 Q278 252 298 231 M132 279 Q96 307 82 337 M228 279 Q264 307 278 337" fill="none" stroke="#687180" stroke-width="4" stroke-linecap="round" opacity=".6"/>
          <path d="M151 186 Q180 171 209 186 L217 262 Q180 286 143 262Z" fill="#171c25"/>
          <path d="M159 195 L180 208 L201 195" fill="none" stroke="#d8d1c5" stroke-width="3" opacity=".65"/>
        </g>
        <g class="tein-spider-head">
          <path d="M128 130 Q137 77 180 63 Q223 77 232 130 L213 178 Q180 194 147 178Z" fill="url(#teinSpiderHood)" stroke="#8e8b86" stroke-width="2"/>
          <path d="M142 128 Q151 93 180 84 Q209 93 218 128 L205 163 Q180 178 155 163Z" fill="#151a22"/>
          <path class="tein-spider-eye tein-spider-eye-a" d="M151 119 Q164 101 176 119 Q164 139 151 145Z" fill="#f6c54b" filter="url(#teinSpiderGlow)"/>
          <path class="tein-spider-eye tein-spider-eye-b" d="M209 119 Q196 101 184 119 Q196 139 209 145Z" fill="#f6c54b" filter="url(#teinSpiderGlow)"/>
          <path d="M135 105 L119 92 M225 105 L241 92" stroke="#d7d0c5" stroke-width="6" stroke-linecap="round"/>
        </g>
      </svg>`;
    return rig;
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

    const spider = makeSpiderRig();
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
    scene.append(veil, spider, glow, noise, content, status);
    document.body.appendChild(scene);
    document.documentElement.style.overflow = "hidden";
    document.body.style.overflow = "hidden";

    let started = false;
    let raf = 0;
    let targetX = 0, targetY = 0, currentX = 0, currentY = 0;
    const head = spider.querySelector(".tein-spider-head");
    const body = spider.querySelector(".tein-spider-body");
    const setStatus = (text) => { status.textContent = text; status.classList.add("is-visible"); };

    const animateLook = () => {
      currentX += (targetX - currentX) * 0.105;
      currentY += (targetY - currentY) * 0.105;
      spider.style.setProperty("--spider-x", `${currentX.toFixed(2)}px`);
      spider.style.setProperty("--spider-y", `${currentY.toFixed(2)}px`);
      if (head) head.style.transform = `translate(${currentX * .12}px,${currentY * .08}px) rotate(${currentX * .012}deg)`;
      if (body) body.style.transform = `translate(${currentX * -.025}px,${currentY * -.015}px) rotate(${currentX * -.0025}deg)`;
      raf = requestAnimationFrame(animateLook);
    };
    animateLook();

    const move = event => {
      if (started) return;
      const x = (event.clientX / Math.max(1, window.innerWidth) - .5);
      const y = (event.clientY / Math.max(1, window.innerHeight) - .35);
      targetX = Math.max(-38, Math.min(38, x * 76));
      targetY = Math.max(-28, Math.min(28, y * 42));
      scene.style.setProperty("--cursor-x", `${event.clientX}px`);
      scene.style.setProperty("--cursor-y", `${event.clientY}px`);
    };
    window.addEventListener("pointermove", move, { passive: true });

    const restoreOnError = message => {
      scene.classList.remove("is-loading", "is-dashing", "is-restoring");
      scene.style.pointerEvents = "auto";
      started = false;
      setStatus(message);
      setTimeout(() => status.classList.remove("is-visible"), 2600);
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
      }, 180);

      const minimumSequence = new Promise(resolve => setTimeout(resolve, 1850));
      Promise.all([responsePromise, minimumSequence]).then(([html]) => {
        setStatus("Attendance retrieved");
        scene.classList.remove("is-dashing");
        scene.classList.add("is-restoring");
        setTimeout(() => { document.open(); document.write(html); document.close(); }, 620);
      }).catch(() => restoreOnError("Could not reach the portal — try again"));
    };

    window.showLoading = startSequence;
    form.addEventListener("submit", event => { event.preventDefault(); startSequence(); });
    window.addEventListener("beforeunload", () => cancelAnimationFrame(raf), { once: true });
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
