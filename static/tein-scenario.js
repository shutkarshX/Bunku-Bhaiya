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
          <span class="tein-eyebrow">Attendance planner</span>
          <h3>Plan your attendance</h3>
        </div>
        <div class="tein-current-attendance"><span>Right now</span><strong id="tein-current-pct">—</strong></div>
      </div>
      <div class="tein-scenario-context" id="tein-scenario-context">Loading your attendance…</div>
      <div class="tein-date-grid">
        <label>From<input id="tein-plan-from" type="date"></label>
        <label>To<input id="tein-plan-to" type="date"></label>
      </div>
      <div class="tein-period-summary"><strong id="tein-period-classes">—</strong><span>classes in this period</span></div>
      <div class="tein-scenario-control">
        <div><span class="tein-scenario-label">I'll attend</span><small id="tein-attend-available">—</small></div>
        <div class="tein-stepper"><button type="button" data-attend-step="-1" aria-label="Decrease classes attended">−</button><output id="tein-attend-count">0</output><button type="button" data-attend-step="1" aria-label="Increase classes attended">+</button></div>
      </div>
      <div class="tein-scenario-control">
        <div><span class="tein-scenario-label">I'll bunk</span><small id="tein-bunk-available">—</small></div>
        <div class="tein-stepper"><button type="button" data-bunk-step="-1" aria-label="Decrease classes to bunk">−</button><output id="tein-bunk-count">0</output><button type="button" data-bunk-step="1" aria-label="Increase classes to bunk">+</button></div>
      </div>
      <button type="button" class="tein-scenario-adjust" id="tein-event-toggle">Not sure about today's unrecorded classes?</button>
      <div class="tein-scenario-adjuster" id="tein-event-panel" hidden>
        <label>Were today's remaining classes an event?</label>
        <p class="tein-scenario-help">Tell TEIN how many event classes you attended. The rest can be planned as bunked.</p>
        <div class="tein-event-choice"><button type="button" id="tein-event-yes">Yes, event</button><button type="button" id="tein-event-no" class="is-active">No, normal classes</button></div>
        <div class="tein-event-attended" id="tein-event-attended-row" hidden><span>Event classes attended</span><div class="tein-stepper"><button type="button" data-event-step="-1" aria-label="Decrease event classes attended">−</button><output id="tein-event-count">0</output><button type="button" data-event-step="1" aria-label="Increase event classes attended">+</button></div></div>
      </div>
      <div class="tein-scenario-results">
        <div class="tein-scenario-result tein-result-main"><span>After your plan</span><strong id="tein-result-primary">—</strong></div>
        <div class="tein-scenario-result"><span>Attendance change</span><strong id="tein-result-change">—</strong></div>
        <div class="tein-scenario-result tein-scenario-status"><span>Status</span><strong id="tein-result-status">—</strong></div>
      </div>
      <div class="tein-scenario-footer" id="tein-scenario-footer">Simulation only · saved attendance unchanged</div>
    `;
    plan.prepend(card);

    let attendedCount = 0;
    let bunkCount = 0;
    let eventMode = false;
    let eventAttended = 0;
    let periodClasses = 0;
    let availableToPlan = 0;
    let portalRemaining = 0;
    let timer = null;
    const $ = (selector) => card.querySelector(selector);

    const today = new Date();
    const iso = (d) => { const copy = new Date(d); copy.setMinutes(copy.getMinutes() - copy.getTimezoneOffset()); return copy.toISOString().slice(0, 10); };
    const todayISO = iso(today);
    $("#tein-plan-from").value = todayISO;
    $("#tein-plan-to").value = todayISO;
    $("#tein-plan-from").min = todayISO;
    $("#tein-plan-to").min = todayISO;

    function updateLocalState() {
      availableToPlan = Math.max(0, periodClasses - (eventMode ? eventAttended : 0));
      attendedCount = Math.min(attendedCount, Math.max(0, availableToPlan - bunkCount));
      bunkCount = Math.min(bunkCount, Math.max(0, availableToPlan - attendedCount));
      $("#tein-attend-count").textContent = attendedCount;
      $("#tein-bunk-count").textContent = bunkCount;
      $("#tein-event-count").textContent = eventAttended;
      $("#tein-period-classes").textContent = periodClasses;
      $("#tein-attend-available").textContent = `${Math.max(0, availableToPlan - bunkCount)} max`;
      $("#tein-bunk-available").textContent = `${Math.max(0, availableToPlan - attendedCount)} max`;
    }

    async function refresh() {
      try {
        const from = $("#tein-plan-from").value;
        const to = $("#tein-plan-to").value;
        const response = await fetch("/scenario", {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify({ scope: "today", classes_missed: bunkCount, event_mode: eventMode, event_attended: eventAttended, plan_from: from, plan_to: to, planned_attended: attendedCount, planned_bunked: bunkCount }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Planner unavailable");

        portalRemaining = Number(data.portal_today_remaining) || 0;
        periodClasses = Number(data.planner_period_classes) || 0;
        eventAttended = Math.min(eventAttended, portalRemaining);
        availableToPlan = Number(data.available_classes) || 0;
        attendedCount = Math.min(attendedCount, Math.max(0, availableToPlan - bunkCount));
        bunkCount = Math.min(bunkCount, Math.max(0, availableToPlan - attendedCount));
        updateLocalState();

        $("#tein-current-pct").textContent = `${Number(data.current_percentage) || 0}%`;
        $("#tein-scenario-context").textContent = from === to
          ? `${portalRemaining} attendance ${portalRemaining === 1 ? "class is" : "classes are"} not recorded yet`
          : `${periodClasses} scheduled classes between ${from} and ${to}`;

        const baselineAttended = Number(data.current_attended) || 0;
        const baselineTotal = Number(data.current_total) || 0;
        const simulatedAttended = baselineAttended + attendedCount;
        const simulatedTotal = baselineTotal + attendedCount + bunkCount;
        const pct = simulatedTotal ? Math.round((simulatedAttended / simulatedTotal) * 10000) / 100 : Number(data.current_percentage) || 0;
        const change = Math.round((pct - (Number(data.current_percentage) || 0)) * 100) / 100;
        $("#tein-result-primary").textContent = `${pct}%`;
        $("#tein-result-change").textContent = `${change > 0 ? "+" : ""}${change}%`;
        $("#tein-result-status").textContent = pct >= 75 ? "Safe" : "Below 75%";
        const eventDetail = eventMode ? ` · ${eventAttended} event attended` : "";
        $("#tein-scenario-footer").textContent = `${attendedCount} attending · ${bunkCount} bunking${eventDetail} · simulation only`;
      } catch (error) {
        $("#tein-scenario-context").textContent = "Planner unavailable right now.";
        $("#tein-result-primary").textContent = "—";
        $("#tein-result-change").textContent = "—";
        $("#tein-result-status").textContent = "—";
        $("#tein-scenario-footer").textContent = error.message || "Try again.";
      }
    }

    function scheduleRefresh() { if (timer) clearTimeout(timer); timer = setTimeout(refresh, 120); }

    $("#tein-plan-from").addEventListener("change", () => { const to = $("#tein-plan-to"); if (to.value < $("#tein-plan-from").value) to.value = $("#tein-plan-from").value; attendedCount = 0; bunkCount = 0; scheduleRefresh(); });
    $("#tein-plan-to").addEventListener("change", () => { if ($("#tein-plan-to").value < $("#tein-plan-from").value) $("#tein-plan-to").value = $("#tein-plan-from").value; attendedCount = 0; bunkCount = 0; scheduleRefresh(); });

    card.querySelectorAll("[data-attend-step]").forEach((button) => button.addEventListener("click", () => {
      attendedCount = Math.max(0, Math.min(availableToPlan - bunkCount, attendedCount + Number(button.dataset.attendStep)));
      updateLocalState(); scheduleRefresh(); if (window.TEIN?.tick) window.TEIN.tick("soft");
    }));
    card.querySelectorAll("[data-bunk-step]").forEach((button) => button.addEventListener("click", () => {
      bunkCount = Math.max(0, Math.min(availableToPlan - attendedCount, bunkCount + Number(button.dataset.bunkStep)));
      updateLocalState(); scheduleRefresh(); if (window.TEIN?.tick) window.TEIN.tick("soft");
    }));

    $("#tein-event-toggle").addEventListener("click", () => { $("#tein-event-panel").hidden = !$("#tein-event-panel").hidden; });
    $("#tein-event-yes").addEventListener("click", () => { eventMode = true; $("#tein-event-yes").classList.add("is-active"); $("#tein-event-no").classList.remove("is-active"); $("#tein-event-attended-row").hidden = false; updateLocalState(); scheduleRefresh(); });
    $("#tein-event-no").addEventListener("click", () => { eventMode = false; eventAttended = 0; attendedCount = 0; bunkCount = 0; $("#tein-event-no").classList.add("is-active"); $("#tein-event-yes").classList.remove("is-active"); $("#tein-event-attended-row").hidden = true; updateLocalState(); scheduleRefresh(); });
    card.querySelectorAll("[data-event-step]").forEach((button) => button.addEventListener("click", () => { eventAttended = Math.max(0, Math.min(portalRemaining, eventAttended + Number(button.dataset.eventStep))); updateLocalState(); refresh(); if (window.TEIN?.tick) window.TEIN.tick("soft"); }));

    refresh();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bootScenario);
  else bootScenario();
})();
