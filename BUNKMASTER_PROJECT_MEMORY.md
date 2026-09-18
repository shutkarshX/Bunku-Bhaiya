# BunkMaster — Project Memory / Workflow Brain

> Living project context for continuing development without losing the reasoning behind the code.
>
> **Primary branch:** `version-D`
>
> **Repository:** `shutkarshX/Bunku-Bhaiya`
>
> **Rule:** `main` must remain untouched. All current development belongs on `version-D`.

---

## 1. How we work

This file is the project's continuity/backup brain.

When continuing work:

1. Read this file first.
2. Work only on `version-D`.
3. Inspect the existing implementation before changing it.
4. Preserve the attendance model and architecture documented below unless the user explicitly changes the rule.
5. Prefer small, understandable files over giant HTML/Python blocks.
6. Keep backend calculations separate from UI templates.
7. Reuse shared state/data instead of making one feature initialize another feature accidentally.
8. After a meaningful change, update this file so the reasoning is not lost.
9. Commit changes with a clear commit message.
10. Give the user the exact pull/run commands.

### Normal local run

The user does **not** use the virtual environment.

```powershell
cd "C:\Users\Roger\Desktop\Bunk Clean\Bunku-Bhaiya"
git switch version-D
git pull origin version-D
python app.py
```

Do not add `.venv` activation commands unless the user explicitly says they are using it.

---

# 2. Product idea

BunkMaster is an attendance planning tool built around the user's actual NIET portal attendance.

The important conceptual separation is:

- **Actual state** = what the portal currently says.
- **Unmarked/Frozen state** = classes that have already happened but are not posted to the portal yet.
- **Scenario state** = temporary hypothetical attendance used only for What-If calculations.
- **Result** = projected attendance produced by a scenario.

What-If calculations must never modify the real portal attendance.

---

# 3. Authoritative attendance model

Use these definitions everywhere.

Let:

- `P` = Present
- `A` = Absent
- `U` = Unmarked / Frozen

```text
TOTAL = P + A + U

PORTAL ATTENDANCE = P / (P + A)

SITE ATTENDANCE = P / TOTAL

EFFECTIVE ATTENDANCE = (P + U) / TOTAL
```

## Meaning of U / Unmarked

Unmarked classes:

- have already been held;
- have not yet been posted to the portal;
- count in the denominator for Site attendance;
- count as present for Effective attendance;
- are NOT future classes.

Future classes are separate and are not included in current/site/effective attendance.

### Important rejected formulas

Do **not** use:

```text
P / (P + A + U)
```

as the old/current attendance formula.

Do **not** use `P + U` as the Site numerator.

Site numerator remains `P`.

Do **not** include future classes in current/site/effective totals.

---

# 4. Known calculation examples

For:

```text
P = 254
A = 88
U = 4
```

the expected values are:

```text
Portal    = 254 / 342 = 74.27%
Site      = 254 / 346 = 73.41%
Effective = 258 / 346 = 74.57%
```

Latest live verification also showed:

```text
Present = 284
Unmarked = 1
Total = 374

Site      = 284 / 374 = 75.94%
Effective = 285 / 374 = 76.20%
```

These values confirmed the current attendance-state implementation.

---

# 5. Current main navigation

The intended top-level structure is now:

```text
Home
│
├── What-If
│    │
│    ├── [ Today ]
│    ├── [ Sessional Checkpoints ]
│    └── [ future scenario buttons ]
│
└── Subject Attendance
```

## Important UX decision

There is **ONE** top-level page named **What-If**.

There must NOT be a visible top-level:

- Planner Setup
- Today What-If
- Sessional What-If
- separate page for every future scenario

Instead:

```text
What-If
   ↓
Scenario buttons
   ↓
Selected scenario
   ↓
That scenario's setup + questions + calculation
```

The setup steps are part of the selected scenario flow.

---

# 6. What the user wants from the What-If page

The page should initially be simple:

```text
What-If

Choose what you want to simulate.
Your real portal attendance is never changed by these scenarios.

[ Today ]
Attend or bunk today's remaining classes

[ Sessional Checkpoints ]
Plan attendance through First, Second and Third Sessional
```

