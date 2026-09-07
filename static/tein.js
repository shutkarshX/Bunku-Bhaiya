(() => {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const coarsePointer = window.matchMedia("(pointer: coarse)");
  const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");
  const audio = {
    ctx: null,
    master: null,
    enabled: localStorage.getItem("tein-sound") !== "off",
    last: 0,
    unlocked: false,
  };

  function bootstrapTheme() {
    const stored = localStorage.getItem("tein-theme");
    if (stored === "light" || stored === "dark") {
      document.documentElement.dataset.theme = stored;
    } else {
      delete document.documentElement.dataset.theme;
    }
  }

  function initAudio() {
    if (audio.ctx || !audio.enabled) return;
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return;
    audio.ctx = new Ctx();
    audio.master = audio.ctx.createGain();
    audio.master.gain.value = 0.7;
    audio.master.connect(audio.ctx.destination);
  }

  function unlockAudio() {
    if (!audio.enabled) return;
    initAudio();
    if (!audio.ctx) return;
    if (audio.ctx.state === "suspended") {
      const result = audio.ctx.resume();
      if (result && typeof result.catch === "function") result.catch(() => {});
    }
    audio.unlocked = true;
  }

  function tone(frequency, duration, volume, type = "sine", when = 0) {
    if (!audio.enabled || !audio.ctx || !audio.master) return;
    const now = audio.ctx.currentTime + when;
    const osc = audio.ctx.createOscillator();
    const gain = audio.ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(frequency, now);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(volume, now + 0.006);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);
    osc.connect(gain).connect(audio.master);
    osc.start(now);
    osc.stop(now + duration + 0.015);
  }

  function tick(kind = "soft") {
    if (!audio.enabled) return;
    unlockAudio();
    if (!audio.unlocked) return;
    const now = performance.now();
    if (now - audio.last < 55) return;
    audio.last = now;
    if (kind === "success") {
      tone(520, 0.08, 0.045);
      tone(780, 0.12, 0.035, "sine", 0.055);
    } else if (kind === "error") {
      tone(180, 0.11, 0.045, "triangle");
      tone(125, 0.14, 0.032, "triangle", 0.055);
    } else if (kind === "hover") {
      tone(900, 0.035, 0.012);
    } else {
      tone(330, 0.055, 0.022, "triangle");
      tone(495, 0.045, 0.012, "sine", 0.018);
    }
  }

  function setupGlobalAudioUnlock() {
    const unlock = () => unlockAudio();
    window.addEventListener("pointerdown", unlock, { passive: true, once: true });
    window.addEventListener("keydown", unlock, { passive: true, once: true });
  }

  function setupInteractiveSounds() {
    document.querySelectorAll("button,a,input,select,textarea,.subject-attendance-row,.flow-card").forEach((element) => {
      if (element.dataset.teinSoundBound) return;
      element.dataset.teinSoundBound = "true";
      element.addEventListener("pointerenter", () => {
        if (!coarsePointer.matches) tick("hover");
      });
      element.addEventListener("pointerdown", () => tick("soft"));
    });
  }

  function setupMagneticButtons() {
    if (coarsePointer.matches || reduceMotion.matches) return;
    document.querySelectorAll(".attendance-button").forEach((button) => {
      if (button.dataset.teinMagneticBound) return;
      button.dataset.teinMagneticBound = "true";
      button.addEventListener("pointermove", (event) => {
        const rect = button.getBoundingClientRect();
        const x = (event.clientX - rect.left) / rect.width - 0.5;
        const y = (event.clientY - rect.top) / rect.height - 0.5;
        button.style.transform = `translate3d(${x * 10}px,${y * 7}px,0) scale(1.018)`;
      });
      button.addEventListener("pointerleave", () => {
        button.style.transform = "";
      });
    });
  }

  function setupCardTilt() {
    if (coarsePointer.matches || reduceMotion.matches) return;
    document.querySelectorAll(".bunk-card,.summary,.stat-card").forEach((card) => {
      if (card.dataset.teinTiltBound) return;
      card.dataset.teinTiltBound = "true";
      card.addEventListener("pointermove", (event) => {
        const rect = card.getBoundingClientRect();
        const x = (event.clientX - rect.left) / rect.width - 0.5;
        const y = (event.clientY - rect.top) / rect.height - 0.5;
        card.style.setProperty("--tilt-x", `${y * -1.8}deg`);
        card.style.setProperty("--tilt-y", `${x * 2.2}deg`);
        card.classList.add("tein-tilting");
      });
      card.addEventListener("pointerleave", () => card.classList.remove("tein-tilting"));
    });
  }

  function animateNumbers() {
    if (reduceMotion.matches) return;
    document.querySelectorAll(".stat-card strong").forEach((node) => {
      const raw = node.textContent.trim();
      const match = raw.match(/(-?\d+(?:\.\d+)?)(.*)/);
      if (!match) return;
      const target = Number(match[1]);
      if (!Number.isFinite(target)) return;
      const suffix = match[2];
      const decimals = (match[1].split(".")[1] || "").length;
      const start = performance.now();
      const frame = (time) => {
        const progress = Math.min(1, (time - start) / 700);
        const eased = 1 - Math.pow(1 - progress, 3);
        node.textContent = (target * eased).toFixed(decimals) + suffix;
        if (progress < 1) requestAnimationFrame(frame);
      };
      node.textContent = (0).toFixed(decimals) + suffix;
      requestAnimationFrame(frame);
    });
  }

  function setupAttendanceInstrument() {
    const overall = document.querySelector(".tein-home-hero .stat-card.overall strong");
    if (!overall) return;
    const match = overall.textContent.match(/(\d+(?:\.\d+)?)/);
    const percentage = match ? Math.max(0, Math.min(100, Number(match[1]))) : 0;
    document.documentElement.style.setProperty("--tein-attendance-pct", `${percentage}%`);
    if (document.querySelector("style[data-tein-instrument]")) return;
    const style = document.createElement("style");
    style.dataset.teinInstrument = "true";
    style.textContent = `.tein-home-hero .stat-card.overall::before{content:"";position:absolute;inset:12px;border:1px solid color-mix(in srgb,var(--bg) 12%,transparent);border-radius:18px;pointer-events:none}.tein-home-hero .stat-card.overall::after{content:"";position:absolute;right:-42px;top:50%;width:205px;height:205px;border-radius:50%;transform:translateY(-50%) rotate(-12deg);background:conic-gradient(from 215deg,var(--accent-2) 0 var(--tein-attendance-pct),color-mix(in srgb,var(--bg) 16%,transparent) var(--tein-attendance-pct) 100%);-webkit-mask:radial-gradient(farthest-side,transparent calc(100% - 12px),#000 calc(100% - 11px));mask:radial-gradient(farthest-side,transparent calc(100% - 12px),#000 calc(100% - 11px));opacity:.9;pointer-events:none}`;
    document.head.appendChild(style);
  }

  function applyTheme(mode) {
    document.documentElement.classList.add("tein-theme-transition");
    window.setTimeout(() => document.documentElement.classList.remove("tein-theme-transition"), 420);
    if (mode === "system") delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = mode;
    localStorage.setItem("tein-theme", mode);
  }

  function setupThemeToggle() {
    if (document.querySelector(".tein-theme-toggle")) return;
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "tein-theme-toggle";
    toggle.setAttribute("aria-label", "Cycle TEIN theme: system, light, dark");
    const modes = ["system", "light", "dark"];
    let mode = localStorage.getItem("tein-theme") || "system";
    if (!modes.includes(mode)) mode = "system";
    applyTheme(mode);
    const render = () => {
      const isDark = mode === "dark" || (mode === "system" && systemTheme.matches);
      toggle.dataset.mode = mode;
      toggle.innerHTML = `<span class="tein-theme-glyph" aria-hidden="true"></span><span>${mode === "system" ? "Auto" : isDark ? "Dark" : "Light"}</span>`;
    };
    toggle.addEventListener("click", () => {
      mode = modes[(modes.indexOf(mode) + 1) % modes.length];
      applyTheme(mode);
      render();
      tick("soft");
    });
    const onSystemChange = () => { if (mode === "system") render(); };
    if (systemTheme.addEventListener) systemTheme.addEventListener("change", onSystemChange);
    else if (systemTheme.addListener) systemTheme.addListener(onSystemChange);
    render();
    document.body.appendChild(toggle);
  }

  function setupSoundToggle() {
    if (document.querySelector(".tein-sound-toggle")) return;
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "tein-sound-toggle";
    toggle.setAttribute("aria-label", "Toggle interface sounds");
    const render = () => {
      toggle.classList.toggle("is-off", !audio.enabled);
      toggle.innerHTML = `<span class="tein-sound-glyph" aria-hidden="true"></span><span>${audio.enabled ? "Sound" : "Muted"}</span>`;
    };
    toggle.addEventListener("click", () => {
      audio.enabled = !audio.enabled;
      localStorage.setItem("tein-sound", audio.enabled ? "on" : "off");
      if (audio.enabled) { unlockAudio(); tick("success"); }
      render();
    });
    render();
    document.body.appendChild(toggle);
  }

  function loadLoginNativeBridge() {
    if (!document.getElementById("login-section") || document.querySelector('script[data-tein-login-native]')) return;
    const script = document.createElement("script");
    script.src = "/static/tein-login-native.js";
    script.defer = true;
    script.dataset.teinLoginNative = "true";
    document.head.appendChild(script);
  }

  function boot() {
    bootstrapTheme();
    setupGlobalAudioUnlock();
    setupThemeToggle();
    setupSoundToggle();
    setupInteractiveSounds();
    setupMagneticButtons();
    setupCardTilt();
    animateNumbers();
    setupAttendanceInstrument();
    loadLoginNativeBridge();
  }

  window.TEIN = window.TEIN || {};
  window.TEIN.tick = tick;

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
