# Bunku-Bhaiya — Working Context / Preservation File

> This file is the project's **behavior memory**. It is intentionally detailed so fast/vibe coding does not accidentally remove a small existing feature, calculation rule, route, selector, UI behavior, or bug fix.
>
> **Rule:** Before changing behavior, read this file. After changing behavior, update this file in the same work session.

---

# 0. CURRENT BASELINE

- Repository: `shutkarshX/Bunku-Bhaiya`
- Current working branch for the new work: `version-D`
- `version-D` was created directly from `main`.
- Baseline `main` commit when Version-D was created: `f0d4b6fdd1d7a3e53cebca15c7e4dae5ab8683aa`
- Main's latest commit message at the baseline: `Polish Bunku-Bhaiya README and fix Markdown rendering`
- Do not treat experimental branches as part of Version-D unless explicitly merged.

## Important existing branches / experiments

- `main` — OG/current checkpoint-planner baseline used to create Version-D.
- `version-D` — current clean working branch for the next evolution.
- `feature/today-remaining-classes` — later experiment; **not automatically part of Version-D**.
- `ui-changes` / `ui-tein-v1` — later UI/PWA development lines; **not automatically part of Version-D**.

---

# 1. WHAT THE CURRENT BASELINE DOES

The baseline is the original checkpoint-oriented BunkMaster flow:

```text
NIET portal login
    ↓
Retrieve real attendance
    ↓
Aggregate subject attendance
    ↓
Determine current/active sessional checkpoint
    ↓
Count future teaching classes until checkpoint
    ↓
Calculate maximum safe leave at 75%
    ↓
User chooses actual leave (days + classes)
    ↓
Calculate projected attendance at checkpoint
    ↓
Carry projected attendance into next checkpoint
    ↓
Repeat for next sessionals
```

The baseline is **not** the later date-range Attendance Planner, Scenario Lab, or the later "today remaining classes" UI unless explicitly added to Version-D.

---

# 2. ATTENDANCE TERMINOLOGY — DO NOT MIX THESE UP

## 2.1 Portal attendance

This is what the NIET portal currently reports through the attendance data retrieved by the scraper.

The portal aggregation is based on subject values:

- `attendedLecture`
- `absentLecture`

The basic portal total is:

```text
portal attended = sum(attendedLecture)
portal absent    = sum(absentLecture)
portal total     = portal attended + portal absent
```

Portal percentage:

```text
portal attended / portal total × 100
```

Example tested in the project:

```text
243 attended
20 absent
263 total
92.40%
```

## 2.2 Already-happened but unmarked attendance

The project has a separate concept for classes that have already happened but are not yet reflected in the portal attendance totals, where the system has determined those classes should count as attended.

These are **not future classes**.

They are **not today's remaining classes**.

They are treated as additional attended classes in the effective calculation.

## 2.3 Effective attendance

The effective calculation incorporates the already-happened confirmed/unmarked classes:

```text
effective_attended = portal_attended + unmarked_classes
effective_total    = portal_total + unmarked_classes
```

Therefore the effective percentage is calculated from those adjusted totals.

Example:

```text
Portal:
250 / 270

Already-happened confirmed/unmarked:
3 / 3

Effective:
253 / 273
```

This distinction is important because the user may see a different number on the college portal than the number used by the planner.

## 2.4 Future classes

Future classes are classes that have not happened yet and are expected from the academic calendar between the calculation start and checkpoint.

They are calculated separately from already-happened unmarked classes.

## 2.5 Later "today remaining classes" concept

A later development introduced a different concept: classes scheduled for **today** that have not yet been posted because they may still be in progress or have not yet happened/been marked.

That is distinct from the already-happened confirmed/unmarked attendance described above.

Do not silently merge these concepts.

---

# 3. COLLEGE ATTENDANCE IS NOT ALWAYS POSTED IMMEDIATELY

The college portal may post attendance later.

The existing project therefore has to distinguish:

```text
already posted by portal
+
already happened and confirmed/unmarked
+
future classes
```

The first two contribute to the known/effective starting attendance when the existing calculator has that metadata available.

Future classes are used for checkpoint projection.

Never assume that an unposted class is absent merely because it is absent from the current portal response.

Never assume a future class has already happened.

---

# 4. ACADEMIC CALENDAR

File:

```text
academic_calendar.py
```

Important constants:

```text
TEACHING_CLASSES_PER_DAY = 8
ATTENDANCE_TARGET = 75
```

