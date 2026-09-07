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
            if (button.dataset.teinMagneticBound) return;
            button.dataset.teinMagneticBound = "true";
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
            if (card.dataset.teinTiltBound) return;
            card.dataset.teinTiltBound = "true";
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

    // Restored from the original dashboard behavior. The TEIN redesign kept
    // the subject rows and detail panels but had lost the bridge between them.
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

        document.querySelectorAll(".subject-attendance-row.is-selected").forEach((row) => {
            row.classList.remove("is-selected");
        });
        const selectedRow = document.querySelector(`.subject-attendance-row[data-subject-index="${index}"]`);
        selectedRow?.classList.add("is-selected");

        if (!selectedPanel) {
            container.hidden = true;
            container.style.display = "none";
            return;
        }

        container.hidden = false;
        container.style.display = "block";
        selectedPanel.scrollIntoView({
            behavior: reduceMotion.matches ? "auto" : "smooth",
            block: "start"
        });
        tick("soft");
    }

    window.showSubjectAttendance = showSubjectAttendance;

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
        if (document.querySelector("style[data-tein-instrument]")) return;
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
        if (document.querySelector(".tein-sound-toggle")) return;
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
        document.querySelectorAll('form[action^="/sessional-"]').forEach((form) => {
            if (form.dataset.teinFormBound) return;
            form.dataset.teinFormBound = "true";
            form.addEventListener("submit", () => tick("success"));
        });
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
            Object.entries(views).forEach(([key, view]) => {
                const active = key === name;
                view.classList.toggle("is-active", active);
                view.hidden = !active;
            });
            [home, plan, subjects].forEach((button, index) => {
                const active = ["home", "plan", "subjects"][index] === name;
                button.classList.toggle("is-active", active);
                button.setAttribute("aria-selected", String(active));
            });
            if (updateHash) history.replaceState(null, "", `#${name}`);
            tick("soft");
            window.setTimeout(() => { setupInteractiveSounds(); setupMagneticButtons(); setupCardTilt(); setupSubjectRows(); setupForms(); }, 0);
        };

        home.addEventListener("click", () => activate("home"));
        plan.addEventListener("click", () => activate("plan"));
        subjects.addEventListener("click", () => activate("subjects"));
        views.home.querySelectorAll(".tein-focus-action").forEach((button) => button.addEventListener("click", () => activate("plan")));

        const initial = location.hash.replace("#", "");
        activate(views[initial] ? initial : "home", false);
    }

    function updateGeneratedUsername() {
        const year = document.getElementById("admission-year")?.value;
        const branchInput = document.getElementById("branch");
        const studentInput = document.getElementById("student-number");
        const output = document.getElementById("generated-username");
        const hidden = document.getElementById("generated-username-input");
        if (!year || !branchInput || !studentInput || !output || !hidden) return;

        const branch = branchInput.value.trim().toUpperCase();
        const studentNumber = studentInput.value.trim();
        const yearCode = `0${String(year).slice(-2)}1`;
        const username = `${yearCode}${branch}${studentNumber}@niet.co.in`;
        const complete = /^0\d{3}[A-Z0-9]+\d{3}@niet\.co\.in$/.test(username);
        output.textContent = branch && studentNumber.length === 3 ? username : "—";
        hidden.value = username;
        hidden.disabled = !complete;
    }

    function updateManualUsername() {
        const source = document.getElementById("manual-username");
        const hidden = document.getElementById("manual-username-input");
        if (!source || !hidden) return;
        let value = source.value.trim();
        if (value && !/@niet\.co\.in$/i.test(value)) value += "@niet.co.in";
        hidden.value = value;
        hidden.disabled = !value;
    }

    function setLoginMethod(method) {
        const manual = document.getElementById("manual-login-fields");
        const generated = document.getElementById("generate-login-fields");
        const manualButton = document.getElementById("manual-login-button");
        const generateButton = document.getElementById("generate-login-button");
        const manualInput = document.getElementById("manual-username");
        const year = document.getElementById("admission-year");
        const branch = document.getElementById("branch");
        const student = document.getElementById("student-number");
        const generatedHidden = document.getElementById("generated-username-input");
        const manualHidden = document.getElementById("manual-username-input");
        if (!manual || !generated) return;

        const isManual = method === "manual";
        manual.style.setProperty("display", isManual ? "block" : "none", "important");
        generated.style.setProperty("display", isManual ? "none" : "block", "important");
        manualButton?.classList.toggle("is-selected", isManual);
        generateButton?.classList.toggle("is-selected", !isManual);
        if (manualInput) manualInput.required = isManual;
        if (year) year.required = !isManual;
        if (branch) branch.required = !isManual;
        if (student) student.required = !isManual;
        if (generatedHidden) generatedHidden.disabled = isManual;
        if (manualHidden) manualHidden.disabled = !isManual;
        if (!isManual) updateGeneratedUsername();
    }

    function showLoading() {
        const login = document.getElementById("login-section");
        const loading = document.getElementById("loading-screen");
        const video = document.getElementById("loading-video");
        if (login) login.style.display = "none";
        if (loading) loading.style.display = "flex";
        if (video) {
            try { video.currentTime = 0; video.play().catch(() => {}); } catch (_) {}
        }
        tick("success");
    }

    function normalizeLeaveInputs(form) {
        if (!form) return true;
        const days = form.querySelector('input[name^="leave_"][name$="_days"]');
        const classes = form.querySelector('input[name^="leave_"][name$="_classes"]');
        const maximum = Number(form.dataset.maximumClasses || 0);
        const d = Math.max(0, Number(days?.value || 0));
        const c = Math.max(0, Number(classes?.value || 0));
        const total = Math.min(maximum, d * 8 + c);
        if (days) days.value = Math.floor(total / 8);
        if (classes) classes.value = total % 8;
        return true;
    }

    window.setLoginMethod = setLoginMethod;
    window.updateManualUsername = updateManualUsername;
    window.updateGeneratedUsername = updateGeneratedUsername;
    window.showLoading = showLoading;
    window.normalizeLeaveInputs = normalizeLeaveInputs;
    window.TEIN = window.TEIN || {};
    window.TEIN.tick = tick;

    function boot() {
        bootstrapTheme();
        loadStylesheet("/static/tein-dynamic.css", "teinDynamic");
        loadStylesheet("/static/tein-overhaul.css", "teinOverhaul");
        loadStylesheet("/static/tein-shell.css", "teinShell");
        setupGlobalAudioUnlock();
        setupThemeToggle();
        setupSoundToggle();
        setupAppShell();
        setupInteractiveSounds();
        setupMagneticButtons();
        setupCardTilt();
        setupSubjectRows();
        setupForms();
        animateNumbers();
        setupAttendanceInstrument();
        updateGeneratedUsername();
    }

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
    else boot();
})();
