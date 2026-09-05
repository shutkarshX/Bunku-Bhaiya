(() => {
    "use strict";

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const coarsePointer = window.matchMedia("(pointer: coarse)");
    const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");
    const audio = { ctx: null, master: null, enabled: localStorage.getItem("tein-sound") !== "off", last: 0, unlocked: false };

    function bootstrapTheme() {
        const stored = localStorage.getItem("tein-theme");
        if (stored === "light" || stored === "dark") document.documentElement.dataset.theme = stored;
        else delete document.documentElement.dataset.theme;
    }

    function loadStylesheet(href, key) {
        if (document.querySelector(`link[data-${key}]`)) return;
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = href;
        link.dataset[key] = "true";
        document.head.appendChild(link);
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
            tone(520, .08, .045, "sine");
            tone(780, .12, .035, "sine", .055);
        } else if (kind === "error") {
            tone(180, .11, .045, "triangle");
            tone(125, .14, .032, "triangle", .055);
        } else if (kind === "hover") {
            tone(900, .035, .012, "sine");
        } else {
            tone(330, .055, .022, "triangle");
            tone(495, .045, .012, "sine", .018);
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
            element.addEventListener("pointerenter", () => { if (!coarsePointer.matches) tick("hover"); });
            element.addEventListener("pointerdown", () => tick("soft"));
        });
    }

    function setupMagneticButtons() {
        if (coarsePointer.matches || reduceMotion.matches) return;
        document.querySelectorAll(".attendance-button").forEach((button) => {
            button.addEventListener("pointermove", (event) => {
                const r = button.getBoundingClientRect();
                const x = (event.clientX - r.left) / r.width - .5;
                const y = (event.clientY - r.top) / r.height - .5;
                button.style.setProperty("--mx", `${x * 10}px`);
                button.style.setProperty("--my", `${y * 7}px`);
                button.style.transform = `translate3d(var(--mx),var(--my),0) scale(1.018)`;
            });
            button.addEventListener("pointerleave", () => { button.style.transform = ""; });
        });
    }

    function setupCardTilt() {
        if (coarsePointer.matches || reduceMotion.matches) return;
        document.querySelectorAll(".bunk-card,.summary,.stat-card").forEach((card) => {
            card.addEventListener("pointermove", (event) => {
                const r = card.getBoundingClientRect();
                const x = (event.clientX - r.left) / r.width - .5;
                const y = (event.clientY - r.top) / r.height - .5;
                card.style.setProperty("--tilt-x", `${y * -1.8}deg`);
                card.style.setProperty("--tilt-y", `${x * 2.2}deg`);
                card.classList.add("tein-tilting");
            });
            card.addEventListener("pointerleave", () => card.classList.remove("tein-tilting"));
        });
    }

    function setupSubjectRows() {
        document.querySelectorAll(".subject-attendance-row").forEach((row) => {
            row.setAttribute("role", "button");
            row.setAttribute("tabindex", "0");
            row.addEventListener("keydown", (event) => {
                if (event.key === "Enter" || event.key === " ") { event.preventDefault(); row.click(); }
            });
            row.addEventListener("click", () => {
                document.querySelectorAll(".subject-attendance-row.is-selected").forEach((r) => r.classList.remove("is-selected"));
                row.classList.add("is-selected");
                tick("soft");
            });
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
                const p = Math.min(1, (time - start) / 700);
                const eased = 1 - Math.pow(1 - p, 3);
                node.textContent = (target * eased).toFixed(decimals) + suffix;
                if (p < 1) requestAnimationFrame(frame);
            };
            node.textContent = (0).toFixed(decimals) + suffix;
            requestAnimationFrame(frame);
        });
    }

    function setupAttendanceInstrument() {
        const overall = document.querySelector(".stat-card.overall strong");
        if (!overall) return;
        const match = overall.textContent.match(/(\d+(?:\.\d+)?)/);
        const percentage = match ? Math.max(0, Math.min(100, Number(match[1]))) : 0;
        document.documentElement.style.setProperty("--tein-attendance-pct", `${percentage}%`);
        const style = document.createElement("style");
        style.dataset.teinInstrument = "true";
        style.textContent = ".stat-card.overall::after{background:conic-gradient(from 215deg,var(--accent-2) 0 var(--tein-attendance-pct),color-mix(in srgb,var(--bg) 16%,transparent) var(--tein-attendance-pct) 100%)}";
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
            toggle.innerHTML = `<span class="tein-theme-glyph" aria-hidden="true"></span><span class="tein-theme-label">${mode === "system" ? "Auto" : isDark ? "Dark" : "Light"}</span>`;
        };
        toggle.addEventListener("click", () => {
            mode = modes[(modes.indexOf(mode) + 1) % modes.length];
            applyTheme(mode); render(); tick("soft");
        });
        const onSystemChange = () => { if (mode === "system") render(); };
        if (systemTheme.addEventListener) systemTheme.addEventListener("change", onSystemChange);
        else if (systemTheme.addListener) systemTheme.addListener(onSystemChange);
        render(); document.body.appendChild(toggle);
    }

    function setupSoundToggle() {
        const toggle = document.createElement("button");
        toggle.type = "button"; toggle.className = "tein-sound-toggle";
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
        render(); document.body.appendChild(toggle);
    }

    function setupForms() {
        document.querySelectorAll('form[action^="/sessional-"]').forEach((form) => form.addEventListener("submit", () => tick("success")));
    }

    function topLevelChildren(container) {
        return Array.from(container.children).filter((el) => el.tagName !== "SCRIPT" && el.tagName !== "STYLE");
    }

    function setupAppShell() {
        const container = document.querySelector(".container");
        if (!container || !document.querySelector(".stats")) return;
        if (document.querySelector(".tein-app-nav")) return;

        const header = container.querySelector("header");
        if (!header) return;

        const children = topLevelChildren(container);
        const attendance = children.find((el) => el.matches(".summary") && /Attendance Summary/i.test(el.textContent));
        const planSummary = children.find((el) => el.matches(".summary") && (/Bunk Calculator/i.test(el.textContent) || /Step [123] of 3/i.test(el.textContent)));
        const planResults = children.find((el) => el.matches(".bunk-results"));
        const subjectDetails = container.querySelector("#subject-attendance-details");
        const subjectTable = children.find((el) => el.matches(".table-container"));
        const subjectSummary = children.find((el) => el.matches(".summary") && /subject/i.test(el.textContent) && el !== attendance && el !== planSummary);
        const planText = `${planSummary ? planSummary.textContent : ""} ${planResults ? planResults.textContent : ""}`;
        const stepMatch = planText.match(/Step\s+(\d)\s+of\s+3/i);
        const activeStep = stepMatch ? Number(stepMatch[1]) : 1;

        const nav = document.createElement("nav");
        nav.className = "tein-app-nav";
        nav.setAttribute("aria-label", "TEIN sections");
        const home = document.createElement("button");
        const plan = document.createElement("button");
        const subjects = document.createElement("button");
        home.innerHTML = "Overview";
        plan.innerHTML = `Plan <span class="tein-nav-count">${activeStep}/3</span>`;
        subjects.innerHTML = "Subjects";
        nav.append(home, plan, subjects);
        header.after(nav);

        const views = {};
        ["home", "plan", "subjects"].forEach((name) => {
            const view = document.createElement("section");
            view.className = `tein-app-view tein-${name}-view`;
            view.dataset.view = name;
            views[name] = view;
            nav.after(view);
        });

        const focus = document.createElement("div");
        focus.className = "tein-focus";
        const checkpointNames = ["First Sessional", "Second Sessional", "Third Sessional"];
        const activeName = checkpointNames[Math.max(0, Math.min(2, activeStep - 1))];
        focus.innerHTML = `<div><span class="tein-focus-kicker">Next focus</span><h2>${activeName}</h2><p>${activeStep > 1 ? "Previous checkpoint(s) are completed. Continue from the current real attendance." : "Your first checkpoint is ready for planning."}</p></div><button type="button" class="attendance-button tein-focus-action">Open plan</button>`;
        views.home.appendChild(focus);

        const rail = document.createElement("div");
        rail.className = "tein-checkpoints";
        checkpointNames.forEach((name, index) => {
            const item = document.createElement("div");
            const state = index < activeStep - 1 ? "complete" : index === activeStep - 1 ? "active" : "upcoming";
            item.className = `tein-checkpoint is-${state}`;
            item.innerHTML = `<span class="tein-checkpoint-mark">${state === "complete" ? "✓" : index + 1}</span><span class="tein-checkpoint-copy"><strong>${name}</strong><small>${state === "complete" ? "Completed" : state === "active" ? "Active" : "Upcoming"}</small></span>`;
            rail.appendChild(item);
        });
        views.home.appendChild(rail);

        const homeTitle = document.createElement("div");
        homeTitle.className = "tein-view-title";
        homeTitle.innerHTML = `<div><h2>Overview</h2></div><p>Live attendance from the college portal</p>`;
        views.home.appendChild(homeTitle);
        if (attendance) views.home.appendChild(attendance);

        const planTitle = document.createElement("div");
        planTitle.className = "tein-view-title";
        planTitle.innerHTML = `<div><h2>Plan</h2></div><p>Checkpoint by checkpoint</p>`;
        views.plan.appendChild(planTitle);
        if (planSummary) views.plan.appendChild(planSummary);
        if (planResults) views.plan.appendChild(planResults);

        const subjectTitle = document.createElement("div");
        subjectTitle.className = "tein-view-title";
        subjectTitle.innerHTML = `<div><h2>Subjects</h2></div><p>Tap a subject to inspect its real attendance history</p>`;
        views.subjects.appendChild(subjectTitle);
        if (subjectSummary) { subjectSummary.classList.add("tein-subject-heading"); views.subjects.appendChild(subjectSummary); }
        if (subjectTable) views.subjects.appendChild(subjectTable);
        if (subjectDetails) views.subjects.appendChild(subjectDetails);

        const used = new Set([header, nav, ...Object.values(views), attendance, planSummary, planResults, subjectSummary, subjectTable, subjectDetails]);
        children.forEach((el) => { if (!used.has(el) && el.parentElement === container) views.home.appendChild(el); });

        const activate = (name, updateHash = true) => {
            Object.entries(views).forEach(([key, view]) => view.classList.toggle("is-active", key === name));
            [home, plan, subjects].forEach((button) => button.classList.remove("is-active"));
            ({home, plan, subjects}[name]).classList.add("is-active");
            if (updateHash) history.replaceState(null, "", `#${name}`);
            tick("soft");
            window.scrollTo({ top: 0, behavior: reduceMotion.matches ? "auto" : "smooth" });
        };
        home.addEventListener("click", () => activate("home"));
        plan.addEventListener("click", () => activate("plan"));
        subjects.addEventListener("click", () => activate("subjects"));
        focus.querySelector("button").addEventListener("click", () => activate("plan"));
        window.addEventListener("hashchange", () => activate(location.hash.slice(1) || "home", false));
        activate(["home", "plan", "subjects"].includes(location.hash.slice(1)) ? location.hash.slice(1) : "home", false);
        setupInteractiveSounds();
    }

    bootstrapTheme();
    loadStylesheet("/static/tein-overhaul.css", "teinOverhaul");
    loadStylesheet("/static/tein-dynamic.css", "teinDynamic");
    loadStylesheet("/static/tein-app.css", "teinApp");

    document.addEventListener("DOMContentLoaded", () => {
        setupGlobalAudioUnlock();
        setupMagneticButtons();
        setupCardTilt();
        setupSubjectRows();
        animateNumbers();
        setupAttendanceInstrument();
        setupForms();
        setupSoundToggle();
        setupThemeToggle();
        setupAppShell();
        setupInteractiveSounds();
    });

    window.TEIN = { tick };
})();