Clicking a scenario keeps the user on the same page:

```text
/what-if?scenario=today
/what-if?scenario=sessional
```

Only the selected scenario's content should be shown.

Future scenarios should be added as more buttons inside this same page.

---

# 7. Current screenshot / UI note

A screenshot was taken showing:

- Home / What-If / Subject Attendance navigation;
- What-If heading and description;
- two scenario links;
- the scenario links appeared as plain blue underlined browser links.

This was because the screenshot represented the UI before the dedicated scenario-button CSS was applied.

The intended final styling is:

- card-like scenario buttons;
- clean spacing;
- hover movement/shadow;
- active scenario shown in the dark BunkMaster style;
- responsive one-column layout on small screens.

The CSS class is:

```text
.what-if-scenario-buttons
.what-if-scenario-button
.what-if-scenario-button.active
```

---

# 8. Scenario architecture

The project should not become a collection of independent calculators.

The intended architecture is:

```text
                 RIGHT NOW
                    ↓
          Current Effective State
                    +
             Today's Event
                    ↓
          Effective Starting State
                    ↓
             scenario_engine
                    ↓
        ┌───────────┼───────────┐
        │           │           │
      TODAY      DATE PLAN     TARGET
        │
        ↓
Projected Effective Attendance
```

The shared engine is:

```text
scenario_engine.py
```

Common scenario output should ultimately use the same concepts:

- projected attended;
- projected total;
- projected percentage.

Do not duplicate the same attendance math in every scenario.

---

# 9. Critical What-If starting-point rule

Every scenario starts from:

> **Today / Right Now**

The event decision is not its own scenario.

Today's event information is simply part of establishing the scenario's starting state.

Correct conceptual flow:

```text
Right Now
  ↓
Effective attendance
  ↓
Today's event information, if needed
  ↓
Today's remaining ordinary classes
  ↓
Scenario-specific planning
  ↓
Projection
```

Once the user answers the event question, the answer is shared.

The user should NOT have to answer the same event question separately for every scenario.

---

# 10. Event handling rule

An event is a planning-only adjustment for today's currently-unposted/remaining class window.

If today's event is stored:

- event-attended classes increase planning attended;
- event classes increase planning total;
- event-covered classes are removed from today's remaining ordinary classes;
- actual portal attendance is unchanged.

For the starting state:

```text
starting_attended = effective_attended + event_attended
starting_total    = effective_total + event_classes
```

Today's ordinary remaining classes become:

```text
remaining_today = portal_remaining_today - event_classes
```

The event is therefore applied once to the shared starting state.

---

# 11. Shared subject-detail data architecture

A bug was found where:

> Subject Attendance could not expand/show full attendance unless Attendance Planner had been opened first.

That meant Planner was accidentally acting as the initializer for detailed subject data.

The correct architecture is shared data loading:

```text
Attendance Planner
       ↓
load_subject_details(token)
       ↓
shared cache

Subject Attendance
       ↓
load_subject_details(token)
       ↓
same cache
```

The first feature that needs detailed data loads it.

Later features reuse the same data.

No feature should depend on another feature being opened first.

---

# 12. Portal cache design

`portal.py` currently has server-side in-memory caches:

```python
_SUBJECT_DETAILS_CACHE = {}
_PORTAL_SESSION_CACHE = {}
```

The authenticated Playwright storage state is saved server-side using a token.

The token is stored with the attendance subject data as:

```text
_bunkmaster_subject_details_token
```

Detailed subject history is loaded through:

```python
load_subject_details(details_token)
```

Today-specific attendance is derived from that shared detailed data through:

```python
get_today_attendance(details_token)
```

This avoids performing separate full subject scans for every page.

---

# 13. Portal data flow

Initial login:

```text
/get-attendance
   ↓
portal.get_attendance()
   ↓
aggregate attendance + course data
   ↓
save authenticated portal state server-side
   ↓
store token in attendance data
```

Detailed scan is deferred.

When detailed data is actually needed:

```text
load_subject_details(token)
   ↓
reuse cached data if available
   ↓
otherwise use saved authenticated storage state
   ↓
fetch subject-wise attendance
   ↓
cache complete subject history
```

