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
    const display = document.getElementById("generated-username");

    if (!manualFields || !generateFields) return;

    const updateGeneratedUsername = () => {
      if (!yearEl || !branchEl || !numberEl) return;
      const year = String(yearEl.value || "").trim();
      const branch = branchEl.value.trim().toUpperCase();
      const number = numberEl.value.trim();
      const valid = /^\d{4}$/.test(year) && /^[A-Z0-9]+$/.test(branch) && /^\d{3}$/.test(number);
      const yearCode = valid ? `0${year.slice(-2)}1` : "";
      const username = valid ? `${yearCode}${branch}${number}@niet.co.in` : "—";
      if (display) display.textContent = username;
      if (generatedInput) {
        generatedInput.value = valid ? username : "";
        generatedInput.disabled = !valid;
      }
    };

    const setMethod = (method) => {
      const manual = method === "manual";
      manualFields.style.setProperty("display", manual ? "block" : "none", "important");
      generateFields.style.setProperty("display", manual ? "none" : "block", "important");
      manualButton?.classList.toggle("is-selected", manual);
      generateButton?.classList.toggle("is-selected", !manual);
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
      if (value && !/@niet\.co\.in$/i.test(value)) value += "@niet.co.in";
      manualHidden.value = value;
      manualHidden.disabled = !value;
    };

    yearEl?.addEventListener("change", updateGeneratedUsername);
    branchEl?.addEventListener("input", updateGeneratedUsername);
    numberEl?.addEventListener("input", updateGeneratedUsername);
    setMethod("generate");
  }

  function makeSpiderRig() {
    const rig = document.createElement("div");
    rig.className = "tein-spider-rig";
    rig.setAttribute("aria-hidden", "true");
    rig.innerHTML = `<svg class="tein-spider-svg" viewBox="0 0 360 430" role="presentation"><defs><linearGradient id="teinSpiderSuit" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#343b48"/><stop offset="1" stop-color="#11151d"/></linearGradient><linearGradient id="teinSpiderHood" x1="0" y1="0" x2="0.9" y2="1"><stop offset="0" stop-color="#f3eee4"/><stop offset="1" stop-color="#b9b4ab"/></linearGradient><filter id="teinSpiderGlow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><g class="tein-spider-web"><path d="M180 0 C181 42 179 78 180 111" fill="none" stroke="rgba(235,239,242,.88)" stroke-width="2"/><path d="M180 16 C156 32 143 51 137 76 M180 16 C204 32 217 51 223 76 M180 42 C155 57 145 70 141 92 M180 42 C205 57 215 70 219 92" fill="none" stroke="rgba(235,239,242,.28)" stroke-width="1"/></g><g class="tein-spider-body"><ellipse cx="180" cy="239" rx="66" ry="82" fill="url(#teinSpiderSuit)" stroke="#535b69" stroke-width="2"/><path d="M125 213 Q85 195 72 161 M235 213 Q275 195 288 161 M125 250 Q82 253 62 231 M235 250 Q278 253 298 231 M132 278 Q96 307 82 337 M228 278 Q264 307 278 337" fill="none" stroke="#202631" stroke-width="20" stroke-linecap="round"/><path d="M124 213 Q84 194 72 161 M236 213 Q276 194 288 161 M124 250 Q82 252 62 231 M236 250 Q278 252 298 231 M132 279 Q96 307 82 337 M228 279 Q264 307 278 337" fill="none" stroke="#687180" stroke-width="4" stroke-linecap="round" opacity=".6"/><path d="M151 186 Q180 171 209 186 L217 262 Q180 286 143 262Z" fill="#171c25"/><path d="M159 195 L180 208 L201 195" fill="none" stroke="#d8d1c5" stroke-width="3" opacity=".65"/></g><g class="tein-spider-head"><path d="M128 130 Q137 77 180 63 Q223 77 232 130 L213 178 Q180 194 147 178Z" fill="url(#teinSpiderHood)" stroke="#8e8b86" stroke-width="2"/><path d="M142 128 Q151 93 180 84 Q209 93 218 128 L205 163 Q180 178 155 163Z" fill="#151a22"/><path class="tein-spider-eye tein-spider-eye-a" d="M151 119 Q164 101 176 119 Q164 139 151 145Z" fill="#f6c54b" filter="url(#teinSpiderGlow)"/><path class="tein-spider-eye tein-spider-eye-b" d="M209 119 Q196 101 184 119 Q196 139 209 145Z" fill="#f6c54b" filter="url(#teinSpiderGlow)"/><path d="M135 105 L119 92 M225 105 L241 92" stroke="#d7d0c5" stroke-width="6" stroke-linecap="round"/></g></svg>`;
    return rig;
  }

  function setupLoginScene() {
    const loginSection = document.getElementById("login-section");
    const form = loginSection?.querySelector('form[action="/get-attendance"]');
    if (!loginSection || !form || document.querySelector(".tein-login-scene")) return;

    const loadStyle = (href) => {
      if (document.querySelector(`link[href="${href}"]`)) return;
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = href;
      document.head.appendChild(link);
    };
    loadStyle("/static/tein-login.css");
    loadStyle("/static/tein-login-spider.css");

    const scene = document.createElement("div");
    scene.className = "tein-login-scene";
    scene.setAttribute("aria-label", "TEIN login");
    const spider = makeSpiderRig();
    const veil = document.createElement("div");
    veil.className = "tein-login-veil";
    const noise = document.createElement("div");
    noise.className = "tein-login-noise";
    const glow = document.createElement("div");
    glow.className = "tein-login-glow";
    const status = document.createElement("div");
    status.className = "tein-login-status";
    const content = document.createElement("div");
    content.className = "tein-login-content";

    loginSection.className = "tein-login-card";
    if (!loginSection.querySelector(".tein-login-brand")) {
      const brand = document.createElement("div");
      brand.className = "tein-login-brand";
      brand.textContent = "TEIN / ATTENDANCE";
      loginSection.insertBefore(brand, loginSection.firstChild);
    }
    if (!loginSection.querySelector(".tein-login-tagline")) {
      const tagline = document.createElement("div");
      tagline.className = "tein-login-tagline";
      tagline.textContent = "Discipline today. Freedom tomorrow.";
      loginSection.appendChild(tagline);
    }
    form.querySelector('button[type="submit"]')?.classList.add("tein-login-submit");

    content.appendChild(loginSection);
    scene.append(veil, spider, glow, noise, content, status);
    document.body.appendChild(scene);
    document.documentElement.style.overflow = "hidden";
    document.body.style.overflow = "hidden";

    let started = false;
    let raf = 0;
    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;
    const head = spider.querySelector(".tein-spider-head");
    const body = spider.querySelector(".tein-spider-body");
    const setStatus = (text) => {
      status.textContent = text;
      status.classList.add("is-visible");
    };
    const animateLook = () => {
      currentX += (targetX - currentX) * 0.105;
      currentY += (targetY - currentY) * 0.105;
      spider.style.setProperty("--spider-x", `${currentX.toFixed(2)}px`);
      spider.style.setProperty("--spider-y", `${currentY.toFixed(2)}px`);
      if (head) head.style.transform = `translate(${currentX * 0.12}px,${currentY * 0.08}px) rotate(${currentX * 0.012}deg)`;
      if (body) body.style.transform = `translate(${currentX * -0.025}px,${currentY * -0.015}px) rotate(${currentX * -0.0025}deg)`;
      raf = requestAnimationFrame(animateLook);
    };
    animateLook();

    window.addEventListener("pointermove", (event) => {
      if (started) return;
      const x = event.clientX / Math.max(1, innerWidth) - 0.5;
      const y = event.clientY / Math.max(1, innerHeight) - 0.35;
      targetX = Math.max(-38, Math.min(38, x * 76));
      targetY = Math.max(-28, Math.min(28, y * 42));
    }, { passive: true });

    const startSequence = () => {
      if (started) return;
      started = true;
      setStatus("Connecting to the NIET portal");
      scene.classList.add("is-loading");
      scene.style.pointerEvents = "none";
      const responsePromise = fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        credentials: "same-origin",
        headers: { "X-Requested-With": "TEIN" },
      }).then(async (response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.text();
      });

      window.setTimeout(() => {
        setStatus("Focus awakened");
        scene.classList.add("is-dashing");
      }, 180);

      Promise.all([responsePromise, new Promise((resolve) => setTimeout(resolve, 1850))])
        .then(([html]) => {
          setStatus("Attendance retrieved");
          scene.classList.remove("is-dashing");
          scene.classList.add("is-restoring");
          setTimeout(() => {
            document.open();
            document.write(html);
            document.close();
          }, 620);
        })
        .catch(() => {
          scene.classList.remove("is-loading", "is-dashing", "is-restoring");
          scene.style.pointerEvents = "auto";
          started = false;
          setStatus("Could not reach the portal — try again");
          setTimeout(() => status.classList.remove("is-visible"), 2600);
        });
    };

    window.showLoading = startSequence;
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      startSequence();
    });
    window.addEventListener("beforeunload", () => cancelAnimationFrame(raf), { once: true });
  }

  function setupShell() {
    const nav = document.querySelector(".tein-app-nav");
    if (!nav) return;

    let moreButton = nav.querySelector('button[data-view="more"]');
    let moreView = document.querySelector('.tein-app-view[data-view="more"]');
    if (!moreButton) {
      moreButton = document.createElement("button");
      moreButton.type = "button";
      moreButton.dataset.view = "more";
      moreButton.setAttribute("aria-selected", "false");
      moreButton.textContent = "More";
      nav.appendChild(moreButton);
    }

    if (!moreView) {
      moreView = document.createElement("section");
      moreView.className = "tein-app-view tein-more-view";
      moreView.dataset.view = "more";
      moreView.hidden = true;
      nav.parentNode.insertBefore(moreView, nav.nextElementSibling);
    }

    if (!moreView.dataset.ready) {
      moreView.dataset.ready = "true";
      moreView.innerHTML = '<div class="tein-more-header"><span class="tein-eyebrow">TEIN controls</span><h2>More</h2><p>Settings and utilities.</p></div><div class="tein-more-grid"><div class="tein-more-panel"><div><strong>Appearance</strong><span>Switch between Auto, Light and Dark.</span></div><div class="tein-more-control" data-control="theme"></div></div><div class="tein-more-panel"><div><strong>Interface sound</strong><span>Subtle feedback for interactions.</span></div><div class="tein-more-control" data-control="sound"></div></div></div>';
      const theme = document.querySelector(".tein-theme-toggle");
      const sound = document.querySelector(".tein-sound-toggle");
      if (theme) moreView.querySelector('[data-control="theme"]')?.appendChild(theme);
      if (sound) moreView.querySelector('[data-control="sound"]')?.appendChild(sound);
    }

    const buttons = [...nav.querySelectorAll("button[data-view]")];
    const views = [...document.querySelectorAll(".tein-app-view[data-view]")];
    const activate = (name, updateHash = true) => {
      buttons.forEach((button) => {
        const active = button.dataset.view === name;
        button.classList.toggle("is-active", active);
        button.setAttribute("aria-selected", String(active));
      });
      views.forEach((view) => {
        const active = view.dataset.view === name;
        view.classList.toggle("is-active", active);
        view.hidden = !active;
      });
      if (updateHash) history.replaceState?.(null, "", `#${name}`);
      window.TEIN?.tick?.("soft");
    };

    buttons.forEach((button) => button.addEventListener("click", () => activate(button.dataset.view)));
    document.querySelectorAll(".tein-open-plan,.tein-focus-action").forEach((button) => {
      button.addEventListener("click", () => activate("plan"));
    });

    const initial = location.hash.slice(1);
    activate(views.some((view) => view.dataset.view === initial) ? initial : "home", false);
  }

  function showSubjectAttendance(index) {
    const container = document.getElementById("subject-attendance-details");
    if (!container) return;
    const panels = container.querySelectorAll("[data-subject-detail]");
    let selectedPanel = null;

    panels.forEach((panel) => {
      const selected = panel.dataset.subjectDetail === String(index);
      panel.hidden = !selected;
      panel.style.display = selected ? "block" : "none";
      if (selected) selectedPanel = panel;
    });

    document.querySelectorAll(".subject-attendance-row.is-selected").forEach((row) => row.classList.remove("is-selected"));
    document.querySelector(`.subject-attendance-row[data-subject-index="${index}"]`)?.classList.add("is-selected");

    if (!selectedPanel) {
      container.hidden = true;
      container.style.display = "none";
      return;
    }

    container.hidden = false;
    container.style.display = "block";
    selectedPanel.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
      block: "start",
    });
    window.TEIN?.tick?.("soft");
  }

  function setupSubjectRows() {
    document.querySelectorAll(".subject-attendance-row").forEach((row) => {
      if (row.dataset.teinSubjectBound) return;
      row.dataset.teinSubjectBound = "true";
      row.setAttribute("role", "button");
      row.setAttribute("tabindex", "0");
      row.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          row.click();
        }
      });
      row.addEventListener("click", () => {
        const index = row.dataset.subjectIndex;
        if (index !== undefined) showSubjectAttendance(index);
      });
    });
  }

  function formatLeave(totalClasses) {
    totalClasses = Math.max(0, parseInt(totalClasses || "0", 10) || 0);
    const days = Math.floor(totalClasses / 8);
    const classes = totalClasses % 8;
    if (days === 0) return `${classes} class(es)`;
    if (classes === 0) return `${days} day(s)`;
    return `${days} day(s) ${classes} class(es)`;
  }

  function getLeaveValues(form) {
    const daysInput = form.querySelector('input[name$="_days"]');
    const classesInput = form.querySelector('input[name$="_classes"]');
    if (!daysInput || !classesInput) return { daysInput, classesInput, total: 0 };
    const days = Math.max(0, parseInt(daysInput.value || "0", 10) || 0);
    const classes = Math.max(0, parseInt(classesInput.value || "0", 10) || 0);
    return { daysInput, classesInput, total: days * 8 + classes };
  }

  function updateProjection(form) {
    const values = getLeaveValues(form);
    if (!values.daysInput || !values.classesInput) return;
    let leave = values.total;
    const maximum = parseInt(form.dataset.maximumClasses || "0", 10) || 0;
    leave = Math.min(leave, maximum);
    const attended = parseInt(form.dataset.attended || "0", 10) || 0;
    const total = parseInt(form.dataset.total || "0", 10) || 0;
    const future = parseInt(form.dataset.future || "0", 10) || 0;
    const projectedAttended = attended + future - leave;
    const projectedTotal = total + future;
    const percentage = projectedTotal > 0 ? (projectedAttended / projectedTotal) * 100 : 0;
    const preview = form.querySelector(".leave-preview strong");
    if (preview) preview.textContent = formatLeave(leave);
    const projection = form.querySelector('[id^="projection_"]');
    if (projection) projection.textContent = `${projectedAttended} / ${projectedTotal} — ${percentage.toFixed(2)}%`;
  }

  function updateLeavePreview(form) {
    const values = getLeaveValues(form);
    if (!values.daysInput || !values.classesInput) return;
    const maximum = parseInt(form.dataset.maximumClasses || "0", 10) || 0;
    const total = Math.min(values.total, maximum);
    values.daysInput.value = Math.floor(total / 8);
    values.classesInput.value = total % 8;
    updateProjection(form);
  }

  function normalizeLeaveInputs(form) {
    updateLeavePreview(form);
    return true;
  }

  function setupForms() {
    document.querySelectorAll('form[action^="/sessional-"]').forEach((form) => {
      if (form.dataset.teinFormBound) return;
      form.dataset.teinFormBound = "true";
      form.addEventListener("input", () => updateLeavePreview(form));
      updateLeavePreview(form);
    });
  }

  window.showSubjectAttendance = showSubjectAttendance;
  window.formatLeave = formatLeave;
  window.getLeaveValues = getLeaveValues;
  window.updateProjection = updateProjection;
  window.updateLeavePreview = updateLeavePreview;
  window.normalizeLeaveInputs = normalizeLeaveInputs;

  function boot() {
    setupLogin();
    setupLoginScene();
    setupShell();
    setupSubjectRows();
    setupForms();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