/* Legacy dashboard handlers kept global because dashboard.html uses inline events. */
window.setLoginMethod = function (method) {
    const manualFields = document.getElementById("manual-login-fields");
    const generateFields = document.getElementById("generate-login-fields");
    const manualButton = document.getElementById("manual-login-button");
    const generateButton = document.getElementById("generate-login-button");
    const manualInput = document.getElementById("manual-username");
    const generatedInput = document.getElementById("generated-username-input");
    const manualHidden = document.getElementById("manual-username-input");
    if (!manualFields || !generateFields) return;
    const manual = method === "manual";
    manualFields.style.display = manual ? "block" : "none";
    generateFields.style.display = manual ? "none" : "block";
    if (manualButton) manualButton.classList.toggle("is-selected", manual);
    if (generateButton) generateButton.classList.toggle("is-selected", !manual);
    if (manualInput) manualInput.required = manual;
    if (manualHidden) manualHidden.disabled = !manual;
    if (generatedInput) generatedInput.disabled = manual;
    if (!manual) window.updateGeneratedUsername();
};

window.updateManualUsername = function () {
    const input = document.getElementById("manual-username");
    const hidden = document.getElementById("manual-username-input");
    if (!input || !hidden) return;
    let value = input.value.trim();
    if (!value) {
        hidden.value = "";
        return;
    }
    if (!value.includes("@")) value += "@niet.co.in";
    hidden.value = value;
};

window.updateGeneratedUsername = function () {
    const yearEl = document.getElementById("admission-year");
    const branchEl = document.getElementById("branch");
    const numberEl = document.getElementById("student-number");
    const display = document.getElementById("generated-username");
    const hidden = document.getElementById("generated-username-input");
    if (!yearEl || !branchEl || !numberEl || !display || !hidden) return;
    const year = yearEl.value;
    const branch = branchEl.value.trim().toLowerCase();
    const number = numberEl.value.trim();
    const valid = year && branch && /^\d{3}$/.test(number);
    const username = valid ? `${year}${branch}${number}@niet.co.in` : "—";
    display.textContent = username;
    hidden.value = valid ? username : "";
};

window.showLoading = function () {
    const loginSection = document.getElementById("login-section");
    const loadingScreen = document.getElementById("loading-screen");
    const video = document.getElementById("loading-video");
    if (loginSection) loginSection.style.display = "none";
    if (loadingScreen) {
        loadingScreen.style.display = "flex";
        if (video) {
            const play = video.play();
            if (play && typeof play.catch === "function") play.catch(() => {});
        }
    }
};