Today calculation:

```text
get_today_attendance(token)
   ↓
load_subject_details(token)
   ↓
read cached records
   ↓
count today's logged classes
   ↓
calculate today's remaining classes
```

---

# 14. Portal error behavior

Portal failures should not silently become partial/incorrect attendance data.

Important exceptions:

```python
PortalUnavailableError
PortalLoginError
```

General unexpected portal failures are treated as portal unavailable by the Flask layer.

The user should see an unavailable/error state rather than a misleading partial calculation.

---

# 15. Today scenario

Scenario 1 is:

> **Today — Attend or bunk today's remaining classes**

It uses the effective starting state.

User inputs:

```text
Attend: X
Bunk: Y
```

Validation:

```text
X + Y <= remaining_today
```

Projection:

```text
projected_attended = starting_attended + X

projected_total = starting_total + X + Y

projected_percentage =
    projected_attended / projected_total
```

The UI shows:

```text
Right now → After today
```

and the number of planned classes remaining after the plan.

This is planning-only.

---

# 16. Sessional Checkpoints scenario

Scenario 2 is:

> **Sessional Checkpoints — Plan attendance through First, Second and Third Sessional**

It contains the existing checkpoint tracker/calculator flow.

The sessional tracker is not a separate top-level page.

It is part of the selected Sessional scenario.

---

# 17. Sessional tracker

The right-side tracker represents academic checkpoint state.

Example:

```text
✓ First Sessional
  Passed

● Second Sessional
  Current

○ Third Sessional
  Upcoming
```

Color/state classes:

```text
passed
current
upcoming
```

A passed checkpoint does not display made-up historical attendance.

---

# 18. Current checkpoint projection

After the user chooses leave for the current checkpoint, the current checkpoint can show:

```text
Second Sessional
Current

Your checkpoint attendance
75.39%
X / Y classes

This becomes the starting attendance for the next sessional.
```

This is a **forward projection**, not historical portal data.

---

# 19. Planner target rule — authoritative

The attendance requirement is selected **once per planning session**.

It is NOT per checkpoint.

Correct:

```text
planner_target_attendance = 75
```

Then:

```text
First Sessional  → 75%
Second Sessional → 75%
Third Sessional  → 75%
```

If the user enters 80%:

```text
First Sessional  → 80%
Second Sessional → 80%
Third Sessional  → 80%
```

Do NOT create:

```text
checkpoint_targets = {
    first: 75,
    second: 80,
    third: 70
}
```

The target is one user-level planning value.

---

# 20. Planner target storage

Current helper design:

```python
def get_planner_target():
    return session.get("planner_target_attendance")
```

```python
def save_planner_target(value):
    try:
        target = int(value)
    except (TypeError, ValueError):
        return False

    if target < 1 or target > 100:
        return False

    session["planner_target_attendance"] = target
    session.modified = True
    return True
```

A fresh portal attendance retrieval resets the planner target.

---

# 21. Sessional calendar logic

The checkpoint calculator has centralized calendar constants.

The important rule is that future checkpoint planning starts from today's scenario context.

For the active checkpoint:

- today's remaining classes are included;
- then future teaching days are counted;
- later checkpoints continue from the appropriate following day.

A key bug was fixed where today's remaining classes were not being included in the active checkpoint before maximum-safe-leave/recovery/requested projection calculations.

---

# 22. Main files and responsibilities

## `app.py`

Flask routes and session state orchestration.

It should NOT become the place for huge HTML blocks or duplicated calculation logic.

Relevant responsibilities:

- login/attendance retrieval;
- What-If route;
- scenario form routes;
- planner/session state;
- passing data into templates.

## `portal.py`

NIET Playwright integration and portal data retrieval.

Responsible for:

- login;
- aggregate attendance;
- course data;
- detailed subject attendance;
- today's portal-recorded classes;
- server-side portal/session cache.

## `attendance_state.py`

Central attendance-state model.

Responsible for the authoritative:

- Portal state;
- Site state;
- Effective state.

## `bunk_calculator.py`

Existing checkpoint/calendar calculation logic.

