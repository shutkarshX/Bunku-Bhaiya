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


---

# 35. Detailed continuity log — why we changed the architecture

This section exists so a future conversation can understand not only **what** the code does, but **why** we arrived here.

## 35.1 Original planner idea

The first planner implementation treated the Attendance Planner as a separate destination.

Conceptually it was:

```text
Home
  ↓
Attendance Planner
  ↓
load today's detailed portal data
  ↓
event question
  ↓
target attendance
  ↓
sessional checkpoint calculations
```

This worked technically, but it mixed several different ideas:

- today's What-If;
- event adjustment;
- checkpoint planning;
- target selection;
- planner setup.

The user later clarified that these are not separate products.

The actual product concept is **What-If**.

Therefore planner setup should be an internal step of whichever What-If scenario needs it.

---

## 35.2 Why the old Planner Setup navigation was rejected

The UI previously exposed something equivalent to:

```text
Home | Planner Setup | What-If: Today | What-If: Sessional | Subject Attendance
```

This was rejected because the user does not want users thinking:

> "First I go to Planner Setup, then I go somewhere else to run a scenario."

The intended mental model is:

```text
Home | What-If | Subject Attendance
             ↓
       choose a scenario
             ↓
       scenario handles
       its own setup
```

So **Planner Setup is implementation detail, not a product-level navigation item**.

The planner route may remain temporarily for backwards compatibility, but it must not be presented as a normal feature.

---

## 35.3 Why What-If became one page

There was an intermediate design where Today and Sessional were separate What-If pages/tabs.

That was also corrected.

The desired structure is:

```text
What-If
│
├── [ Today ]
├── [ Sessional Checkpoints ]
├── [ future scenario ]
└── [ future scenario ]
```

Clicking a button changes the selected scenario on the same canonical page:

```text
/what-if?scenario=today
/what-if?scenario=sessional
```

The page should show only the selected scenario's body.

This makes adding a future scenario predictable:

1. Add one scenario button.
2. Add one conditional scenario block.
3. Reuse the shared scenario engine/state.
4. Do not add another top-level navigation page.

---

## 35.4 Why scenario buttons are actual UI controls, not plain links

The first version of the unified page rendered the scenario choices as ordinary HTML links.

That produced the browser-default appearance visible in the screenshot:

```text
Scenario 1 Today Attend or bunk today's remaining classes
Scenario 2 Sessional Checkpoints Plan attendance...
```

They appeared blue and underlined.

That is technically functional but visually communicates "raw links", not "scenario choices".

The intended UI is therefore card/button-like controls with:

- clear scenario number;
- scenario name;
- short description;
- spacing;
- hover state;
- selected/active state;
- responsive layout.

The styling belongs in `static/style.css`, not inline HTML.

---

## 35.5 Why the event question is shared

The user explicitly identified an important behavior:

> If today's event question is answered once, the same answer must be reused by other scenarios.

This means the event answer is **shared planning context**, not scenario-specific input.

Correct:

```text
Today scenario
    ↓
event answer saved
    ↓
Sessional scenario
    ↓
reuse same event answer
```

Incorrect:

```text
Today scenario → ask event
Sessional scenario → ask event again
Future scenario → ask event again
```

The backend therefore stores one `pending_event` in the current session.

The event contains:

```python
{
    "date": "YYYY-MM-DD",
    "classes": N,
    "attended": True_or_False,
}
```

The scenario engine reads that shared value.

---

## 35.6 Why the event does not modify actual attendance

The event is only a planning assumption because the portal has not necessarily posted those classes yet.

Therefore:

```text
REAL PORTAL STATE
        ≠
PLANNING STATE
```

The event must never be written into the actual P/A/U portal state.

Instead, the scenario starting point temporarily applies it:

```text
Effective starting attended
    = effective attended + event attended

Effective starting total
    = effective total + event classes
```

And ordinary remaining classes for today are reduced by the event-covered classes.

This lets every scenario start from the same "today/right now" reality without corrupting the actual attendance snapshot.

---

## 35.7 Why every scenario starts from Right Now

A previous interpretation treated events as something that only belonged to one special scenario.

That was corrected.

The actual rule is:

> Every What-If scenario starts from today/right now.

Therefore the scenario engine conceptually does:

```text
Current Effective State
        +
Today's planning context
        ↓
Effective Starting State
        ↓
chosen scenario
```

For a future date scenario, it would therefore be:

```text
Right Now
  ↓
apply today's event
  ↓
apply today's remaining classes
  ↓
future teaching days
  ↓
requested date
```

This is why a shared starting-state function is more important than building isolated calculators.

---

## 35.8 Why subject attendance needed a shared cache

A real bug exposed an architecture problem.

Observed behavior:

```text
Login
  ↓
Open Subject Attendance
  ↓
subject details do not fully expand
```

but:

```text
Login
  ↓
Open Attendance Planner
  ↓
open Subject Attendance
  ↓
details work
```

That meant Planner was accidentally initializing data required by Subject Attendance.

The fix was not to make Subject Attendance call Planner.

Instead both features call the same data-layer function:

```text
load_subject_details(token)
```

with a server-side cache:

```text
                 ┌── Planner
                 │
load_subject_details
                 │
                 └── Subject Attendance
                         ↓
                    same cache
```

The first consumer loads the data.

Later consumers reuse it.

This is an architectural fix rather than a UI workaround.

---

## 35.9 Why detailed portal loading is lazy

The initial login only needs aggregate attendance to render Home.

Fetching every subject's complete attendance history through Playwright is more expensive.

Therefore the initial flow stores:

- aggregate attendance;
- course data;
- authenticated Playwright storage state;
- a short-lived server-side token.

Detailed subject history is loaded only when a feature actually needs it.

This gives:

```text
Initial login
    ↓
fast aggregate snapshot
    ↓
Home can render

Detailed feature
    ↓
load_subject_details(token)
    ↓
fetch once
    ↓
cache
```

This also lets Today/Sessional/Subject Attendance share the same detailed data instead of each starting another expensive scan.

---

## 35.10 Why the attendance formulas were explicitly locked

Several attendance interpretations were considered during development.

The final model is intentionally explicit:

```text
P = portal-present
A = portal-absent
U = already-held but unposted
```

Then:

```text
Portal    = P / (P + A)
Site      = P / (P + A + U)
Effective = (P + U) / (P + A + U)
```

The distinction matters because the site and effective percentages answer different questions.

The Site figure treats unmarked classes as classes in the denominator but does not call them present.

The Effective figure treats those same unmarked classes as effectively attended for planning.

Future classes are not part of any of these current attendance percentages.

---

## 35.11 Why What-If uses Effective Attendance

What-If is a planning tool.

If an already-held class has not yet appeared in the portal, the planner should not pretend that the user has no attendance information for it.

That is why the scenario starting point is the Effective state.

Then today's event/remaining-class context can be layered on top temporarily.

The actual portal/site/effective dashboard values remain unchanged.

---

## 35.12 Why the Sessional target is one value

The target originally risked becoming checkpoint-specific.

That was explicitly rejected.

The user wants:

```text
One planning target
        ↓
First Sessional
Second Sessional
Third Sessional
```

For example, if the user enters 75:

```text
First  → 75%
Second → 75%
Third  → 75%
```

If the user enters 80:

```text
First  → 80%
Second → 80%
Third → 80%
```

Therefore the state is:

```python
planner_target_attendance = 75
```

not a dictionary of checkpoint targets.

This is important for both UI and calculator design.

---

## 35.13 Why today's remaining classes had to be added to the active checkpoint

A checkpoint projection represents what can happen from **today forward**.

Therefore, when the current checkpoint is still ahead, today's remaining classes are part of the available planning window.

The active checkpoint calculation was corrected so that:

```text
today remaining
+
future teaching-day classes
```

is considered before calculating:

- maximum safe leave;
- maximum possible leave;
- recovery;
- requested projection.

Without this, the active checkpoint could undercount the actual number of classes available from right now.

---

# 36. Exact state machine for the current What-If UI

This is the intended behavior to preserve.

## State A — What-If selector

URL:

```text
/what-if
```

Show:

- What-If introduction;
- Today button;
- Sessional Checkpoints button;
- future scenario buttons.

Do not show Planner Setup as a separate page.

---

## State B — Today selected, planner data not loaded

URL:

```text
/what-if?scenario=today
```

Show:

```text
Today
↓
Ready to calculate
↓
Start Today's Scenario
```

Submitting starts the deferred portal/detail loading.

---

## State C — Today selected, event not answered

Show the event question inside the Today scenario.

If the user says no event:

```text
planner_event_checked = True
pending_event = None
```

If the user saves an event:

```text
planner_event_checked = True
pending_event = saved event
```

Then return to:

```text
/what-if?scenario=today
```

---

## State D — Today scenario ready

Show the Today calculator:

```text
Right now
↓
Attend X
Bunk Y
↓
After today
```

No portal data is modified.

---

## State E — Sessional selected, planner data not loaded

URL:

```text
/what-if?scenario=sessional
```

Show:

```text
Sessional Checkpoints
↓
Ready to calculate
↓
Start Sessional Scenario
```

---

## State F — Sessional selected, event not answered

Show the shared event question.

The wording explains that the answer is shared with checkpoint planning.

After answering, return to:

```text
/what-if?scenario=sessional
```

---

## State G — Sessional selected, target not set

Show one target question:

> What minimum attendance percentage do you need?

The value applies to all checkpoints.

After saving, return to the same selected scenario.

---

## State H — Sessional scenario ready