The academic calendar uses an explicit list/set of teaching dates.

It is **not** safe to replace this with a simple Monday-Friday calculation.

Teaching dates include the configured sessional/exam dates where applicable.

Main helper:

```python
is_teaching_day(date_string)
```

The calculator relies on the explicit academic calendar to determine future teaching days.

---

# 5. CURRENT SESSIONAL CHECKPOINTS

Defined in the legacy checkpoint calculator:

```text
First Sessional   → 29 August 2026
Second Sessional  → 10 October 2026
Third Sessional   → 16 November 2026
```

The app also has the same date keys in its checkpoint-choice dictionary.

Date keys:

```text
2026-08-29
2026-10-10
2026-11-16
```

---

# 6. CHECKPOINT STATE RULES

For a checkpoint date:

```text
today < checkpoint
    → upcoming

today >= checkpoint
    → completed
```

The active checkpoint is the first checkpoint whose date is strictly after the current date.

Therefore:

```text
before First Sessional
    → First is active

First date passed, Second not passed
    → Second is active

Second date passed, Third not passed
    → Third is active

Third date passed
    → semester completed / no active checkpoint
```

The exact active index is derived from the ordered checkpoint list.

---

# 7. CRITICAL DATE CALCULATION RULE

For the active upcoming checkpoint, the original checkpoint calculator starts counting future classes from:

```text
TOMORROW
```

not from today.

Conceptually:

```text
current effective attendance
+
classes from tomorrow through checkpoint
-
selected leave
=
expected checkpoint attendance
```

This is the OG checkpoint behavior.

Do not change today's inclusion/exclusion accidentally while changing the UI.

---

# 8. CHECKPOINT DAY INCLUSION

For an upcoming checkpoint, the calculator checks whether the checkpoint date itself is a teaching day.

If it is a teaching day:

```text
checkpoint day is included
```

If it is not a teaching day:

```text
calculation ends on the previous day
```

Therefore future class count is based on actual teaching days, not raw calendar days.

---

# 9. SUBSEQUENT CHECKPOINT CALCULATION

For the checkpoint after the active one, the calculation starts from:

```text
previous checkpoint date + 1 day
```

and proceeds through the next checkpoint using the academic teaching calendar.

The projected result from the previous checkpoint becomes the starting attendance for the next checkpoint when a BunkMaster plan has been made.

---

# 10. WHAT HAPPENS WHEN A CHECKPOINT HAS PASSED

The system must not invent historical attendance.

If a checkpoint is already completed and there was no valid saved BunkMaster plan from before that checkpoint, the current portal attendance is used as the real known starting point for the next checkpoint.

UI meaning:

```text
First Sessional
✓ Completed
```

This does **not** mean:

```text
current portal percentage = historical First Sessional percentage
```

It means the date has passed and the application refuses to fabricate the old historical value.

---

# 11. IF A USER PLANNED BEFORE A CHECKPOINT

A valid pre-checkpoint plan can produce an expected checkpoint result.

That expected result can then be carried forward.

Example from the project documentation:

```text
Starting:
243 / 263 = 92.40%

Future classes:
8

Selected leave:
8 classes (1 day)

Projected:
243 / 271 = 89.67%
```

The `243 / 271` projection becomes the starting attendance for the next checkpoint if the plan is the applicable saved plan.

---

# 12. 75% ATTENDANCE TARGET

The required target is:

```text
75%
```

Safe means:

```text
percentage >= 75
```

Exactly 75% is safe.

The calculator must not use `> 75` where the project requirement is `>= 75`.

---

# 13. ATTENDANCE PERCENTAGE

General formula:

```text
attended / total × 100
```

The displayed overall percentage is rounded to two decimal places.

Zero-total handling returns 0 rather than dividing by zero.

---

# 14. CLASSES PER DAY

Configured teaching-day class count:

```text
8 classes/day
```

User leave is entered as:

```text
Days
Classes
```

Conversion:

```text
total leave classes = days × 8 + extra classes
```

Example:

```text
1 day + 3 classes
= 8 + 3
= 11 classes
```

The backend calculates in raw class counts.

The UI can turn a raw class count back into a day/class display.

---

# 15. LEAVE DISPLAY CONVERSION

The project has helper behavior for formatting a class count into days/classes.

Conceptually:

```text
classes // 8 → full days
classes % 8  → remaining classes
```