Use/reuse this math rather than duplicating it elsewhere.

## `scenario_engine.py`

Shared What-If scenario calculations.

Responsible for:

- effective starting state;
- today's event adjustment;
- scenario projections;
- reusable scenario math.

## `templates/dashboard.html`

Main shell:

- header;
- top navigation;
- page-level includes.

## `templates/what_if.html`

Unified What-If page.

Contains:

- scenario buttons;
- selected Today scenario setup/flow;
- selected Sessional scenario setup/flow;
- future scenario button slots.

## `templates/scenario_today.html`

Today scenario calculation UI.

## `templates/sessional_scenario.html`

Sessional checkpoint scenario UI.

It is embeddable inside What-If.

## `templates/checkpoint_tracker.html`

Reusable visual checkpoint tracker.

Do not move its CSS/giant markup into `app.py`.

## `static/style.css`

All styling.

The What-If scenario button styling belongs here.

---

# 23. Current What-If template structure

The selected scenario is controlled by:

```text
request.args.get("scenario")
```

Current links:

```text
/what-if?scenario=today
/what-if?scenario=sessional
```

The template concept is:

```jinja2
scenario buttons

if scenario == "today":
    Today setup
    → event question if needed
    → Today scenario

elif scenario == "sessional":
    Sessional setup
    → event question if needed
    → target question if needed
    → checkpoint scenario
```

Future scenarios should follow the same pattern.

---

# 24. Planner route status

The old:

```text
/planner
```

route used to be a visible Planner Setup page.

That UX is no longer wanted.

The intended behavior is that planner setup lives inside the selected What-If scenario.

The route can remain as a compatibility route if useful, but it should not be a visible alternative in the navigation.

Current cleanup direction:

```text
/planner
    ↓
/what-if
```

No visible Planner Setup navigation item.

---

# 25. Compatibility routes

Legacy routes may remain temporarily so old links do not break.

Current conceptual compatibility:

```text
/what-if/today → /what-if?scenario=today
/sessional     → /what-if?scenario=sessional
/planner       → /what-if
```

The canonical user-facing URLs are the What-If URLs.

---

# 26. Session reset behavior

When fresh attendance is retrieved:

```text
planner_loaded = False
planner_choice_made = False
planner_target_attendance = cleared
planner_event_checked = cleared
pending_event = cleared
today_scenario_result = cleared
selected checkpoint leaves = reset
```

This is intentional because a new portal snapshot represents a new planning session.

---

# 27. Important UX principle: no repeated questions

The user specifically wants:

> If today's event question is asked once and answered, that answer is reused by other scenarios.

So:

```text
Today scenario
   ↓
event answer saved
   ↓
Sessional scenario
   ↓
same event answer
```

No second event question should appear just because the user changed scenarios.

The same principle should be used for other truly shared planning inputs.

---

# 28. Current scenario sequence

### No scenario selected

```text
/what-if

Show:
- What-If intro
- Today button
- Sessional Checkpoints button
- future scenario buttons
```

### Today selected

```text
/what-if?scenario=today

If planner data not loaded:
    Start Today's Scenario

Else if event not answered:
    Ask event question

Else:
    Show Today calculator
```

### Sessional selected

```text
/what-if?scenario=sessional

If planner data not loaded:
    Start Sessional Scenario

Else if event not answered:
    Ask event question

Else if target not set:
    Ask minimum attendance once

Else:
    Show checkpoint flow
```

---

# 29. Future scenario roadmap

Planned scenarios:

1. **Today**
   - Attend/bunk today's remaining classes.

2. **Sessional Checkpoints**
   - Plan leave through First, Second and Third Sessional.

3. **Plan Until a Date**
   - Start from today;
   - apply today's event/remaining classes;
   - plan attendance through a selected date.

4. **Reach a Target**
   - User enters a target;
   - calculate classes needed to reach it.

5. **Safe Leaves**
   - Calculate how many classes can be left while maintaining a target.

A future:

> Can I reach X% by date?

can be composed from the shared date-plan + target logic instead of becoming another completely separate calculator.

---

# 30. Do not break these decisions

Before changing code, check this list.