Show the checkpoint flow/tracker.

The tracker identifies:

```text
Passed
Current
Upcoming
```

The current checkpoint can show its forward projection after a leave choice.

---

# 37. Current backend state keys

The important Flask session values are:

```text
attendance_data
selected_leaves
planner_loaded
planner_choice_made
planner_target_attendance
planner_event_checked
pending_event
today_scenario_result
```

Meaning:

### `attendance_data`

Current portal aggregate snapshot plus subject records/token.

### `selected_leaves`

Temporary user planning choices for checkpoint calculations.

### `planner_loaded`

Whether today's deferred planning data has been loaded.

### `planner_choice_made`

Whether checkpoint planning has started/made a choice.

### `planner_target_attendance`

One shared target for all checkpoints.

### `planner_event_checked`

Whether the user has answered today's event question.

### `pending_event`

Today's planning-only event adjustment.

### `today_scenario_result`

Latest Today What-If projection.

All of these are planning/session state, not a replacement for portal truth.

---

# 38. Route responsibilities — current canonical model

## `/`

Home.

Only the current attendance snapshot and normal dashboard information should be presented here.

## `/what-if`

Canonical What-If page.

The `scenario` query parameter selects the internal scenario.

## `/subjects`

Canonical Subject Attendance page.

Uses shared subject detail cache.

## `/get-attendance`

Fresh portal retrieval.

Resets planning state because a new portal snapshot starts a new planning session.

## `/load-planner`

Deferred loading action.

It prepares today's planning data and returns to the scenario that requested it.

It is an internal action, not a top-level product page.

## `/event`

Saves today's shared event decision.

It returns to the scenario supplied by `return_to`.

## `/planner-target`

Saves the single shared planner target.

It returns to the selected scenario.

## `/scenario/today`

Processes Today What-If input.

The UI entry point is inside What-If; this route is the calculation endpoint.

## `/sessional-1`, `/sessional-2`, `/sessional-3`

Process checkpoint submissions.

They are internal form endpoints for the Sessional scenario.

## Compatibility routes

```text
/planner
/what-if/today
/sessional
```

may remain temporarily so old links do not break, but they should redirect toward the canonical What-If page rather than becoming separate user-facing experiences.

---

# 39. What changed in the latest cleanup

The latest cleanup is specifically about making the product match the final UX decision.

### Navigation

Changed from exposing Planner Setup to:

```text
Home | What-If | Subject Attendance
```

### What-If

Scenario selection is now inside one page.

### Scenario selection

Uses:

```text
/what-if?scenario=today
/what-if?scenario=sessional
```

### Scenario styling

Dedicated CSS classes were added for the scenario cards/buttons.

### Planner

Planner setup is treated as an internal compatibility flow rather than a top-level destination.

### Redirects

Scenario actions should return to the selected What-If scenario rather than unexpectedly dropping the user into an old Planner Setup page.

---

# 40. Current screenshot diagnosis

The supplied screenshot showed the correct high-level navigation:

```text
Home
What-If
Subject Attendance
```

and the correct What-If concept:

```text
Scenario 1 Today
Scenario 2 Sessional Checkpoints
```

The problem visible in the screenshot was presentation:

- scenario choices were plain underlined blue links;
- they were not visually separated into cards/buttons;
- both descriptions ran together horizontally;
- there was excessive empty space after the links.

The intended CSS solution is to turn the two choices into a responsive grid of scenario cards.

Desktop:

```text
┌─────────────────────────┐  ┌─────────────────────────────┐
│ SCENARIO 1              │  │ SCENARIO 2                  │
│ Today                   │  │ Sessional Checkpoints       │
│ Attend or bunk...       │  │ Plan through checkpoints... │
└─────────────────────────┘  └─────────────────────────────┘
```

Mobile:

```text
┌─────────────────────────────┐
│ SCENARIO 1                  │
│ Today                       │
│ Attend or bunk...           │
└─────────────────────────────┘

┌─────────────────────────────┐
│ SCENARIO 2                  │
│ Sessional Checkpoints       │
│ Plan through checkpoints... │
└─────────────────────────────┘
```

The active scenario uses the dark BunkMaster treatment.

---

# 41. Future development workflow

When adding another What-If scenario, follow this order:

### Step 1 — Define the user question

Example:

> "How much attendance will I have by 15 October?"

Do not start by copying another calculator.

### Step 2 — Identify shared starting state

Use the same:

```text
get_effective_starting_state(...)
```

or extend `scenario_engine.py`.

### Step 3 — Define only the scenario-specific inputs

Do not ask for information already known from:

- current portal state;
- shared event decision;
- shared planner target;
- existing scenario state.

### Step 4 — Put math in `scenario_engine.py`

Do not put calculation formulas directly in Jinja.

### Step 5 — Put the UI in its own template

For example:

