(() => {
    "use strict";

    function setupShell() {
        const nav = document.querySelector(".tein-app-nav");
        if (!nav) return;

        const buttons = [...nav.querySelectorAll("button[data-view]")];
        const views = [...document.querySelectorAll(".tein-app-view[data-view]")];
        if (!buttons.length || !views.length) return;

        const activate = (viewName, updateHash = true) => {
            buttons.forEach((button) => {
                const active = button.dataset.view === viewName;
                button.classList.toggle("is-active", active);
                button.setAttribute("aria-selected", String(active));
            });

            views.forEach((view) => {
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

        buttons.forEach((button) => {
            button.addEventListener("click", () => activate(button.dataset.view));
        });

        const requested = window.location.hash.replace("#", "");
        const initial = buttons.some((button) => button.dataset.view === requested)
            ? requested
            : (buttons.find((button) => button.dataset.view === "home")?.dataset.view || buttons[0].dataset.view);

        activate(initial, false);
    }

    document.addEventListener("DOMContentLoaded", setupShell);
})();
