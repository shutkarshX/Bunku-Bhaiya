(() => {
    "use strict";

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const coarsePointer = window.matchMedia("(pointer: coarse)");

    const audio = {
        ctx: null,
        enabled: localStorage.getItem("tein-sound") !== "off",
        last: 0
    };

    function injectInteractionStyles() {
        if (document.getElementById("tein-interaction-styles")) return;
        const style = document.createElement("style");
        style.id = "tein-interaction-styles";
        style.textContent = `
            html[data-theme="light"] { color-scheme: light; --bg:#f3f4f6; --surface:rgba(255,255,255,.82); --surface-solid:#fff; --surface-2:#f8fafc; --text:#111318; --muted:#68707d; --line:rgba(17,19,24,.09); --line-strong:rgba(17,19,24,.15); --accent:#111318; --accent-2:#6d5dfc; --accent-soft:rgba(109,93,252,.10); --success:#177245; --warning:#9a6500; --danger:#b42318; }
            html[data-theme="dark"] { color-scheme: dark; --bg:#08090c; --surface:rgba(20,22,27,.78); --surface-solid:#14161b; --surface-2:#101217; --text:#f4f5f7; --muted:#9aa1ad; --line:rgba(255,255,255,.09); --line-strong:rgba(255,255,255,.16); --accent:#f4f5f7; --accent-2:#8b7dff; --accent-soft:rgba(139,125,255,.13); --success:#4fd18a; --warning:#e6b85c; --danger:#ff746c; }
            html[data-theme] body { background:radial-gradient(circle at 8% 0%, color-mix(in srgb,var(--accent-2) 10%,transparent), transparent 28rem), radial-gradient(circle at 92% 14%, color-mix(in srgb,var(--text) 5%,transparent), transparent 24rem), var(--bg); }
            .tein-sound-toggle,.tein-theme-toggle { position:fixed; z-index:110; bottom:18px; display:inline-flex; align-items:center; gap:8px; min-height:40px; padding:9px 12px; border:1px solid var(--line-strong); border-radius:999px; background:var(--surface); color:var(--text); box-shadow:var(--shadow-sm); backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px); font:600 12px/1 inherit; letter-spacing:.04em; cursor:pointer; transition:transform .35s var(--spring), background .35s var(--ease), border-color .35s var(--ease); }
            .tein-sound-toggle { right:18px; } .tein-theme-toggle { right:92px; }
            .tein-sound-toggle:hover,.tein-theme-toggle:hover { transform:translateY(-3px); border-color:var(--accent-2); }
            .tein-sound-dot { width:7px; height:7px; border-radius:50%; background:var(--accent-2); box-shadow:0 0 0 4px var(--accent-soft); }
            .tein-sound-toggle.is-off .tein-sound-dot { background:var(--muted); box-shadow:none; }
            .tein-theme-indicator { width:24px; height:14px; border:1px solid var(--line-strong); border-radius:999px; position:relative; background:var(--surface-2); }
            .tein-theme-indicator::after { content:""; position:absolute; top:2px; left:2px; width:8px; height:8px; border-radius:50%; background:var(--accent-2); transition:transform .35s var(--spring); }
            .tein-theme-toggle.is-dark .tein-theme-indicator::after { transform:translateX(10px); }
            .subject-attendance-row { position:relative; }
            .subject-attendance-row.is-selected { background:var(--accent-soft); }
            .subject-attendance-row:focus-visible { outline:2px solid var(--accent-2); outline-offset:-2px; }
            .tein-tilting { transform:perspective(900px) rotateX(var(--tilt-x,0deg)) rotateY(var(--tilt-y,0deg)) translateY(-3px); }
            @media (max-width:650px) { .tein-sound-toggle,.tein-theme-toggle { bottom:12px; } .tein-sound-toggle { right:12px; } .tein-theme-toggle { right:86px; } }
            @media (prefers-reduced-motion: reduce) { .tein-sound-toggle,.tein-theme-toggle { transition:none; } }
        `;
        document.head.appendChild(style);
    }

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
            button.addEventListener("pointerleave", () => { button.style.transform = ""; });
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
            row.setAttribute("aria-label", "Show subject attendance details");
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
        toggle.classList.toggle("is-off", !audio.enabled);
        toggle.addEventListener("click", () => {
            audio.enabled = !audio.enabled;
            localStorage.setItem("tein-sound", audio.enabled ? "on" : "off");
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
        if (stored === "light" || stored === "dark") document.documentElement.dataset.theme = stored;
        const sync = () => toggle.classList.toggle("is-dark", document.documentElement.dataset.theme === "dark");
        toggle.addEventListener("click", () => {
            const current = document.documentElement.dataset.theme || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
            const next = current === "dark" ? "light" : "dark";
            document.documentElement.dataset.theme = next;
            localStorage.setItem("tein-theme", next);
            sync();
            tick("soft");
        });
        sync();
        document.body.appendChild(toggle);
    }

    function removeLegacyEmoji() {
        const replacements = [
            ["🟢 Attendance is Safe", "Attendance is Safe"],
            ["🟡 Attendance Recovery Needed", "Attendance Recovery Needed"],
            ["🔴 75% Not Reachable", "75% Not Reachable"],
            ["⚠️ College Portal Unavailable", "College Portal Unavailable"],
            ["❌ Login Failed", "Login Failed"],
            ["✍️ Enter Email Manually", "Enter Email Manually"],
            ["⚡ Generate NIET Email", "Generate NIET Email"],
            ["✅ Completed", "Completed"]
        ];
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        const nodes = [];
        while (walker.nextNode()) nodes.push(walker.currentNode);
        nodes.forEach((node) => {
            replacements.forEach(([from, to]) => {
                if (node.nodeValue.includes(from)) node.nodeValue = node.nodeValue.replaceAll(from, to);
            });
        });
    }

    function setupForms() {
        document.querySelectorAll('form[action^="/sessional-"]').forEach((form) => {
            form.addEventListener("submit", () => tick("success"));
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        injectInteractionStyles();
        removeLegacyEmoji();
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