Do not remove this helper just because raw classes are easier internally; the UI uses the human-readable representation.

---

# 16. MAXIMUM SAFE LEAVE

The calculator determines the largest number of future classes that can be missed while remaining at or above 75% at the checkpoint.

For every possible missed count:

```text
future_attended = future_classes - missed_classes

projected_attended = current_attended + future_attended

projected_total = current_total + future_classes

projected_percentage =
    projected_attended / projected_total × 100
```

The largest missed count satisfying:

```text
projected_percentage >= 75
```

is maximum safe leave.

If the starting attendance is already below 75%:

```text
maximum safe leave = 0
```

---

# 17. USER-SELECTED LEAVE IS DIFFERENT FROM MAXIMUM SAFE LEAVE

Maximum safe leave is only a ceiling.

The user can select less.

Example:

```text
Maximum safe = 11 classes
User selects = 5 classes
```

The projection uses:

```text
5
```

not 11.

The backend caps requested leave so it cannot exceed:

- available future classes
- maximum safe leave

---

# 18. REQUESTED LEAVE PROJECTION

For an upcoming checkpoint:

```text
projected_attended =
    starting_attended
    + future_classes
    - requested_leave
```

```text
projected_total =
    starting_total
    + future_classes
```

```text
projected_percentage =
    projected_attended / projected_total × 100
```

The UI calls this the expected/projected attendance at the sessional.

It is not historical attendance.

---

# 19. RECOVERY STATUS

If current attendance is below 75%, the calculator determines how many consecutive attended classes are needed to reach 75%.

It solves:

```text
(attended + x) / (total + x) >= 0.75
```

The result is rounded upward to a whole class using ceiling behavior.

---

# 20. IMPOSSIBLE STATUS

If current attendance is below 75%, the calculator checks whether attending **every remaining future class** can recover attendance to 75%.

If:

```text
(attended + future_classes)
---------------------------- < 75%
(total + future_classes)
```

then status is:

```text
impossible
```

Otherwise, when currently below target, status is recovery.

If already at/above target, status is safe.

---

# 21. MAXIMUM POSSIBLE ATTENDANCE

The calculator exposes the maximum possible percentage assuming all future classes are attended.

This is used to distinguish recovery from impossible.

Do not confuse this with the user's chosen leave projection.

---

# 22. REMAINING SAFE LEAVE

After a user chooses leave, the calculator reports the remaining safe leave available relative to the maximum safe amount.

Example:

```text
maximum safe = 10
user selected = 4
remaining safe = 6
```

This is informational and does not automatically alter the user's selection.

---

# 23. CORE CALCULATOR FILES

## `legacy_bunk_calculator.py`

Contains the original checkpoint calculation primitives and flow.

Important functions/concepts:

```text
CHECKPOINTS
calculate_percentage()
classes_needed_to_reach_target()
days_and_classes_to_classes()
classes_to_leave_display()
count_teaching_days()
find_maximum_safe_leave()
calculate_requested_leave()
determine_status()
get_checkpoint_state()
get_active_checkpoint_index()
run_phase_1()
```

`run_phase_1()` is the central multi-checkpoint projection engine in the OG design.

## `bunk_calculator.py`

The application-facing calculator layer.

It imports/reuses the legacy calculator behavior and is the calculation module imported by `app.py`.

Important application-facing helpers include:

```text
run_phase_1
classes_to_leave_display
days_and_classes_to_classes
```

When changing this layer, preserve the legacy mathematical contract unless the change is explicitly intended.

---

# 24. `run_phase_1()` BEHAVIOR

The OG engine starts from attendance data.

It determines:

```text
current date
active checkpoint index
```

Then processes checkpoints in order.

For completed checkpoints:

- mark them completed
- do not fabricate historical future classes
- do not apply new future leave to a completed checkpoint
- use the known current/projected state as appropriate

For the first active upcoming checkpoint:

```text
calculation_start = today + 1 day
```

For later upcoming checkpoints:

```text
calculation_start = previous checkpoint date + 1 day
```

It counts teaching days, converts them to future classes, calculates status and safe leave, applies requested leave, and carries the projected result forward.

---

# 25. CHECKPOINT OUTPUT DATA

The calculator returns an overall structure containing current/projected state and a checkpoint list.

Important output concepts include:

```text
current_attended
current_total
current_percentage

active_checkpoint_index
active_checkpoint
semester_completed
today

checkpoints
```

