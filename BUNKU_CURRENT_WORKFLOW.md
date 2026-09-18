# Bunku-Bhaiya — CURRENT VERSION-D WORKFLOW MEMORY

> This is the current handoff / workflow brain for Version-D.
> Read it before continuing development.
> If an older historical note conflicts with this file, this file contains the latest product decisions as of 2026-09-18.

## 1. PROJECT / WORKFLOW

- Repository: shutkarshX/Bunku-Bhaiya
- Active branch: version-D
- main must remain untouched for this work.
- Local path: C:\Users\Roger\Desktop\Bunk Clean\Bunku-Bhaiya
- User does not normally use .venv. Do not include activation commands in normal run instructions.

Normal run:

    cd "C:\Users\Roger\Desktop\Bunk Clean\Bunku-Bhaiya"
    git switch version-D
    git pull origin version-D
    python app.py

Working rule:
1. Read this file before changing behavior.
2. Inspect actual current code.
3. Preserve existing behavior unless the user explicitly changes the decision.
4. Keep logic/templates/CSS separated.
5. Update this file after meaningful behavior or architecture changes.
6. Commit Version-D changes.
7. Never silently change formulas or UX architecture.

---

## 2. FINAL TOP-LEVEL UX

The authenticated product has exactly three top-level destinations:

    Home | What-If | Subject Attendance

There must NOT be a visible Planner Setup navigation item.

The intended structure is:

    Home
    |
    +-- What-If
    |     |
    |     +-- [ Today ]
    |     +-- [ Sessional Checkpoints ]
    |     +-- [ future scenario buttons ]
    |
    +-- Subject Attendance

What-If is one page/hub. Scenarios are selected inside it.

Today:
    /what-if?scenario=today

Sessional:
    /what-if?scenario=sessional

Only the selected scenario is displayed. Do not stack every scenario vertically.

Future scenarios get more buttons inside the same What-If page.

---

## 3. WHY WHAT-IF IS ONE PAGE

Earlier designs incorrectly separated Planner Setup, Today, and Sessional.

The final decision is:

    What-If
       ↓
    choose a scenario
       ↓
    that scenario contains its own required setup
       ↓
    scenario result

Planner loading, today's event question, and target selection are setup steps inside the selected scenario. They are not separate user-facing destinations.

The backend may retain compatibility routes temporarily, but they must not create a competing Planner Setup UX.

---

## 4. CURRENT SCREEN BEHAVIOR

