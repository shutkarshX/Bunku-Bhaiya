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
      <div class="tein-scenario-context" id="tein-scenario-context">Checking today's remaining classes…</div>
      <button type="button" class="tein-scenario-adjust" id="tein-scenario-adjust">Adjust today's schedule</button>
      <div class="tein-scenario-adjuster" id="tein-scenario-adjuster" hidden>
        <label for="tein-today-remaining">How many classes are actually still remaining today?</label>
        <div class="tein-adjust-row">
          <input id="tein-today-remaining" type="number" min="0" max="8" inputmode="numeric">
          <button type="button" class="tein-scenario-save" id="tein-scenario-save">Save</button>
          <button type="button" class="tein-scenario-clear" id="tein-scenario-clear">Use automatic</button>
        </div>
        <small>This changes today only. Tomorrow returns to automatic calculation.</small>
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
        <div class="tein-scenario-result">
          <span id="tein-result-primary-label">After today</span>
          <strong id="tein-result-primary">—</strong>
        </div>
        <div class="tein-scenario-result">
          <span id="tein-result-secondary-label">At checkpoint</span>
          <strong id="tein-result-secondary">—</strong>
        </div>
        <div class="tein-scenario-result tein-scenario-status">
          <span>Status</span>
          <strong id="tein-result-status">—</strong>
        </div>
      </div>
      <div class="tein-scenario-footer" id="tein-scenario-footer"></div>
    `;
    plan.prepend(card);

    let scope = "today";
    let count = 0;
    let available = 0;
    let timer = null;

    const $ = (selector) => card.querySelector(selector);

    function setScope(next) {
      scope = next;
      count = 0;
      $("#tein-scenario-adjust").hidden = scope !== "today";
      $("#tein-scenario-adjuster").hidden = true;
      card.querySelectorAll("[data-scope]").forEach((button) => {
        const active = button.dataset.scope === scope;
        button.classList.toggle("is-active", active);
        button.setAttribute("aria-selected", active ? "true" : "false");
      });
      $("#tein-scenario-title").textContent = scope === "today" ? "What if I bunk today?" : "How much can I bunk?";
      $("#tein-scenario-label").textContent = scope === "today" ? "Classes to miss today" : "Classes to miss before checkpoint";
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
          body: JSON.stringify({ scope, classes_missed: count }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Scenario unavailable");

        available = Number(data.available_classes) || 0;
        count = Math.min(count, available);
        $("#tein-scenario-count").textContent = count;
        $("#tein-scenario-available").textContent = `${available} available`;

        if (scope === "today") {
          const source = data.today_override_active ? "manual schedule" : "automatic estimate";
          $("#tein-scenario-context").textContent = `${data.today_remaining} classes remaining today · ${source}`;
          $("#tein-scenario-primary-label");
          $("#tein-result-primary-label").textContent = "After today";
          $("#tein-result-primary").textContent = data.today ? `${data.today.percentage}%` : "—";
          $("#tein-result-secondary-label").textContent = data.checkpoint_date ? `At ${data.checkpoint_date}` : "At checkpoint";
          $("#tein-result-secondary").textContent = data.checkpoint ? `${data.checkpoint.percentage}%` : "—";
          const adjust = $("#tein-today-remaining");
          if (adjust && document.activeElement !== adjust) adjust.value = data.today_remaining;
        } else {
          $("#tein-scenario-context").textContent = `${available} future classes to the next checkpoint · simulation only`;
          $("#tein-result-primary-label").textContent = "At checkpoint";
          $("#tein-result-primary").textContent = data.checkpoint ? `${data.checkpoint.percentage}%` : "—";
          $("#tein-result-secondary-label").textContent = "Safe leave remaining";
          $("#tein-result-secondary").textContent = `${data.remaining_safe_leave} classes`;
        }

        const status = data.checkpoint_status || "";
        $("#tein-result-status").textContent = status.charAt(0).toUpperCase() + status.slice(1);
        $("#tein-scenario-footer").textContent = `${count} class${count === 1 ? "" : "es"} simulated · your saved plan is unchanged`;
      } catch (error) {
        $("#tein-scenario-context").textContent = "Scenario unavailable right now.";
        $("#tein-result-primary").textContent = "—";
        $("#tein-result-secondary").textContent = "—";
        $("#tein-result-status").textContent = "—";
        $("#tein-scenario-footer").textContent = error.message || "Try again.";
      }
    }

    $("#tein-scenario-adjust").addEventListener("click", () => {
      $("#tein-scenario-adjuster").hidden = !$("#tein-scenario-adjuster").hidden;
    });

    $("#tein-scenario-save").addEventListener("click", async () => {
      const remaining = Number($("#tein-today-remaining").value);
      if (!Number.isInteger(remaining) || remaining < 0 || remaining > 8) return;
      const response = await fetch("/today-adjust", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ remaining_classes: remaining }),
      });
      if (!response.ok) return;
      $("#tein-scenario-adjuster").hidden = true;
      count = 0;
      refresh();
    });

    $("#tein-scenario-clear").addEventListener("click", async () => {
      const response = await fetch("/today-adjust", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ action: "clear" }),
      });
      if (!response.ok) return;
      $("#tein-scenario-adjuster").hidden = true;
      count = 0;
      refresh();
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