Checkpoint-level output includes concepts such as:

```text
checkpoint
date
date_key
state
is_completed
is_active
is_upcoming

status

starting_attended
starting_total
starting_percentage

teaching_days
future_classes

maximum_leave
maximum_leave_classes
maximum_leave_days
maximum_leave_remaining_classes
maximum_leave_display

classes_needed_for_75
maximum_possible_percentage
projected_without_leave

requested_leave
requested_leave_classes
requested_leave_days
requested_leave_remaining_classes
requested_leave_display

requested_classes_missed
requested_projected_attended
requested_projected_total
requested_projected_percentage
requested_leave_is_safe

remaining_safe_leave
remaining_safe_leave_classes
remaining_safe_leave_days
remaining_safe_leave_remaining_classes
remaining_safe_leave_display

final_attended
final_total
final_percentage
classes_missed
```

If a UI component uses one of these fields, preserve its meaning before renaming/removing it.

---

# 26. PORTAL AUTOMATION

File:

```text
portal.py
```

The working baseline uses Playwright sync API.

Architecture:

```text
new sync_playwright instance
    ↓
launch headless Chromium
    ↓
new browser/page
    ↓
open NIET login page
    ↓
submit credentials
    ↓
open academic functions
    ↓
open courses
    ↓
open attendance
    ↓
capture attendance API response
    ↓
process attendance
    ↓
close browser
```

The baseline intentionally creates a fresh browser instance per attendance retrieval.

---

# 27. NIET PORTAL

Host:

```text
https://nietcloud.niet.co.in
```

Login page:

```text
/login.htm
```

Successful login destination is expected to match:

```text
**/home.htm
```

---

# 28. PORTAL SELECTORS

Current known selectors:

Username:

```text
#j_username
```

Password:

```text
#password-1
```

Login:

```text
button[type='submit']
```

Academic Functions:

```text
a[pid="20009"]
```

Courses:

```text
a[pid="24732"]
```

Attendance tab:

```text
button[data-tab="attendanceTab"]
```

These are fragile portal dependencies. Do not change casually.

---

# 29. CAPTURED NIET ATTENDANCE API

Important endpoint captured by the scraper:

```text
stu_getStudentBatchCourseAttendanceList.json
```

The portal flow also uses:

```text
stu_getStudentBatchCourseList.json
```

and subject-wise attendance retrieval:

```text
stu_getSubjectWiseStudentAttendance.json
```

The subject-wise data is used for additional attendance details/metadata in the working implementations.

---

# 30. PORTAL ERRORS

Two custom error concepts exist:

```text
PortalUnavailableError
PortalLoginError
```

## PortalUnavailableError

Used for problems such as:

- NIET unreachable
- browser startup failure
- page/navigation failure
- attendance data/API unavailable
- unexpected browser/session failure

## PortalLoginError

Used when the portal is reachable but credentials/login do not successfully reach the expected logged-in page.

The dashboard distinguishes login failure from portal unavailability.

---

# 31. IMPORTANT PLAYWRIGHT HISTORY

A persistent Playwright/browser experiment was attempted.

It caused:

```text
cannot switch to a different thread
(which happens to have exited)
```

Therefore the reliable baseline is a fresh Playwright/Chromium/page for each attendance retrieval.

Do not reintroduce a shared synchronous Playwright object casually.

---

# 32. ATTENDANCE RETRIEVAL AND AGGREGATION

File:

```text
app.py
```

The `/get-attendance` route:

1. Reads username.
2. Reads password.
3. Calls `get_attendance(username, password)`.
4. Handles portal/login errors.
5. Rejects empty attendance results.
6. Sums `attendedLecture` for every subject.
7. Sums `absentLecture` for every subject.
8. Calculates total classes.
9. Calculates overall percentage.
10. Saves attendance to Flask session.
11. Resets saved leave choices.
12. Runs `run_phase_1()`.
13. Renders the dashboard.

Invalid numeric subject values are handled defensively; values that cannot be converted to integers are ignored for that field rather than crashing the entire aggregation.

---

# 33. EMPTY ATTENDANCE STATE

`app.py` has an `empty_attendance()` helper returning:

```text
subjects: []
total_attended: 0
total_absent: 0
total_classes: 0
overall_percentage: 0
```

This is used when no attendance is available and when portal errors need to render the login/error state.

---

# 34. FLASK SECRET KEY