What-If default:

    What-If

    Choose what you want to simulate.
    Your real portal attendance is never changed by these scenarios.

    [ Scenario 1
      Today
      Attend or bunk today's remaining classes ]

    [ Scenario 2
      Sessional Checkpoints
      Plan attendance through First, Second and Third Sessional ]

The screenshot from 2026-09-18 had the correct structure but scenario links appeared as plain blue browser links. That was styling, not a product-flow decision. Scenario buttons now have dedicated CSS classes.

---

## 5. ATTENDANCE MODEL — AUTHORITATIVE

Use:

    P = Present
    A = Absent
    U = Unmarked / Freeze

Formulas:

    TOTAL = P + A + U

    PORTAL ATTENDANCE = P / (P + A)

    SITE ATTENDANCE = P / TOTAL

    EFFECTIVE ATTENDANCE = (P + U) / TOTAL

Equivalent:

    Portal = P / (P + A)
    Site = P / (P + A + U)
    Effective = (P + U) / (P + A + U)

Critical:
- Site numerator is P, NOT P+U.
- Effective numerator is P+U.
- Future classes are excluded from current/site/effective totals.
- U classes already happened but are not yet posted.
- U classes are not future classes.
- U classes count in Site denominator.
- U classes count as present for Effective.

Test:

    P=254, A=88, U=4
    Portal   = 254/342 = 74.27%
    Site     = 254/346 = 73.41%
    Effective= 258/346 = 74.57%

Latest live test:

    Present=284
    U=1
    Total=374
    Site=284/374=75.94%
    Effective=285/374=76.20%

These formulas are locked unless the user explicitly changes them.

---

## 6. RIGHT-NOW MODEL

Every What-If scenario starts from RIGHT NOW.

It does not start from raw portal attendance and does not start from a future checkpoint.

Concept:

    RIGHT NOW
       ↓
    Current Effective State
       +
    Today's event information when needed
       ↓
    Effective Starting State
       ↓
    scenario_engine.py
       ↓
    selected scenario
       ↓
    projection

This is the central What-If architecture.

---

## 7. EVENT RULE — VERY IMPORTANT

The event is NOT a separate scenario.

It is information used to establish the shared planning starting state.

The user explicitly wants the event question asked when needed, but once answered, the answer is reused by other scenarios.

Example:

    User opens Today
       ↓
    event question
       ↓
    user answers
       ↓
    answer stored

Then:

    User opens Sessional
       ↓
    DO NOT ask event again
       ↓
    reuse same event state

Do not create one event answer per scenario.

---

## 8. TODAY EVENT CALCULATION

If today's pending event covers N currently unposted classes:

If attended:

    planning attended += N
    planning total += N

If not attended:

    planning attended += 0
    planning total += N

In both cases:

    today's remaining ordinary classes -= N

The event-covered classes are removed from today's ordinary remaining window.

The actual portal/effective attendance state is never mutated.

---

## 9. SCENARIO ENGINE

File:

    scenario_engine.py

Purpose:
- centralize What-If math
- avoid building unrelated calculators
- reuse attendance_state.py and existing calculator math

Current foundation:

    get_effective_starting_state(...)
    calculate_today_scenario(...)

get_effective_starting_state:
- builds normalized effective state
- reads today's remaining classes
- applies today's pending event if applicable
- returns a common starting state

Returned concepts:

    attended
    total
    percentage
    today_remaining
    event_classes
    event_attended

---

## 10. TODAY SCENARIO

Question:

    If I attend X classes and leave Y classes today,
    what will my effective attendance be?

Inputs:
- attended
- leave/bunk

Validation:

    attended >= 0
    leave >= 0
    attended + leave <= today_remaining

Projection:

    projected_attended =
        starting_attended + attended

    projected_total =
        starting_total + attended + leave

    projected_percentage =
        projected_attended / projected_total * 100

Also show:
- starting effective attendance
- today's remaining classes
- event note if relevant
- planned classes
- classes remaining after plan
- Right now → After today

Files:

    templates/scenario_today.html
    scenario_engine.py

Today does NOT require the sessional target.

---

## 11. SESSIONAL CHECKPOINT SCENARIO

Scenario name:

    Sessional Checkpoints

Selected through:

    /what-if?scenario=sessional

Template:

    templates/sessional_scenario.html

This contains the full checkpoint planning flow and checkpoint tracker.

It is NOT a separate top-level page.

---

## 12. SESSIONALS

Current dates:

    First Sessional   = 29 August 2026
    Second Sessional  = 10 October 2026
    Third Sessional   = 16 November 2026

Date keys:

    2026-08-29
    2026-10-10
    2026-11-16

On 2026-09-18 the tracker should conceptually show:

    ✓ First Sessional
      Passed

    ● Second Sessional
      Current

    ○ Third Sessional
      Upcoming

A passed checkpoint does not automatically get a historical attendance percentage.

---

## 13. NO FABRICATED HISTORICAL CHECKPOINT ATTENDANCE

If First Sessional has passed and there is no valid saved historical plan/result:

    First Sessional
    Passed

Do NOT infer an old percentage from today's attendance.

Passed/current/upcoming is a date/state concept, not permission to invent history.

---

## 14. CURRENT CHECKPOINT PROJECTION

After a user chooses leave for the current checkpoint, tracker can show:

    Second Sessional
    Current

    Your checkpoint attendance
    75.39%

    X / Y classes

    This becomes the starting attendance for the next sessional.

This is a forward projection, not historical attendance.

Flow:

    current effective state
       ↓
    user planned leave
       ↓
    projected current checkpoint
       ↓
    starting state for next checkpoint

---

## 15. ONE PLANNER-LEVEL TARGET

The user chooses ONE minimum attendance requirement for the planner session.

Storage:

    planner_target_attendance

Example:

    user chooses 80%

    First Sessional  → 80%
    Second Sessional → 80%
    Third Sessional  → 80%

Do NOT reintroduce checkpoint-specific targets.

Bad design:

    checkpoint_targets = {
        first: 75,
        second: 80,
        third: 70
    }

The target is asked once:

    What minimum attendance percentage do you need?

Not:

    What minimum attendance percentage do you need for this checkpoint?

Validation:

    integer
    1 <= target <= 100

Fresh /get-attendance clears the target.

---

## 16. SESSIONAL FLOW

Selected Sessional scenario:

    click Sessional Checkpoints
       ↓
    load today's planner data if needed
       ↓
    ask today's event if unresolved
       ↓
    ask one planner-level target if unresolved
       ↓
    checkpoint planning
       ↓
    user chooses leave
       ↓
    current checkpoint projection
       ↓
    next checkpoint
       ↓
    final result

All of this happens inside the selected What-If scenario.

---

## 17. TODAY REMAINING CLASSES

Planner's detailed scan determines today's logged classes and remaining classes.

Rule:

    8 classes/day

If today is a teaching day:

    remaining_today = max(0, 8 - today_logged)

If today is not a teaching day:

    remaining_today = 0

The detailed scan respects:

    noOfConsicativeLectur

It gathers subject-wise attendance records and counts today's actual logged sessions.

Failures should raise PortalUnavailableError rather than return partial counts.

---

## 18. CHECKPOINT DATE CALCULATION

Original/OG checkpoint rule:

For the active upcoming checkpoint, future teaching classes traditionally start from tomorrow because today's remainder is handled explicitly in Version-D.

Version-D correction:

Today's remaining classes are explicitly added to the active checkpoint horizon before:
- maximum safe leave
- maximum possible attendance
- recovery/safe calculation
- requested projection

Later checkpoints start from:

    previous checkpoint date + 1 day

Teaching days must come from the explicit academic calendar, not generic weekdays.

---

## 19. CHECKPOINT MATH

General:

    percentage = attended / total * 100

Safe condition:

    projected percentage >= target

Exactly the target is safe.

Maximum safe leave:
- largest missed count that still satisfies target
- if already below target, safe leave is normally 0

Recovery:
- solve the number of consecutive attended classes needed to reach target
- round upward to a whole class

Impossible:
- if attending every remaining future class still cannot reach target

Maximum possible:
- attendance assuming all remaining future classes are attended

User-selected leave is separate from maximum safe leave.

Example:

    maximum safe = 11
    user chooses = 5

Projection uses 5, not 11.

---

## 20. LEAVE INPUT

Teaching day:

    8 classes

Conversion:

    total leave classes = days * 8 + extra classes

Example:

    1 day + 3 classes = 11 classes

Backend should calculate in raw class counts. UI may display days + remaining classes.

---

## 21. SUBJECT ATTENDANCE SHARED CACHE

Problem found:

Subject Attendance showed summary rows, but detailed subject history did not expand until Planner had been opened.

Cause:
- detailed subject data was lazy
- Planner was accidentally acting as the initializer
- Subject Attendance only read the cache

Fix:

Both use:

    load_subject_details(token)

Architecture:

    Attendance Planner
        ↓
    load_subject_details(token)
        ↓
    SUBJECT_DETAILS_CACHE[token]

    Subject Attendance
        ↓
    load_subject_details(token)
        ↓
    SUBJECT_DETAILS_CACHE[token]

First feature fetches.
Later feature reuses.

Therefore either navigation order works.

---

## 22. SUBJECT DATA IS NOT THE SAME AS ATTENDANCE STATE

Attendance model:

    attendance_state.py
        ↓
    P / A / U
        ↓
    portal/site/effective

Detailed history:

    portal.py
        ↓
    token/cache
        ↓
    Planner + Subject Attendance

Do not replace one with the other.

---

## 23. PORTAL SESSION CACHE

portal.py currently has concepts:

    _SUBJECT_DETAILS_CACHE
    _PORTAL_SESSION_CACHE

Initial login:
- retrieves aggregate attendance
- retrieves course data
- captures authenticated storage state
- stores server-side token/session
- does not need to perform the expensive detailed subject scan immediately

Deferred loading:
- uses saved authenticated storage state
- fetches details
- caches them

The cache is in memory.
It is not persistent.
Do not assume it survives server restart.

---

## 24. PORTAL

Host:

    https://nietcloud.niet.co.in

Login:

    /login.htm

Important APIs:

    stu_getStudentBatchCourseAttendanceList.json
    stu_getStudentBatchCourseList.json
    stu_getSubjectWiseStudentAttendance.json

Known selectors:

    #j_username
    #password-1
    button[type='submit']
    a[pid="20009"]
    a[pid="24732"]
    button[data-tab="attendanceTab"]

Do not casually change fragile portal selectors.

---

## 25. PLAYWRIGHT THREAD RULE

A persistent synchronous Playwright object previously caused:

    cannot switch to a different thread
    (which happens to have exited)

Reliable design:
- fresh Playwright/browser/context when needed
- saved storage state for deferred authenticated operations
- no casual global shared sync Playwright object

---

## 26. ERROR HANDLING

Custom errors:

    PortalUnavailableError
    PortalLoginError

PortalUnavailableError:
- portal unreachable
- navigation failure
- browser/session failure
- attendance API failure
- deferred detailed scan failure

PortalLoginError:
- portal reachable but login did not successfully reach authenticated state

Do not silently return fake or partial attendance after a portal failure.

---

## 27. FILE RESPONSIBILITIES

    app.py
        Flask routes
        session state
        template data preparation

    portal.py
        NIET login
        Playwright
        portal APIs
        storage-state/session cache
        subject detail cache

    attendance_state.py
        P/A/U normalization
        portal/site/effective formulas

    academic_calendar.py
        teaching dates
        calendar constants

    bunk_calculator.py
        checkpoint math
        safe leave
        recovery
        projections
        run_phase_1

    scenario_engine.py
        What-If calculations
        shared RIGHT-NOW state
        Today scenario
        future scenario foundation

    templates/dashboard.html
        global shell
        navigation
        page routing/includes

    templates/what_if.html
        What-If hub
        scenario buttons
        selected scenario flow

    templates/scenario_today.html
        Today scenario UI

    templates/sessional_scenario.html
        Sessional scenario UI

    templates/checkpoint_tracker.html
        tracker UI

    static/style.css
        all styling

Keep this separation.

---

## 28. ROUTES

Main:

    /                       → Home
    /what-if                → What-If hub
    /what-if?scenario=today
                            → Today selected
    /what-if?scenario=sessional
                            → Sessional selected
    /subjects               → Subject Attendance

Data/planning:

    /get-attendance
    /load-planner
    /event
    /planner-target
    /scenario/today

Checkpoint submissions:

    /sessional-1
    /sessional-2
    /sessional-3

Compatibility:

    /planner
    /what-if/today
    /sessional

Compatibility routes must not restore separate top-level UX.

---

## 29. REDIRECT RULE

Scenario flows must preserve the selected scenario.

Today:

    /what-if?scenario=today

Sessional:

    /what-if?scenario=sessional

Avoid fallback redirects to a visible Planner Setup page.

If a generic planner compatibility redirect is needed:

    /what-if

---

## 30. FRESH LOGIN RESET

/get-attendance resets:

    selected_leaves
    planner_loaded
    planner_choice_made
    planner_target_attendance
    planner_event_checked
    pending_event
    today_scenario_result

Reason:
new portal snapshot = new planning context.

---

## 31. REAL VS PLANNING DATA

REAL:

    Portal P
    Portal A
    U
    Site attendance
    Effective attendance

PLANNING:

    today's event
    today's remaining classes
    selected leave
    planner target
    scenario inputs

RESULT:

    projected attended
    projected total
    projected percentage

Never mutate REAL state from a scenario.

---

## 32. CSS / UI RULES

What-If button classes:

    .what-if-scenario-buttons
    .what-if-scenario-button
    .what-if-scenario-button.active

Scenario buttons should look like proper cards/buttons, not default hyperlinks.

What-If page uses:

    .what-if-page
    .what-if-scenario-box
    .what-if-scenario-heading

Mobile:
- scenario buttons become one column
- no horizontal overflow
- sessional tracker moves into normal page flow

---

## 33. KNOWN UI ISSUE TO INVESTIGATE LATER

A screenshot showed a possible inconsistency:

    Second Sessional
    First Sessional has already passed

while a First Sessional card was still visible.

Do not change the checkpoint calculation just from this visual symptom.

When fixing it, inspect:
- checkpoint state
- phase_1 result
- tracker data
- card rendering
- current selected scenario

---

## 34. IMPORTANT HISTORY

Shared subject cache:

    440c25df43ef9d5c59c97df601a8751f908be574
    Reuse cached subject attendance across planner and subjects

    c1c518e6a72751121d4002ddccea99b3c262c923
    Load subject history from shared cache on subjects page

    b316d9812086cf226becea1315fc3b137b934db0
    Document shared subject data cache architecture

Unified What-If transition:

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

Jinja fix:

    c3d5aeca16101e821690c621c45ed38f3d48fa64
    Fix planner Jinja block closure

---

## 35. DO NOT BREAK THESE

Never accidentally:
- change Site numerator from P to P+U
- change Effective away from (P+U)/(P+A+U)
- include future classes in current attendance
- treat U as absent
- ask today's event again after it is already answered
- make Event a separate scenario
- make Planner Setup top-level
- make Sessional top-level navigation
- fabricate historical checkpoint attendance
- create checkpoint-specific targets
- make Subject Attendance depend on Planner being opened
- duplicate detailed subject portal requests unnecessarily
- put tracker HTML/CSS into app.py
- reintroduce unsafe shared sync Playwright
- silently swallow portal failures
- mutate real attendance during What-If

---

## 36. FUTURE SCENARIOS

Planned:

1. Today
2. Plan Until a Date
3. Reach a Target
4. Safe Leaves

Future date planning must start from RIGHT NOW:

    current effective state
       +
    today's event
       +
    today's remaining classes
       +
    future teaching classes through selected date

Do not start from tomorrow while silently discarding today's remainder.

All future scenario math should go through scenario_engine.py where possible.

---

## 37. CURRENT ARCHITECTURAL GOAL

One real attendance state.
Many temporary simulations.

Concept:

    REAL PORTAL DATA
          ↓
    P / A / U normalization
          ↓
    EFFECTIVE RIGHT NOW
          ↓
    shared planning context
          ↓
    What-If scenario selection
          ↓
    temporary hypothetical calculation
          ↓
    projection

Not:

    many unrelated calculators
    each with separate state/setup/event logic

---

## 38. HANDOFF TO A NEW CHAT

If continuing this project in a new conversation:

1. Read BUNKU_CURRENT_WORKFLOW.md.
2. Read BUNKU_WORKING_CONTEXT.md for older history when needed.
3. Work only on version-D.
4. Inspect current files before editing.
5. Do not invent a new architecture.
6. Continue from the latest locked decisions in this file.
7. After a meaningful change, append a dated section to this file explaining:
   - what changed
   - why
   - exact behavior
   - files changed
   - routes/state affected
   - calculation impact
   - UI impact
   - whether reversible/reverted

The purpose is that the next chat can continue with the same workflow without needing the previous conversation.

---

## 39. LAST KNOWN STATE

Date: 2026-09-18

Current top-level nav:

    Home | What-If | Subject Attendance

Current What-If architecture:

    What-If
       ↓
    scenario buttons
       ↓
    selected scenario
       ↓
    setup inside scenario
       ↓
    result

Current shared event rule:

    answer once → reuse across scenarios

Current target rule:

    one planner-level target → all sessional checkpoints

Current attendance rule:

    Portal  = P/(P+A)
    Site    = P/(P+A+U)
    Effective = (P+U)/(P+A+U)

Current planning rule:

    every scenario starts from RIGHT NOW

Current subject-data rule:

    first feature loads details → shared cache → other feature reuses

Last updated:

    2026-09-18
