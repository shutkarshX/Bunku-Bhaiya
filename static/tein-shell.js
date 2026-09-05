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

        // Generated NIET email is the default login method.
        setMethod("generate");
    }

    function setupCalculatorInteractions() {
        const update = (form) => {
            if (!form) return;
            const days = Math.max(0, parseInt(form.querySelector('input[name^="leave_"][name$="_days"]')?.value || "0", 10) || 0);
            const classes = Math.max(0, parseInt(form.querySelector('input[name^="leave_"][name$="_classes"]')?.value || "0", 10) || 0);
            const teaching = Math.max(1, parseInt(form.dataset.teachingDays || "0", 10) || 0);
            const maximum = Math.max(0, parseInt(form.dataset.maximumClasses || "0", 10) || 0);
            const totalLeave = classes + (teaching ? days * Math.ceil(maximum / teaching) : 0);
            const preview = form.querySelector(".leave-preview strong");
            if (preview) preview.textContent = `${Math.max(0, totalLeave)} class(es)`;
        };
        document.querySelectorAll('form[action^="/sessional-"]').forEach((form) => {
            if (form.dataset.teinCalcBound) return;
            form.dataset.teinCalcBound = "true";
            form.querySelectorAll("input").forEach((input) => input.addEventListener("input", () => update(form)));
            update(form);
        });
    }

    function setupSubjectRows() {
        document.querySelectorAll(".subject-attendance-row").forEach((row) => {
            if (row.dataset.teinSubjectBound) return;
            row.dataset.teinSubjectBound = "true";
            row.setAttribute("role", "button");
            row.setAttribute("tabindex", "0");
            const activate = () => {
                document.querySelectorAll(".subject-attendance-row.is-selected").forEach((other) => {
                    if (other !== row) other.classList.remove("is-selected");
                });
                row.classList.toggle("is-selected");
                const targetId = row.dataset.target || row.getAttribute("aria-controls");
                if (targetId) {
                    const target = document.getElementById(targetId);
                    if (target) target.hidden = !row.classList.contains("is-selected");
                }
            };
            row.addEventListener("click", activate);
            row.addEventListener("keydown", (event) => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    activate();
                }
            });
        });
    }

    function setupShell() {
        const nav = document.querySelector(".tein-app-nav");
        if (!nav) return;

        const buttons = [...nav.querySelectorAll("button[data-view]")];
        const views = [...document.querySelectorAll(".tein-app-view[data-view]")];
        if (!buttons.length || !views.length) return;

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
            moreView.setAttribute("aria-label", "More");
            moreView.hidden = true;
            nav.parentNode.insertBefore(moreView, nav.nextElementSibling);
        }

        const allButtons = [...nav.querySelectorAll("button[data-view]")];
        const allViews = [...document.querySelectorAll(".tein-app-view[data-view]")];

        if (!moreView.dataset.ready) {
            moreView.dataset.ready = "true";
            moreView.innerHTML = `
                <div class="tein-more-header">
                    <span class="tein-eyebrow">TEIN controls</span>
                    <h2>More</h2>
                    <p>Keep secondary controls here so Home stays focused on attendance.</p>
                </div>
                <div class="tein-more-grid">
                    <div class="tein-more-panel">
                        <div><strong>Appearance</strong><span>Auto follows your device. You can also force Light or Dark.</span></div>
                        <div class="tein-more-control" data-control="theme"></div>
                    </div>
                    <div class="tein-more-panel">
                        <div><strong>Interface sound</strong><span>Tactile feedback for important interactions.</span></div>
                        <div class="tein-more-control" data-control="sound"></div>
                    </div>
                </div>
                <div class="tein-more-note"><strong>Portal data</strong><span>Attendance and subject history shown in TEIN come from the existing NIET portal data.</span></div>`;

            const theme = document.querySelector(".tein-theme-toggle");
            const sound = document.querySelector(".tein-sound-toggle");
            const themeSlot = moreView.querySelector('[data-control="theme"]');
            const soundSlot = moreView.querySelector('[data-control="sound"]');
            if (theme && themeSlot) themeSlot.appendChild(theme);
            if (sound && soundSlot) soundSlot.appendChild(sound);
        }

        const activate = (viewName, updateHash = true) => {
            allButtons.forEach((button) => {
                const active = button.dataset.view === viewName;
                button.classList.toggle("is-active", active);
                button.setAttribute("aria-selected", String(active));
            });
            allViews.forEach((view) => {
                const active = view.dataset.view === viewName;
                view.classList.toggle("is-active", active);
                view.hidden = !active;
            });
            if (updateHash && history.replaceState) history.replaceState(null, "", `#${viewName}`);
            if (window.TEIN && typeof window.TEIN.tick === "function") window.TEIN.tick("soft");
        };

        allButtons.forEach((button) => {
            if (button.dataset.teinShellBound) return;
            button.dataset.teinShellBound = "true";
            button.addEventListener("click", () => activate(button.dataset.view));
        });

        document.querySelectorAll(".tein-open-plan, .tein-focus-action").forEach((button) => {
            if (button.dataset.teinShellBound) return;
            button.dataset.teinShellBound = "true";
            button.addEventListener("click", () => activate("plan"));
        });

        const requested = window.location.hash.replace(/^#/, "");
        const initial = allButtons.some((button) => button.dataset.view === requested)
            ? requested
            : (allButtons.find((button) => button.dataset.view === "home")?.dataset.view || allButtons[0].dataset.view);
        activate(initial, false);
    }

    document.addEventListener("DOMContentLoaded", () => {
        setupLogin();
        setupCalculatorInteractions();
        setupSubjectRows();
        setupShell();
    });
})();
