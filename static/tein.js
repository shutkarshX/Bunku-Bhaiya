(() => {
    "use strict";

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const coarsePointer = window.matchMedia("(pointer: coarse)");

    const audio = {
        ctx: null,
        enabled: true,
        last: 0
    };

    function initAudio() {
        if (audio.ctx || !audio.enabled) return;
        const Ctx = window.AudioContext || window.webkitAudioContext;
        if (!Ctx) return;
        audio.ctx = new Ctx();
    }

    function tick(kind = "soft") {
        if (!audio.enabled || reduceMotion.matches) return;
        const now = performance.now();
        if (now - audio.last < 90) return;
        audio.last = now;
        initAudio();
        if (!audio.ctx) return;
        const ctx = audio.ctx;
        if (ctx.state === "suspended") ctx.resume();

        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        const base = kind === "success" ? 520 : kind === "error" ? 150 : 300;
        osc.type = kind === "success" ? "sine" : "triangle";
        osc.frequency.setValueAtTime(base, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(base * 1.18, ctx.currentTime + .08);
        gain.gain.setValueAtTime(.0001, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(.035, ctx.currentTime + .008);
        gain.gain.exponentialRampToValueAtTime(.0001, ctx.currentTime + .11);
        osc.connect(gain).connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + .12);
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
            button.addEventListener("pointerdown", () => tick("soft"));
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

    function setupSoundToggle() {
        const toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "tein-sound-toggle";
        toggle.setAttribute("aria-label", "Toggle interface sounds");
        toggle.innerHTML = '<span class="tein-sound-dot"></span><span>Sound</span>';
        toggle.addEventListener("click", () => {
            audio.enabled = !audio.enabled;
            toggle.classList.toggle("is-off", !audio.enabled);
            if (audio.enabled) tick("success");
        });
        document.body.appendChild(toggle);
    }

    function setupThemeToggle() {
        const toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "tein-theme-toggle";
        toggle.setAttribute("aria-label", "Toggle light and dark theme");
        toggle.innerHTML = '<span>Theme</span><span class="tein-theme-indicator"></span>';
        const stored = localStorage.getItem("tein-theme");
        if (stored) document.documentElement.dataset.theme = stored;
        const sync = () => toggle.classList.toggle("is-dark", document.documentElement.dataset.theme === "dark");
        toggle.addEventListener("click", () => {
            const current = document.documentElement.dataset.theme;
            const next = current === "dark" ? "light" : "dark";
            document.documentElement.dataset.theme = next;
            localStorage.setItem("tein-theme", next);
            sync();
            tick("soft");
        });
        sync();
        document.body.appendChild(toggle);
    }

    function setupForms() {
        document.querySelectorAll('form[action^="/sessional-"]').forEach((form) => {
            form.addEventListener("submit", () => tick("success"));
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        setupMagneticButtons();
        setupCardTilt();
        setupSubjectRows();
        animateNumbers();
        setupForms();
        setupSoundToggle();
        setupThemeToggle();
    });

    window.TEIN = { tick };
})();