`app.py` requires:

```text
SECRET_KEY
```

from the environment.

If it is missing, the application raises a runtime error telling the operator to configure it.

Do not hard-code the secret key into the repository.

---

# 35. FLASK SESSION STATE

The app stores:

```text
attendance_data
selected_leaves
```

`attendance_data` contains the current retrieved attendance structure.

`selected_leaves` stores checkpoint-specific user choices.

Default leave map:

```text
2026-08-29 → 0
2026-10-10 → 0
2026-11-16 → 0
```

When new portal attendance is retrieved, the leave plan is reset to zero for all checkpoints.

This prevents a stale leave plan from being silently applied to fresh portal attendance.

---

# 36. AUTOMATIC DASHBOARD STEP

`get_dashboard_step()` uses `active_checkpoint_index`.

Mapping:

```text
None → step 4 / semester complete
0    → step 1 / First Sessional
1    → step 2 / Second Sessional
2    → step 3 / Third Sessional
```

The dashboard normally follows the current calendar checkpoint.

---

# 37. MANUAL CONTINUE STEP OVERRIDE

The sessional POST routes explicitly pass a calculator step when the user clicks Continue.

This exists because date-based automatic logic alone could otherwise send the user back to the current calendar checkpoint immediately after submitting a step.

Important behavior:

```text
POST /sessional-1
    → explicitly render step 2

POST /sessional-2
    → explicitly render step 3

POST /sessional-3
    → explicitly render final step
```

This is a UI-flow fix and should not be removed while refactoring dashboard rendering.

---

# 38. FORM INPUT NAMES

Leave input fields follow the pattern:

```text
leave_1_days
leave_1_classes

leave_2_days
leave_2_classes

leave_3_days
leave_3_classes
```

`get_requested_leave_classes(form, step)` reads the corresponding day/class fields and converts them to raw classes.

Non-numeric input is defensively treated as zero before conversion.

Do not rename these fields without updating the backend route parsing.

---

# 39. FLASK ROUTES

Current baseline routes:

```text
GET  /
POST /get-attendance
POST /sessional-1
POST /sessional-2
POST /sessional-3
GET  /reset
```

## `/`

Loads stored attendance if present.

If no subjects exist, renders the login/empty state.

If attendance exists, recalculates the current checkpoint state from today's date and saved leave choices.

## `/get-attendance`

Fresh portal retrieval and initial calculation.

## `/sessional-1`

Reads First Sessional leave, saves it under `2026-08-29`, recalculates, explicitly displays Step 2.

## `/sessional-2`

Reads Second Sessional leave, saves it under `2026-10-10`, recalculates, explicitly displays Step 3.

## `/sessional-3`

Reads Third Sessional leave, saves it under `2026-11-16`, recalculates, and displays the final state.

## `/reset`

Clears the Flask session.

---

# 40. SUBJECT DETAILS

The application can request subject-detail information from `portal.py`.

`render_dashboard()` augments the attendance data with subject details using the `_bunkmaster_subject_details_token` from the first subject when that token is available.

The subject detail template is:

```text
templates/_subject_attendance_details.html
```

Do not remove subject detail plumbing simply because the headline attendance cards do not need it.

---

# 41. CURRENT BASELINE UI

Main template:

```text
templates/dashboard.html
```

Main stylesheet:

```text
static/style.css
```

The UI is a server-rendered Flask/Jinja dashboard.

It contains the login state, attendance summary, checkpoint planner, leave inputs, projections, and final plan.

---

# 42. DASHBOARD — LOGIN STATE

When attendance is not yet available, the dashboard provides the portal login form.

The user supplies:

```text
username
password
```

The form posts to:

```text
/get-attendance
```

The page also has portal error states for login failure/unavailability.

---

# 43. DASHBOARD — CURRENT ATTENDANCE SUMMARY

The dashboard shows current attendance information including:

```text
Total Classes
Attended
Absent
Current Attendance
```

At the baseline, the primary displayed values are derived from the attendance data/calculator context.

Important future UI rule for Version-D:

If the displayed number is effective rather than raw portal attendance, the user should be able to see both:

```text
College portal currently shows: X / Y
Effective for planning: A / B
```

without changing the underlying calculation merely for display.

---

# 44. DASHBOARD — BUNK CALCULATOR

The main planner says conceptually:

> Plan your leave one checkpoint at a time. Your projected attendance after each checkpoint automatically becomes the starting attendance for the next one.

