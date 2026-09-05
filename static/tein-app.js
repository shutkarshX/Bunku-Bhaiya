(() => {
  "use strict";

  function make(tag, cls, text) {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (text !== undefined) el.textContent = text;
    return el;
  }

  function buildAppShell() {
    const container = document.querySelector(".container");
    if (!container || container.dataset.teinShell) return;
    container.dataset.teinShell = "true";

    const normalDashboard = container.querySelector(".stats")?.closest(".summary");
    if (!normalDashboard) return;

    const allChildren = Array.from(container.children);
    const normalIndex = allChildren.indexOf(normalDashboard);
    if (normalIndex < 0) return;

    const following = allChildren.slice(normalIndex + 1);
    const planNodes = following.filter((node) => node.matches(".summary, .bunk-results"));
    const subjectTable = following.find((node) => node.classList.contains("table-container"));
    const subjectDetails = following.find((node) => node.id === "subject-attendance-details");

    const nav = make("nav", "tein-app-nav");
    nav.setAttribute("aria-label", "TEIN sections");
    const views = {};

    function addNav(key, label) {
      const button = make("button", "", label);
      button.type = "button";
      button.dataset.view = key;
      button.addEventListener("click", () => activate(key));
      nav.appendChild(button);
      return button;
    }

    const homeButton = addNav("home", "Home");
    const planButton = addNav("plan", "Plan");
    const subjectsButton = addNav("subjects", "Subjects");
    const moreButton = addNav("more", "More");

    const home = make("section", "tein-app-view tein-home-view");
    const plan = make("section", "tein-app-view tein-plan-view");
    const subjects = make("section", "tein-app-view tein-subjects-view");
    const more = make("section", "tein-app-view tein-more-view");
    views.home = home; views.plan = plan; views.subjects = subjects; views.more = more;

    const focus = make("div", "tein-focus");
    const focusCopy = make("div");
    focusCopy.append(
      make("span", "tein-focus-kicker", "NEXT CHECKPOINT"),
      make("h2", "", "Attendance plan"),
      make("p", "", "Your active checkpoint stays here. Completed checkpoints stay compact.")
    );
    const focusAction = make("button", "attendance-button tein-focus-action", "Open Plan");
    focusAction.type = "button";
    focusAction.addEventListener("click", () => activate("plan"));
    focus.append(focusCopy, focusAction);
    home.appendChild(focus);

    const checkpoints = make("div", "tein-checkpoints");
    ["First Sessional", "Second Sessional", "Third Sessional"].forEach((name, i) => {
      const item = make("div", "tein-checkpoint");
      item.dataset.index = String(i);
      const mark = make("span", "tein-checkpoint-mark", i === 0 ? "✓" : i === 1 ? "→" : "○");
      const copy = make("div", "tein-checkpoint-copy");
      copy.append(make("strong", "", name), make("small", "", i === 0 ? "Completed" : i === 1 ? "Active" : "Upcoming"));
      item.append(mark, copy);
      checkpoints.appendChild(item);
    });
    home.appendChild(checkpoints);

    const homeStats = normalDashboard.cloneNode(true);
    home.appendChild(homeStats);

    const planTitle = make("div", "tein-view-title");
    planTitle.append(make("h2", "", "Plan"), make("p", "", "Attendance through your checkpoints"));
    plan.appendChild(planTitle);
    planNodes.forEach((node) => plan.appendChild(node));

    const subjectTitle = make("div", "tein-view-title");
    subjectTitle.append(make("h2", "", "Subjects"), make("p", "", "Select a subject to inspect its real portal history"));
    subjects.appendChild(subjectTitle);
    if (subjectTable) subjects.appendChild(subjectTable);
    if (subjectDetails) subjects.appendChild(subjectDetails);

    const moreTitle = make("div", "tein-view-title");
    moreTitle.append(make("h2", "", "More"), make("p", "", "Interface preferences and account tools"));
    more.appendChild(moreTitle);
    const controls = make("div", "tein-more-controls");
    controls.append(
      make("p", "", "Use the controls in the lower corner to change sound and theme."),
      make("p", "", "Theme defaults to your device preference and can be overridden manually.")
    );
    more.appendChild(controls);

    const mount = make("main", "tein-app-shell");
    mount.append(nav, home, plan, subjects, more);
    normalDashboard.replaceWith(mount);

    // Remove original nodes now owned by their views from the container root.
    [normalDashboard, ...planNodes, subjectTable, subjectDetails].forEach((node) => {
      if (node && node.parentElement === container) node.remove();
    });

    function activate(key) {
      Object.entries(views).forEach(([name, view]) => {
        view.classList.toggle("is-active", name === key);
      });
      nav.querySelectorAll("button").forEach((button) => {
        button.classList.toggle("is-active", button.dataset.view === key);
      });
      localStorage.setItem("tein-view", key);
      window.dispatchEvent(new CustomEvent("tein:view", { detail: key }));
      if (key === "subjects") {
        subjects.querySelectorAll(".subject-attendance-row").forEach((row) => row.setAttribute("role", "button"));
      }
    }

    // A completed current checkpoint is never allowed to become the hero.
    const headingText = Array.from(plan.querySelectorAll("h2,h3")).map((n) => n.textContent).join(" ");
    if (/First Sessional/i.test(headingText) && /Second Sessional/i.test(headingText)) {
      focusCopy.querySelector("h2").textContent = "Second Sessional";
      focusCopy.querySelector("p").textContent = "The next active checkpoint is the one TEIN keeps in focus.";
    }

    const storedView = localStorage.getItem("tein-view");
    activate(["home", "plan", "subjects", "more"].includes(storedView) ? storedView : "home");
  }

  document.addEventListener("DOMContentLoaded", buildAppShell);
})();