```text
templates/scenario_date_plan.html
```

### Step 6 — Add one button to `what_if.html`

Do not add another top-level navigation item.

### Step 7 — Add styling to `static/style.css`

Keep visual logic out of Python.

### Step 8 — Preserve URL model

Use:

```text
/what-if?scenario=<scenario-name>
```

### Step 9 — Test switching scenarios

Especially verify:

- event answer is reused;
- no repeated setup appears unnecessarily;
- actual attendance remains unchanged;
- selected scenario remains selected.

### Step 10 — Update this file

Document:

- what changed;
- why it changed;
- which state is shared;
- which route/template owns it;
- any rejected alternative.

---

# 42. Testing checklist for every future change

## Attendance correctness

- [ ] Portal percentage uses P/(P+A).
- [ ] Site percentage uses P/(P+A+U).
- [ ] Effective percentage uses (P+U)/(P+A+U).
- [ ] Future classes are excluded from current attendance.

## What-If correctness

- [ ] Starts from Effective attendance.
- [ ] Starts from today/right now.
- [ ] Applies today's event only as planning state.
- [ ] Applies event exactly once.
- [ ] Reduces today's ordinary remaining classes by event-covered classes.
- [ ] Does not mutate portal attendance.
- [ ] Switching scenarios does not ask the same event question again.

## Sessional correctness

- [ ] One target applies to all checkpoints.
- [ ] Current checkpoint includes today's remaining classes.
- [ ] Passed checkpoint does not invent historical attendance.
- [ ] Current projection is explicitly forward-looking.

## UI correctness

- [ ] Only Home / What-If / Subject Attendance are top-level.
- [ ] What-If contains scenario buttons.
- [ ] No visible Planner Setup navigation.
- [ ] Only selected scenario content is shown.
- [ ] Scenario button remains visibly active.
- [ ] Mobile layout remains usable.

## Architecture correctness

- [ ] Shared subject cache remains shared.
- [ ] Subject Attendance does not depend on Planner initialization.
- [ ] Scenario math remains centralized.
- [ ] app.py remains orchestration-focused.
- [ ] No giant HTML/CSS blocks are moved into Python.
- [ ] Portal errors are not silently converted into partial data.

---

# 43. Decision history — rejected designs

These are important because future development may otherwise accidentally reintroduce them.

### Rejected: Planner Setup as top-level navigation

Reason:

It exposes an implementation/setup concept instead of the actual What-If product.

### Rejected: Today and Sessional as separate top-level pages

Reason:

The user wants one What-If hub with scenario buttons.

### Rejected: All scenario calculators stacked vertically

Reason:

The user wants to choose one scenario and see that scenario's flow, not a giant page containing every calculator.

### Rejected: Event as a separate scenario

Reason:

The event is shared context used to establish today's planning starting point.

### Rejected: Re-asking the event question per scenario

Reason:

The user answered it once; it should be reused.

### Rejected: Per-checkpoint attendance targets

Reason:

The target is one shared planner-level requirement.

### Rejected: Making Subject Attendance depend on Planner

Reason:

Features should initialize their own shared data dependency through the common cache.

### Rejected: Duplicating scenario formulas

Reason:

Multiple calculators would drift and produce inconsistent attendance logic.

---

# 44. Continuation instruction for the next conversation

If a future conversation begins with something like:

> "continue BunkMaster"

the correct starting procedure is:

1. Read `BUNKMASTER_PROJECT_MEMORY.md` from `version-D`.
2. Confirm the current branch is `version-D`.
3. Inspect the relevant files before editing.
4. Treat the decisions in this file as authoritative until the user explicitly changes them.
5. Do not recreate old Planner Setup UX.
6. Do not ask the user to explain the attendance formulas again.
7. Do not reintroduce separate Today/Sessional top-level pages.
8. Do not make the user repeat today's event information across scenarios.
9. Make the smallest clean change required.
10. Update this memory file when the architecture or behavior changes.
11. Commit the implementation and memory update on `version-D`.

The purpose of this document is to make a new conversation behave like a continuation of the same development session rather than starting the project from zero.

---

# 45. Current implementation snapshot

At the time of this update:

```text
Branch:
version-D

Canonical navigation:
Home | What-If | Subject Attendance

Canonical What-If:
 /what-if

Scenario selectors:
 /what-if?scenario=today
 /what-if?scenario=sessional

Shared scenario starting state:
 scenario_engine.py

Shared subject-detail cache:
 portal.py

Attendance model:
 attendance_state.py

Checkpoint math:
 bunk_calculator.py

What-If UI:
 templates/what_if.html

Today UI:
 templates/scenario_today.html

Sessional UI:
 templates/sessional_scenario.html

Checkpoint tracker:
 templates/checkpoint_tracker.html

Styling:
 static/style.css
```

The next changes should build on this architecture rather than replacing it.

