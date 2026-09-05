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
        unlocked: false
    };

    function loadVisualOverhaul() {
        if (document.querySelector('link[data-tein-overhaul]')) return;
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = "/static/tein-overhaul.css";
        link.dataset.teinOverhaul = "true";
        document.head.appendChild(link);
    }

    function loadDynamicLayer() {
        if (document.querySelector('link[data-tein-dynamic]')) return;
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = "/static/tein-dynamic.css";
        link.dataset.teinDynamic = "true";
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
        const ctx = audio.ctx;
        const now = ctx.currentTime + when;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
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
            return;
        }
        if (kind === "error") {
            tone(180, .11, .045, "triangle");
            tone(125, .14, .032, "triangle", .055);
            return;
        }
        if (kind === "hover") {
            tone(900, .035, .012, "sine");
            return;
        }
        tone(330, .055, .022, "triangle");
        tone(495, .045, .012, "sine", .018);
    }

    function setupGlobalAudioUnlock() {
        const unlock = () => unlockAudio();
        window.addEventListener("pointerdown", unlock, { passive: true, once: true });
        window.addEventListener("keydown", unlock, { passive: true, once: true });
    }

    function setupInteractiveSounds() {
        const selector = [
            "button",
            "a",
            "input",
            "select",
            "textarea",
            ".subject-attendance-row",
            ".flow-card"
        ].join(",");

        document.querySelectorAll(selector).forEach((element) => {
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
            button.addEventListener("pointermove", (event) => {
                const r = button.getBoundingClientRect();
                const x = (event.clientX - r.left) / r.width - .5;
                const y = (event.clientY - r.top) / r.height - .5;
                button.style.setProperty("--mx", `${x * 10}px`);
                button.style.setProperty("--my", `${y * 7}px`);
                button.style.transform = `translate3d(var(--mx),var(--my),0) scale(1.018)`;
            });
            button.addEventListener("pointerleave", () => {
                button.style.transform = "";
            });
        });
    }

    function setupCardTilt() {
        if (coarsePointer.matches || reduceMotion.matches) return;
        document.querySelectorAll(".bunk-card, .summary, .stat-card").forEach((card) => {
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
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    row.click();
                }
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
            const duration = 700;
            const frame = (time) => {
                const p = Math.min(1, (time - start) / duration);
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
        style.textContent = `
            .stat-card.overall::after {
                background: conic-gradient(from 215deg, var(--accent-2) 0 var(--tein-attendance-pct), color-mix(in srgb, var(--bg) 16%, transparent) var(--tein-attendance-pct) 100%);
            }
        `;
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
            const nextIndex = (modes.indexOf(mode) + 1) % modes.length;
            mode = modes[nextIndex];
            applyTheme(mode);
            render();
            tick("soft");
        });

        const onSystemChange = () => {
            if (mode === "system") render();
        };
        if (systemTheme.addEventListener) systemTheme.addEventListener("change", onSystemChange);
        else if (systemTheme.addListener) systemTheme.addListener(onSystemChange);

        render();
        document.body.appendChild(toggle);
    }

    function setupSoundToggle() {
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
            if (audio.enabled) {
                unlockAudio();
                tick("success");
            }
            render();
        });
        render();
        document.body.appendChild(toggle);
    }

    function setupForms() {
        document.querySelectorAll('form[action^="/sessional-"]').forEach((form) => {
            form.addEventListener("submit", () => tick("success"));
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        loadVisualOverhaul();
        loadDynamicLayer();
        setupGlobalAudioUnlock();
        setupMagneticButtons();
        setupCardTilt();
        setupSubjectRows();
        animateNumbers();
        setupAttendanceInstrument();
        setupForms();
        setupSoundToggle();
        setupThemeToggle();
        setupInteractiveSounds();
    });

    window.TEIN = { tick };
})();