### Attendance

- [ ] Effective = `(P + U) / (P + A + U)`
- [ ] Site = `P / (P + A + U)`
- [ ] Portal = `P / (P + A)`
- [ ] Future classes excluded from current attendance.

### What-If

- [ ] Every scenario starts from today/right now.
- [ ] What-If uses Effective Attendance.
- [ ] Event is planning input, not a separate scenario.
- [ ] Event answer is shared between scenarios.
- [ ] Scenario calculations do not modify real portal state.

### UI

- [ ] One top-level What-If page.
- [ ] Scenario buttons inside What-If.
- [ ] No visible Planner Setup navigation.
- [ ] Selected scenario stays selected.
- [ ] Future scenarios become additional buttons.

### Sessional

- [ ] One planner target for all checkpoints.
- [ ] Passed/current/upcoming tracker.
- [ ] Current checkpoint projection is forward-looking.
- [ ] Today's remaining classes are included in active checkpoint planning.

### Architecture

- [ ] Subject detail data has one shared cache.
- [ ] Subject Attendance does not depend on Planner being opened first.
- [ ] Portal failures do not silently create partial attendance.
- [ ] Keep calculation logic out of templates/app.py where possible.

---

# 31. Recent implementation history

Important commits from the What-If/cache work:

```text
440c25df43ef9d5c59c97df601a8751f908be574
Reuse cached subject attendance across planner and subjects

c1c518e6a72751121d4002ddccea99b3c262c923
Load subject history from shared cache on subjects page

b316d9812086cf226becea1315fc3b137b934db0
Document shared subject data cache architecture

b27e8ca102138b4d1ce213909e53ff3a8d7191f1
Include today's remaining classes in checkpoint projections

c3d5aeca16101e821690c621c45ed38f3d48fa64
Fix planner Jinja block closure

52d657345d2bcfb1ee82d0a65de8e1e7a74f81ce
Put What-If scenarios behind one page

d0cb06110975c647db21c1b2c453842b1fb1392f
Add unified What-If scenario page

9454d342e767b23679414957c2592e610426e839
Make sessional scenario embeddable in What-If page

3d5ffa812aa0e72fa3d9ddee0d95055ed6c03290
Use one unified What-If page for all scenarios

7cb67f68058eba6bd9f28c150dde924392331b2c
Keep Planner Setup inside What-If scenarios

8d02225dd0e255d6b0e4c5905f56305b0846440e
Use scenario buttons inside unified What-If page

94e282377368490a9dc3f434bb6001c2a6929dbe
Keep selected scenario active in What-If
```

Recent cleanup also moves planner compatibility behavior toward the unified What-If route and adds dedicated styling for the scenario buttons.

---

# 32. Known unrelated UI note

A recent live screenshot showed a possible separate issue:

- the page displayed **Second Sessional** while also showing a **First Sessional** card;
- the text suggested First Sessional had passed while its card remained visible.

This was not part of the What-If architecture fix and has not been treated as the same bug.

Investigate separately if the user asks.

---

# 33. Development style the user expects

The user wants a practical coding workflow:

- inspect first;
- understand why;
- change the smallest relevant files;
- keep architecture clean;
- do not blindly rewrite the project;
- do not create duplicate systems;
- do not put huge HTML/CSS into Python;
- commit changes;
- preserve `version-D`;
- explain what changed and why in simple language.

The user also wants this memory file continuously updated whenever an architectural decision changes.

---

# 34. Current immediate direction

The current product direction is:

```text
HOME
  ↓
WHAT-IF
  ↓
[ TODAY ] [ SESSIONAL CHECKPOINTS ] [ FUTURE... ]
  ↓
selected scenario
  ↓
its setup/questions/calculation
```

The old mental model:

```text
Planner Setup
   ↓
Sessional
   ↓
Today
```

is rejected.

The new mental model:

```text
What-If
   ├── Today
   ├── Sessional Checkpoints
   ├── Plan Until Date
   ├── Reach Target
   └── Safe Leaves
```

is the intended long-term structure.

---

## Last updated

**2026-09-18**

Continue from this file rather than reconstructing the project's decisions from scratch.