The active checkpoint is displayed as a step.

For the first checkpoint the UI includes:

- checkpoint name/date
- safe/recovery/impossible status
- starting attendance
- future classes
- maximum safe leave
- Days input
- Classes input
- live leave total
- projected attendance at checkpoint
- explanation that the projection becomes the starting attendance for the next checkpoint
- Continue button/form

Second and third steps continue the same carry-forward concept.

---

# 45. UI STATUS MEANINGS

## SAFE

Current starting attendance is already at/above 75%.

## RECOVERY

Starting attendance is below 75%, but attending all remaining future classes can recover to at least 75%.

## IMPOSSIBLE

Starting attendance is below 75%, and even perfect attendance across all remaining future classes cannot reach 75%.

Do not rename these statuses or change their conditions casually because both text and styling depend on them.

---

# 46. LIVE LEAVE UI

The Days + Classes inputs are intended to update the human-readable leave total on the page.

Example:

```text
Days = 1
Classes = 2

Your leave: 10 classes
```

This UI feedback should remain consistent with the backend conversion:

```text
1 × 8 + 2 = 10
```

The live UI is not a separate calculation model; it must agree with backend math.

---

# 47. PROJECTION VS CURRENT ATTENDANCE UI LANGUAGE

The page must keep these concepts visually/textually distinct:

```text
Current / portal / effective attendance
```

versus:

```text
Projected / expected attendance at checkpoint
```

A projection must never be presented as if it were a portal-recorded fact.

---

# 48. CSS BASELINE

File:

```text
static/style.css
```

The baseline uses a clean card-based dashboard.

Important existing responsive breakpoints include approximately:

```text
800px
500px
350px
```

The stylesheet contains responsive handling for the attendance summary, planner cards, attendance flow, safe leave, projections, carried-forward information, and final plan.

When redesigning for phone-first use, preserve the information hierarchy and calculation meaning even if the visual implementation changes completely.

---

# 49. SUBJECT DETAIL TEMPLATE

File:

```text
templates/_subject_attendance_details.html
```

This is a partial used for subject-level attendance details.

It should remain compatible with the subject details object supplied by the backend.

---

# 50. MANUAL PORTAL TEST

File:

```text
test_portal.py
```

This is a manual Playwright test used to log into the portal and inspect/capture the attendance API response.

Important captured response:

```text
stu_getStudentBatchCourseAttendanceList.json
```

The tested baseline showed 13 subjects in the documented example.

---

# 51. README / PROJECT DOCUMENTATION

`README.md` is public-facing project documentation.

`Mind.md` is the older backend master reference.

This file (`BUNKU_WORKING_CONTEXT.md`) is more detailed and is intended to be the **behavior-preservation memory** for future rapid development.

Do not treat README wording as the complete technical contract.

---

# 52. HISTORICAL FEATURE / CHANGE RECORD

This section records known development history so a future AI does not mistake an experiment for the current baseline.

## Original checkpoint planner

Status: **ACTIVE in main / Version-D baseline**

Behavior:

- current real attendance
- active sessional determined by date
- future classes from tomorrow for active checkpoint
- safe leave at 75%
- user-selected leave
- projection
- carry-forward to next checkpoint
- completed checkpoints do not get fabricated historical attendance

Reason it exists:

This is the original core BunkMaster product behavior.

---

## Subject-wise attendance / unmarked-class handling

Status: **PART OF THE WORKING ATTENDANCE MODEL WHERE PRESENT IN BASELINE CALCULATOR**

Behavior:

- subject-wise attendance can be retrieved
- attendance records/details can be inspected
- already-happened unmarked/confirmed classes can be incorporated into effective attendance
- those classes are not treated as future classes

Reason:

The college may post attendance later, so the planner can have a more accurate effective starting point than the raw portal snapshot alone.

---

## Persistent Playwright browser experiment

Status: **REVERTED / NOT BASELINE**

Problem:

```text
cannot switch to a different thread
(which happens to have exited)
```

Decision:

Use a fresh Playwright/Chromium/page for each attendance request.

Reason:

Reliability and thread safety.

---

## Later PWA / phone-first TEIN work

Status: **SEPARATE LATER DEVELOPMENT LINE — NOT PART OF VERSION-D BASELINE UNLESS EXPLICITLY PORTED**

Known work included:

- phone-first TEIN layer
- phone app manifest
- TEIN service worker
- TEIN app icon
- Render Playwright service configuration
- production Python dependencies

These changes belong to later UI/PWA development history and must not be assumed to exist in Version-D just because they existed on other branches.

---

## Later Scenario Planner / date-range planner

Status: **EXPERIMENTAL / LATER DEVELOPMENT — NOT AUTOMATICALLY PART OF VERSION-D**

There were later changes involving:

- `scenario_planner.py`
- `/scenario`
- `static/tein-scenario.js`
- `static/tein-scenario.css`
- attendance planner/date-range controls
- manual overrides
- event scenario mode

These were developed after the OG checkpoint baseline.

Do not copy them into Version-D implicitly.

---

## Scenario Lab detour

Status: **REVERTED**

The Scenario Lab approach was attempted and later reverted.

Reason for preserving this note:

A future vibe-coded change should not accidentally resurrect the discarded multi-option Scenario Lab flow.

---

## Event attendance scenario mode

Status: **LATER EXPERIMENT / DO NOT ASSUME IN VERSION-D**

The later branch experimented with event/auditorium classes where attendance may not yet have been posted.

The intended conceptual flow in that experiment was:

```text
remaining unrecorded classes
        ↓
were they an event?
        ↓
yes/no
        ↓
if event: how many were actually attended?
        ↓
remaining event classes can be planned as missed
```

This is historical context only until explicitly reintroduced.

---

# 53. LATER "TODAY REMAINING CLASSES" CONCEPT

Status: **LATER DEVELOPMENT, NOT IN OG MAIN BASELINE**

A later implementation introduced metadata such as:

```text
_bunkmaster_today_logged
_bunkmaster_remaining_today
_bunkmaster_unmarked_classes
_bunkmaster_subject_details_token
```

The later portal logic used an 8-class teaching day and could calculate remaining classes today.

Important conceptual distinction:

```text
already happened + confirmed but unmarked
    ≠
today's remaining classes
```

The OG Version-D starting point is the checkpoint planner that counts future classes from tomorrow.

If today's remaining behavior is later added, it must be explicitly designed so it does not overwrite the existing unmarked/effective model.

---

# 54. LATER UI BRANCHES

Known later branches included:

```text
ui-changes
ui-tein-v1
feature/today-remaining-classes
```

Known later commit themes included:

```text
phone-first TEIN layer
phone app manifest
TEIN service worker
TEIN app icon
Render Playwright service config
production Python dependencies
attendance planner
scenario planner
manual override
calendar/date planner
```

These are recorded to prevent accidental assumption that Version-D already contains them.

---

# 55. KNOWN UX ISSUE THAT VERSION-D IS INTENDED TO HANDLE

The baseline's main goal is correctness, but the user wants the site to become:

- easier to use
- faster to load
- lighter
- especially good on phone

The first concrete transparency improvement discussed for Version-D is:

```text
show what the college portal currently shows
AND
show what BunkMaster calls effective attendance
```

Example presentation:

```text
Effective attendance
253 / 273
93.04%

College portal currently shows
250 / 270
92.59%

Confirmed/unmarked
+3 / +3
```

This is a display clarification; it should not change the existing mathematical model unless explicitly requested.

---

# 56. PERFORMANCE-SENSITIVE AREAS

The portal retrieval is the expensive part because it involves:

- Playwright
- Chromium
- portal navigation
- network/API capture
- subject-wise retrieval/details where used

The pure attendance/checkpoint calculations are cheap Python operations.

Therefore a UI refactor should not accidentally trigger multiple portal retrievals for one page load.

The application should reuse the attendance already stored in session when it only needs to recalculate projections.

Fresh portal retrieval should happen when the user explicitly retrieves/refreshes attendance rather than every internal planner interaction.

---

# 57. IMPORTANT SESSION / REFRESH BEHAVIOR

`GET /` can recalculate checkpoint state from already-stored attendance and saved leave choices.

It does not inherently need to log into NIET again just to recalculate.

A fresh `/get-attendance` resets the leave plan.

This separation is important for both speed and correctness.

---

# 58. WHAT MUST NOT BE ACCIDENTALLY DELETED

When vibe coding, verify that the following still exist after any rewrite:

