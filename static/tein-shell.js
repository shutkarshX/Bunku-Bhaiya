(() => {
    "use strict";

    function setupShell() {
        const nav = document.querySelector(".tein-app-nav");
        if (!nav) return;

        const buttons = [...nav.querySelectorAll("button[data-view]")];
        const views = [...document.querySelectorAll(".tein-app-view[data-view]")];
        if (!buttons.length || !views.length) return;

        // The app shell owns the secondary controls too, so they do not float over
        // the dashboard and compete with the attendance instrument.
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
                        <div>
                            <strong>Appearance</strong>
                            <span>Auto follows your device. You can also force Light or Dark.</span>
                        </div>
                        <div class="tein-more-control" data-control="theme"></div>
                    </div>
                    <div class="tein-more-panel">
                        <div>
                            <strong>Interface sound</strong>
                            <span>Tactile feedback for important interactions.</span>
                        </div>
                        <div class="tein-more-control" data-control="sound"></div>
                    </div>
                </div>
                <div class="tein-more-note">
                    <strong>Portal data</strong>
                    <span>Attendance and subject history shown in TEIN come from the existing NIET portal data.</span>
                </div>
            `;

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

            if (updateHash && history.replaceState) {
                history.replaceState(null, "", `#${viewName}`);
            }

            if (window.TEIN && typeof window.TEIN.tick === "function") {
                window.TEIN.tick("soft");
            }
        };

        allButtons.forEach((button) => {
            if (button.dataset.teinShellBound) return;
            button.dataset.teinShellBound = "true";
            button.addEventListener("click", () => activate(button.dataset.view));
        });

        document.querySelectorAll(".tein-open-plan").forEach((button) => {
            if (button.dataset.teinShellBound) return;
            button.dataset.teinShellBound = "true";
            button.addEventListener("click", () => activate("plan"));
        });

        const requested = window.location.hash.replace("#", "");
        const initial = allButtons.some((button) => button.dataset.view === requested)
            ? requested
            : (allButtons.find((button) => button.dataset.view === "home")?.dataset.view || allButtons[0].dataset.view);

        activate(initial, false);
    }

    document.addEventListener("DOMContentLoaded", setupShell);
})();
