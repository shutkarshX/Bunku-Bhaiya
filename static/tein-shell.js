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

    function setupCalculatorInteractions() {
        document.querySelectorAll('form[action^="/sessional-"]').forEach((form) => {
            if (form.dataset.teinCalcBound) return;
            form.dataset.teinCalcBound = "true";
            const refresh = () => {
                if (typeof window.updateLeavePreview === "function") window.updateLeavePreview(form);
            };
            form.querySelectorAll("input").forEach((input) => input.addEventListener("input", refresh));
            refresh();
        });
    }

    function setupShell() {
        const nav = document.querySelector(".tein-app-nav");
        if (!nav) return;

        // setupAppShell creates the three buttons before this file runs, but those
        // buttons historically did not carry data-view. Wire them deterministically.
        const navButtons = [...nav.querySelectorAll("button")];
        const viewNames = ["home", "plan", "subjects"];
        navButtons.slice(0, 3).forEach((button, index) => {
            if (!button.dataset.view) button.dataset.view = viewNames[index];
            if (!button.getAttribute("aria-selected")) button.setAttribute("aria-selected", "false");
        });

        const initialViews = [...document.querySelectorAll(".tein-app-view[data-view]")];
        const requiredViews = viewNames.every((name) => initialViews.some((view) => view.dataset.view === name));
        if (!navButtons.length || !requiredViews) return;

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
            : "home";
        activate(initial, false);
    }

    document.addEventListener("DOMContentLoaded", () => {
        setupLogin();
        setupCalculatorInteractions();
        setupShell();
    });
})();