```text
Flask app creation
SECRET_KEY environment requirement
session attendance_data
session selected_leaves
empty_attendance()
get_user_attendance()
get_user_leaves()
save_user_leaves()
get_dashboard_step()
get_requested_leave_classes()
render_dashboard()
/
/get-attendance
/sessional-1
/sessional-2
/sessional-3
/reset

portal.get_attendance()
PortalUnavailableError
PortalLoginError

attendedLecture aggregation
absentLecture aggregation
overall percentage

run_phase_1()
75% target
8 classes/day
teaching-day calendar
checkpoint state
active checkpoint
completed checkpoint behavior
future class calculation
maximum safe leave
recovery
impossible
requested leave capping
projection
carry-forward

username selector
password selector
login selector
Academic Functions selector
Courses selector
Attendance tab selector
attendance API capture

subject details
attendance summary
leave days/classes inputs
live leave total
projection card
carry-forward explanation
final result
reset behavior
responsive CSS
```

---

# 59. REFACTORING SAFETY RULES

## Rule A — Preserve calculations first

A visual rewrite must not change:

```text
attendance math
checkpoint dates
teaching calendar
75% threshold
leave conversion
projection formula
carry-forward behavior
```

unless the change is explicitly agreed.

## Rule B — Preserve portal contracts

Do not casually change:

- selectors
- endpoint names
- login success detection
- Playwright lifecycle

## Rule C — Preserve state

Do not remove or rename session keys without tracing every route/template that uses them.

## Rule D — Preserve date semantics

The OG active checkpoint starts future counting from **tomorrow**.

Do not silently turn it into a today-inclusive planner.

## Rule E — Preserve completed-checkpoint honesty

Never reconstruct historical attendance from today's data unless the application has a valid saved projection from before that checkpoint.

## Rule F — Keep portal and effective values distinguishable

If the UI shows effective attendance, provide a clear way to understand that it may differ from the raw portal number.

---

# 60. EVERY FUTURE CHANGE SHOULD BE LOGGED HERE

For every change made after this file was created, append an entry containing:

```text
Date:
Version-D commit:
What changed:
Files changed:
Exact old behavior:
Exact new behavior:
Why it changed:
Calculation impact:
UI impact:
Portal impact:
State/session impact:
Reversible/reverted?:
```

If a change is later reverted, keep the original entry and mark it:

```text
Status: REVERTED
Reason:
Reverted by commit:
```

Do not erase historical entries merely because the code was reverted.

---

# 61. VERSION-D CHANGE LOG

## 2026-09-12 — Version-D created

Status: **ACTIVE BASELINE**

Branch:

```text
version-D
```

Base:

```text
main @ f0d4b6fdd1d7a3e53cebca15c7e4dae5ab8683aa
```

Purpose of this entry:

Create a clean branch from the OG main checkpoint implementation before further product changes.

No application behavior was changed by branch creation.

---

## 2026-09-12 — Working context file created

File:

```text
BUNKU_WORKING_CONTEXT.md
```

Purpose:

Preserve detailed application behavior and development history so rapid/vibe coding does not accidentally overwrite small existing features or calculations.

No application calculation behavior is changed by this documentation file.

---

# 62. QUICK REFERENCE — CURRENT OG MODEL

```text
PORTAL
  ↓
subject attendance
  ↓
portal attended + portal absent
  ↓
known/confirmed unmarked already-happened classes may be added
  ↓
EFFECTIVE STARTING ATTENDANCE
  ↓
active sessional checkpoint
  ↓
future teaching days
  ↓
future classes (OG: starts tomorrow)
  ↓
maximum safe leave at >=75%
  ↓
user chooses actual leave
  ↓
projected checkpoint attendance
  ↓
carry projection to next checkpoint
```

The most important conceptual split is:

```text
PORTAL MARKED
    = what college has posted

CONFIRMED UNMARKED / ALREADY HAPPENED
    = included in effective attendance when available

FUTURE
    = classes that have not happened yet
```

And the most important OG checkpoint rule is:

```text
ACTIVE CHECKPOINT
    → future counting begins TOMORROW
```

---

# 63. DO NOT ASSUME

Do not assume any of the following without checking the actual Version-D code:

- today's remaining classes are already included
- the newer TEIN UI exists
- the Scenario Planner exists
- event mode exists
- the PWA/service worker exists
- later branch CSS exists
- later date-range planner exists
- portal data is refreshed on every page load
- a portal-visible percentage is identical to effective percentage
- an unmarked class is absent
- a completed checkpoint's historical attendance can be reconstructed

This section exists specifically to stop context drift during vibe coding.
