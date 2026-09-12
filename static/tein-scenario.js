(() => {
  "use strict";

  function bootScenario() {
    const plan = document.querySelector(".tein-plan-view");
    if (!plan || plan.querySelector(".tein-scenario-card")) return;

    const card = document.createElement("section");
    card.className = "tein-scenario-card";
    card.innerHTML = `
      <div class="tein-scenario-head">
        <div>
          <span class="tein-eyebrow">Quick planning</span>
          <h3 id="tein-scenario-title">What if I bunk today?</h3>
        </div>
        <div class="tein-scenario-switch" role="tablist" aria-label="Scenario scope">
          <button type="button" class="is-active" data-scope="today" role="tab" aria-selected="true">Today</button>
          <button type="button" data-scope="checkpoint" role="tab" aria-selected="false">Checkpoint</button>
        </div>
      </div>
      <div class="tein-scenario-context" id="tein-scenario-context">Checking today's attendance…</div>

      <button type="button" class="tein-scenario-adjust" id="tein-event-toggle">Not sure about these remaining classes?</button>
      <div class="tein-scenario-adjuster" id="tein-event-panel" hidden>
        <label>Were the remaining classes an event?</label>
        <p class="tein-scenario-help">If yes, tell TEIN how many event classes you attended. The rest stay available to miss.</p>
        <div class="tein-event-choice">
          <button type="button" class="is-active" id="tein-event-yes">Yes, event</button>
          <button type="button" id="tein-event-no">No, normal classes</button>
        </div>
        <div class="tein-event-attended" id="tein-event-attended-row">
          <span>Event classes attended</span>
          <div class="tein-stepper">
            <button type="button" data-event-step="-1" aria-label="Decrease event classes attended">−</button>
            <output id="tein-event-count" aria-live="polite">0</output>
            <button type="button" data-event-step="1" aria-label="Increase event classes attended">+</button>
          </div>
        </div>
      </div>

      <div class="tein-scenario-control">
        <div>
          <span class="tein-scenario-label" id="tein-scenario-label">Classes to miss today</span>
          <small id="tein-scenario-available"></small>
        </div>
        <div class="tein-stepper">
          <button type="button" data-step="-1" aria-label="Decrease classes to miss">−</button>
          <output id="tein-scenario-count" aria-live="polite">0</output>
          <button type="button" data-step="1" aria-label="Increase classes to miss">+</button>
        </div>
      </div>
      <div class="tein-scenario-results" aria-live="polite">
        <div class="tein-scenario-result"><span id="tein-result-primary-label">After today</span><strong id="tein-result-primary">—</strong></div>
        <div class="tein-scenario-result"><span id="tein-result-secondary-label">At checkpoint</span><strong id="tein-result-secondary">—</strong></div>
        <div class="tein-scenario-result tein-scenario-status"><span>Status</span><strong id="tein-result-status">—</strong></div>
      </div>
      <div class="tein-scenario-footer" id="tein-scenario-footer"></div>
    `;
    plan.prepend(card);

    let scope = "today";
    let count = 0;
    let eventMode = false;
    let eventAttended = 0;
    let available = 0;
    let portalRemaining = 0;
    let timer = null;
    const $ = (selector) => card.querySelector(selector);

    function setScope(next) {
      scope = next;
      count = 0;
      $("#tein-event-panel").hidden = scope !== "today" || $("#tein-event-panel").hidden;
      if (scope !== "today") $("#tein-event-panel").hidden = true;
      $("#tein-event-toggle").hidden = scope !== "today";
      $("#tein-scenario-title").textContent = scope === "today" ? "What if I bunk today?" : "How much can I bunk?";
      $("#tein-scenario-label").textContent = scope === "today" ? "Classes to miss today" : "Classes to miss before checkpoint";
      card.querySelectorAll("[data-scope]").forEach((button) => {
        const active = button.dataset.scope === scope;
        button.classList.toggle("is-active", active);
        button.setAttribute("aria-selected", active ? "true" : "false");
      });
      refresh();
    }

    async function refresh() {
      $("#tein-scenario-count").textContent = count;
      $("#tein-result-primary").textContent = "…";
      $("#tein-result-secondary").textContent = "…";
      $("#tein-result-status").textContent = "…";
      try {
        const response = await fetch("/scenario", {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify({ scope, classes_missed: count, event_mode: scope === "today" && eventMode, event_attended: scope === "today" ? eventAttended : 0 }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Scenario unavailable");

        portalRemaining = Number(data.portal_today_remaining) || 0;
        available = Number(data.available_classes) || 0;
        count = Math.min(count, available);
        eventAttended = Math.min(eventAttended, portalRemaining);
        $("#tein-scenario-count").textContent = count;
        $("#tein-event-count").textContent = eventAttended;
        $("#tein-scenario-available").textContent = `${available} available to miss`;

        if (scope === "today") {
          const source = eventMode ? `${eventAttended} event ${eventAttended === 1 ? "class" : "classes"} attended` : `${portalRemaining} unrecorded ${portalRemaining === 1 ? "class" : "classes"}`;
          $("#tein-scenario-context").textContent = `${portalRemaining} attendance ${portalRemaining === 1 ? "class is" : "classes are"} not recorded yet · ${source}`;
          $("#tein-result-primary-label").textContent = "After today";
          $("#tein-result-primary").textContent = data.today ? `${data.today.percentage}%` : "—";
          $("#tein-result-secondary-label").textContent = data.checkpoint_date ? `At ${data.checkpoint_date}` : "At checkpoint";
          $("#tein-result-secondary").textContent = data.checkpoint ? `${data.checkpoint.percentage}%` : "—";
        } else {
          $("#tein-scenario-context").textContent = `${available} future classes to the next checkpoint · simulation only`;
          $("#tein-result-primary-label").textContent = "At checkpoint";
          $("#tein-result-primary").textContent = data.checkpoint ? `${data.checkpoint.percentage}%` : "—";
          $("#tein-result-secondary-label").textContent = "Safe leave remaining";
          $("#tein-result-secondary").textContent = `${data.remaining_safe_leave} classes`;
        }

        const status = data.checkpoint_status || "";
        $("#tein-result-status").textContent = status.charAt(0).toUpperCase() + status.slice(1);
        const detail = eventMode && scope === "today" ? `${eventAttended} event attended · ` : "";
        $("#tein-scenario-footer").textContent = `${detail}${count} class${count === 1 ? "" : "es"} simulated · saved attendance unchanged`;
      } catch (error) {
        $("#tein-scenario-context").textContent = "Scenario unavailable right now.";
        $("#tein-result-primary").textContent = "—";
        $("#tein-result-secondary").textContent = "—";
        $("#tein-result-status").textContent = "—";
        $("#tein-scenario-footer").textContent = error.message || "Try again.";
      }
    }

    $("#tein-event-toggle").addEventListener("click", () => {
      $("#tein-event-panel").hidden = !$("#tein-event-panel").hidden;
    });

    $("#tein-event-yes").addEventListener("click", () => {
      eventMode = true;
      $("#tein-event-yes").classList.add("is-active");
      $("#tein-event-no").classList.remove("is-active");
      $("#tein-event-attended-row").hidden = false;
      refresh();
    });

    $("#tein-event-no").addEventListener("click", () => {
      eventMode = false;
      eventAttended = 0;
      count = 0;
      $("#tein-event-no").classList.add("is-active");
      $("#tein-event-yes").classList.remove("is-active");
      $("#tein-event-attended-row").hidden = true;
      refresh();
    });

    card.querySelectorAll("[data-event-step]").forEach((button) => {
      button.addEventListener("click", () => {
        const delta = Number(button.dataset.eventStep);
        eventAttended = Math.max(0, Math.min(portalRemaining, eventAttended + delta));
        refresh();
        if (window.TEIN?.tick) window.TEIN.tick("soft");
      });
    });

    card.querySelectorAll("[data-scope]").forEach((button) => {
      button.addEventListener("click", () => {
        if (window.TEIN?.tick) window.TEIN.tick("soft");
        setScope(button.dataset.scope);
      });
    });

    card.querySelectorAll("[data-step]").forEach((button) => {
      button.addEventListener("click", () => {
        const delta = Number(button.dataset.step);
        count = Math.max(0, Math.min(available, count + delta));
        if (timer) clearTimeout(timer);
        timer = setTimeout(refresh, 90);
        $("#tein-scenario-count").textContent = count;
        if (window.TEIN?.tick) window.TEIN.tick("soft");
      });
    });

    refresh();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bootScenario);
  else bootScenario();
})();
