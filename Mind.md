# BunkMaster — Backend Master Reference

**Purpose:** This is the single source-of-truth context file for the current working BunkMaster backend. Give this file to another AI before making backend changes so the project architecture, calculations, routes, checkpoint behavior, and known decisions are not reconstructed from scratch.

**Last captured:** 26 August 2026  
**Current tested portal result:** 13 subjects, 243 / 263, 92.40%  
**Current portal architecture:** fresh headless Chromium per attendance request.  
**Important:** The persistent Playwright browser experiment is NOT part of the working baseline. It caused `cannot switch to a different thread (which happens to have exited)`.

---

# 1. PROJECT PURPOSE

BunkMaster retrieves the user's real attendance from the NIET college portal and calculates how much leave/bunk they can safely take before each sessional checkpoint while maintaining at least **75% attendance**.

The intended flow is:

```text
NIET Portal
    ↓
Real current attendance
    ↓
Current date determines active checkpoint
    ↓
Count teaching days/classes until checkpoint
    ↓
Calculate maximum safe leave
    ↓
User chooses actual leave
    ↓
Calculate expected attendance at checkpoint
    ↓
Carry that expected attendance to next checkpoint
    ↓
Final projected attendance
```

---

# 2. BACKEND FILES

```text
app.py
    Flask routes, user session, portal retrieval, form handling.

bunk_calculator.py
    All attendance/sessionals calculations and checkpoint/date logic.

portal.py
    Playwright automation for NIET login and attendance API capture.

academic_calendar.py
    Academic calendar dependency:
      - TEACHING_CLASSES_PER_DAY
      - ATTENDANCE_TARGET
      - is_teaching_day(date_string)

templates/dashboard.html
    UI only. It consumes the data produced by app.py + bunk_calculator.py.

static/style.css
    UI styling only.
```

---

# 3. CHECKPOINTS

Current checkpoints:

```text
First Sessional   → 29 August 2026
Second Sessional  → 10 October 2026
Third Sessional   → 16 November 2026
```

The calculator uses the actual current system date.

Rule:

```text
today < checkpoint date
    → checkpoint is upcoming/active

today >= checkpoint date
    → checkpoint is completed
```

Once all three dates have passed:

```text
semester_completed = True
active_checkpoint = None
```

---

# 4. CRITICAL DATE BEHAVIOR

This is an important project decision.

## Before a checkpoint

BunkMaster calculates:

```text
current portal attendance
+
future teaching classes
-
user's selected leave
=
expected attendance at checkpoint
```

That expected checkpoint attendance can become the starting attendance for the next checkpoint.

## After a checkpoint has passed

BunkMaster must NOT invent the user's historical attendance at that checkpoint.

If the user did not use BunkMaster before the checkpoint:

```text
First Sessional
✅ Completed

Current portal attendance
        ↓
Second Sessional starting attendance
```

The current portal attendance is the real known value.

The UI should therefore say:

```text
First Sessional
✅ Completed
```

rather than pretending that the current portal percentage was the percentage on the old checkpoint date.

## If the user DID make a plan before the checkpoint

Then the expected checkpoint result is valid:

```text
User selects 1 day leave

243 / 263
+
8 future classes
-
8 leave
=
243 / 271

= 89.67%
```

That expected First Sessional attendance becomes the starting point for Second Sessional.

---

# 5. 75% TARGET

The backend uses:

```text
TARGET_ATTENDANCE = ATTENDANCE_TARGET
```

The project requirement is:

```text
75%
```

Safe means:

```text
attendance >= 75%
```

Not strictly greater than 75%.

---

# 6. CLASS/DAY CONVERSION

The academic calendar supplies:

```text
TEACHING_CLASSES_PER_DAY
```

The current project assumes the configured number of classes per teaching day.

User input:

```text
Days
Classes
```

is converted to raw classes:

```text
total classes =
    days × CLASSES_PER_DAY
    + extra classes
```

Example:

```text
1 day + 3 classes
=
8 + 3
=
11 classes
```

All calculations are performed internally in raw classes.

The UI can convert raw classes back into:

```text
X day(s) Y class(es)
```

---

# 7. MAXIMUM SAFE LEAVE

For a current attendance:

```text
attended / total
```

and:

```text
future_classes
```

BunkMaster tests possible missed classes.

For each possible leave:

```text
future_attended =
    future_classes - missed_classes

final_attended =
    attended + future_attended

final_total =
    total + future_classes

percentage =
    final_attended / final_total × 100
```

The largest missed-class count for which:

```text
percentage >= 75%
```

is the maximum safe leave.

If the current attendance is already below 75%:

```text
maximum safe leave = 0
```

---

# 8. RECOVERY MODE

If current attendance is below 75%, the calculator determines how many consecutive attended classes are needed to reach 75%.

The formula solves:

```text
(attended + x)
---------------- >= 0.75
(total + x)
```

and uses `ceil()` so the result is a whole number of classes.

---

# 9. IMPOSSIBLE MODE

If current attendance is below 75%, BunkMaster also checks:

```text
attend every remaining future class
```

If even then:

```text
maximum possible percentage < 75%
```

the status is:

```text
impossible
```

Otherwise it is:

```text
recovery
```

If already at/above 75%:

```text
safe
```

---

# 10. USER'S ACTUAL LEAVE

The maximum safe leave is NOT automatically the user's choice.

The user can choose a smaller amount.

The backend:

1. Converts Days + Classes into raw classes.
2. Prevents the requested leave from exceeding future classes.
3. Prevents the requested leave from exceeding maximum safe leave.
4. Calculates the resulting projected attendance.

Therefore:

```text
maximum safe leave = 11 classes

user chooses = 5 classes

calculation uses = 5 classes
```

not 11.

---

# 11. PROJECTED CHECKPOINT ATTENDANCE

For an upcoming checkpoint:

```text
projected_attended =
    starting_attended
    + future_classes
    - requested_leave
```

and:

```text
projected_total =
    starting_total
    + future_classes
```

Then:

```text
projected_percentage =
    projected_attended / projected_total × 100
```

This is the number shown as:

> Your attendance at [Sessional] will be...

when the checkpoint is upcoming.

---

# 12. CHECKPOINT CARRY-FORWARD

When the user chooses leave before an upcoming checkpoint:

```text
First expected attendance
        ↓
Second starting attendance

Second expected attendance
        ↓
Third starting attendance
```

This is the core BunkMaster feature.

But once a checkpoint is already past, the old plan must NOT be reapplied to current portal attendance.

---

# 13. PORTAL FLOW

`portal.py` currently uses:

```text
sync_playwright()
    ↓
launch headless Chromium
    ↓
new page
    ↓
open NIET login
    ↓
fill username/password
    ↓
wait for /home.htm
    ↓
Academic Functions
    ↓
Courses
    ↓
Attendance
    ↓
capture attendance API response
```

The captured API:

```text
stu_getStudentBatchCourseAttendanceList.json
```

contains subject-wise attendance.

The working test captured:

```text
13 subjects
```

---

# 14. PORTAL SELECTORS CURRENTLY USED

Login username:

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

Attendance:

```text
button[data-tab="attendanceTab"]
```

Successful login URL:

```text
**/home.htm
```

NIET host:

```text
https://nietcloud.niet.co.in
```

---

# 15. PORTAL ERROR TYPES

Two custom errors exist:

```python
PortalUnavailableError
PortalLoginError
```

### PortalUnavailableError

Used when:

- NIET cannot be reached
- browser cannot start
- page cannot be opened
- portal navigation fails
- attendance API gives no data
- browser/session fails unexpectedly

### PortalLoginError

Used when:

- NIET is reachable
- but login does not successfully reach `/home.htm`

The dashboard distinguishes these cases.

---

# 16. IMPORTANT PLAYWRIGHT DECISION

A persistent Chromium/browser was attempted.

It produced:

```text
cannot switch to a different thread
(which happens to have exited)
```

Therefore the current reliable baseline is:

```text
new Playwright instance
new Chromium
new page
retrieve attendance
close browser
```

Do NOT replace this with a shared synchronous Playwright object unless the architecture is redesigned to be thread-safe.

---

# 17. ATTENDANCE AGGREGATION

`app.py` receives the subject list.

For every subject:

```text
attendedLecture
absentLecture
```

are summed.

Then:

```text
total_classes =
    total_attended + total_absent
```

and:

```text
overall_percentage =
    total_attended / total_classes × 100
```

Example tested result:

```text
Attended = 243
Absent   = 20
Total    = 263

243 / 263 × 100
=
92.40%
```

---

# 18. USER SESSION STORAGE

Flask session stores:

```text
attendance_data
selected_leaves
```

`attendance_data` contains:

```text
subjects
total_attended
total_absent
total_classes
overall_percentage
```

`selected_leaves` stores checkpoint-specific leave choices.

Current checkpoint keys:

```text
2026-08-29
2026-10-10
2026-11-16
```

The session is reset when new attendance is retrieved.

---

# 19. FLASK ROUTES

Current routes:

```text
GET  /
POST /get-attendance

POST /sessional-1
POST /sessional-2
POST /sessional-3

GET  /reset
```

### `/`

Shows the initial dashboard/login state.

### `/get-attendance`

1. Reads username/password.
2. Calls `portal.get_attendance()`.
3. Aggregates subject attendance.
4. Saves attendance to session.
5. Resets leave choices.
6. Runs the calculator.
7. Shows Step 1.

### `/sessional-1`

1. Reads First Sessional leave.
2. Saves it.
3. Recalculates.
4. Shows Step 2.

### `/sessional-2`

1. Reads Second Sessional leave.
2. Saves it.
3. Recalculates.
4. Shows Step 3.

### `/sessional-3`

1. Reads Third Sessional leave.
2. Saves it.
3. Recalculates.
4. Shows Step 4/final result.

### `/reset`

Clears the Flask session.

---

# 20. CALCULATOR OUTPUT CONTRACT

`run_phase_1()` returns:

```text
current_attended
current_total
current_percentage

active_checkpoint_index
active_checkpoint
semester_completed
today

checkpoints[]
```

Each checkpoint result contains information such as:

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

---

# 21. ACTIVE CHECKPOINT

The backend checks checkpoints in order.

If today is:

```text
before 29 Aug
```

active:

```text
First Sessional
```

If today is:

```text
29 Aug through before 10 Oct
```

active:

```text
Second Sessional
```

If today is:

```text
10 Oct through before 16 Nov
```

active:

```text
Third Sessional
```

If today is:

```text
16 Nov or later
```

semester:

```text
completed
```

---

# 22. TEACHING-DAY CALCULATION

The calculator does not simply count calendar days.

It calls:

```python
is_teaching_day(date_string)
```

from `academic_calendar.py`.

The checkpoint itself is included only when the academic calendar says it is a teaching day.

Therefore:

```text
future classes =
teaching days × classes per teaching day
```

---

# 23. IMPORTANT UI MEANING

These terms must not be mixed up.

### Current Attendance

Real attendance retrieved from the college portal.

Example:

```text
243 / 263 — 92.40%
```

### Expected Attendance at Sessional

A projection based on the user's selected leave.

Example:

```text
1 day leave

243 / 271 — 89.67%
```

This means:

> This is what your attendance will be at the First Sessional.

It is NOT historical attendance.

### Completed Sessional

If the checkpoint date has passed and no BunkMaster plan was recorded:

```text
First Sessional
✅ Completed
```

Then current portal attendance is used for the next calculation.

---

# 24. CURRENT WORKING EXAMPLE

Known test:

```text
Portal:
243 / 263
92.40%
```

First Sessional:

```text
8 future classes
1 teaching day
```

If user selects:

```text
1 day
```

and 1 day equals 8 classes:

```text
243 + (8 - 8)
----------------
263 + 8

= 243 / 271
= 89.67%
```

That is the expected First Sessional attendance.

Then Second Sessional starts from:

```text
243 / 271
89.67%
```

when the user actually made that First Sessional plan before the checkpoint.

---

# 25. DATE-PASSED EXAMPLE

If the First Sessional date has already passed and the user did not make a BunkMaster plan:

```text
First Sessional
✅ Completed
```

BunkMaster should NOT say:

```text
First Sessional = current portal percentage
```

Instead:

```text
First Sessional
✅ Completed

Current portal attendance
243 / 263 — 92.40%

↓

Second Sessional
Starting attendance
243 / 263 — 92.40%
```

This is intentional.

---

# 26. CURRENT RELIABILITY BASELINE

The current known working behavior has been tested with:

```text
13 subjects
243 / 263
92.4%
```

The Flask app successfully reaches:

```text
First Sessional
        ↓
Second Sessional
        ↓
Third Sessional
        ↓
Final result
```

The portal retrieval is working with the fresh-browser Playwright implementation.

---

# 27. KNOWN PERFORMANCE LIMITATION

The portal retrieval currently takes roughly:

```text
~20–25 seconds
```

in the tested environment.

This is because every retrieval launches a fresh browser.

This is accepted for the current reliable baseline.

Do not sacrifice reliability just to optimize this number.

---

# 28. SECURITY NOTES

The Flask app expects:

```text
SECRET_KEY
```

from an environment variable.

Do not hard-code the secret key into the repository.

User college credentials are passed to the portal retrieval process and should not be stored permanently.

---

# 29. DEVELOPMENT COMMANDS

Syntax check:

```powershell
python -m py_compile app.py
python -m py_compile bunk_calculator.py
python -m py_compile portal.py
```

Run:

```powershell
python app.py
```

Git status:

```powershell
git status
```

Commit:

```powershell
git add app.py bunk_calculator.py portal.py templates/dashboard.html
git commit -m "Update BunkMaster"
git push origin main
```

---

# 30. BEFORE MODIFYING BACKEND

Always preserve these invariants:

1. Portal attendance is the real starting attendance.
2. 75% is the safety threshold.
3. Future classes come from teaching days, not arbitrary calendar days.
4. User leave is a choice, not automatically maximum safe leave.
5. Expected checkpoint attendance can be carried forward.
6. Passed checkpoints must not receive newly invented historical attendance.
7. Current portal attendance is used when a checkpoint has already passed and no BunkMaster historical plan exists.
8. Do not reintroduce the thread-unsafe persistent Playwright browser.
9. Do not change working portal selectors without testing the real NIET portal.
10. Do not change calculator math just to fix a UI wording problem.

---

# 31. CURRENT FILE SNAPSHOTS

The exact working source snapshots captured with this reference are included below.



# ============================================================
# CURRENT APP.PY SNAPSHOT
# ============================================================

```python
import os
from flask import Flask, render_template, request, session

from portal import (
    get_attendance,
    PortalUnavailableError,
    PortalLoginError
)

from bunk_calculator import run_phase_1, classes_to_leave_display, days_and_classes_to_classes


app = Flask(__name__)

# Required for Flask sessions.
# Change this to a long random value before deploying publicly.
SECRET_KEY = os.environ.get("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set. "
        "Please configure it before running BunkMaster."
    )

app.secret_key = SECRET_KEY

# Make the leave formatter available directly inside Jinja templates.
app.jinja_env.globals["classes_to_leave_display"] = classes_to_leave_display


# =========================================
# DEFAULT CHECKPOINT SETTINGS
# =========================================

CHECKPOINT_CHOICES = {
    "2026-10-10": True,
    "2026-11-16": True
}


# =========================================
# HELPER - EMPTY ATTENDANCE
# =========================================

def empty_attendance():

    return {
        "subjects": [],
        "total_attended": 0,
        "total_absent": 0,
        "total_classes": 0,
        "overall_percentage": 0
    }


# =========================================
# HELPER - GET USER ATTENDANCE
# =========================================

def get_user_attendance():

    return session.get(
        "attendance_data",
        empty_attendance()
    )


# =========================================
# HELPER - GET USER LEAVE PLAN
# =========================================

def get_user_leaves():

    return session.get(
        "selected_leaves",
        {
            "2026-08-29": 0,
            "2026-10-10": 0,
            "2026-11-16": 0
        }
    )


# =========================================
# HELPER - SAVE USER LEAVE PLAN
# =========================================

def save_user_leaves(leaves):

    session["selected_leaves"] = leaves

    session.modified = True


# =========================================
# HELPER - PARSE DAYS + CLASSES LEAVE INPUT
# =========================================

def get_requested_leave_classes(form, step):
    """
    Read the two user-facing fields and convert them into
    one raw class count. The calculator uses raw classes
    internally, so values such as 1 day + 10 classes become
    18 classes automatically.
    """
    days_raw = form.get(
        f"leave_{step}_days",
        0
    )

    classes_raw = form.get(
        f"leave_{step}_classes",
        0
    )

    try:
        days = int(days_raw)
    except (TypeError, ValueError):
        days = 0

    try:
        classes = int(classes_raw)
    except (TypeError, ValueError):
        classes = 0

    return days_and_classes_to_classes(
        days,
        classes
    )


# =========================================
# HOME
# =========================================

@app.route("/")
def dashboard():

    attendance_data = get_user_attendance()

    return render_template(

        "dashboard.html",

        attendance=attendance_data,

        phase_1=None,

        calculator_step=0,

        portal_error=None
    )


# =========================================
# GET ATTENDANCE
# =========================================

@app.route(
    "/get-attendance",
    methods=["POST"]
)
def get_attendance_page():

    username = request.form.get(
        "username"
    )

    password = request.form.get(
        "password"
    )


    print()
    print(
        "Starting attendance retrieval..."
    )


    # =====================================
    # GET ATTENDANCE
    # =====================================

    try:

        subjects = get_attendance(
            username,
            password
        )


    except PortalUnavailableError as e:

        print()
        print(
            "======================================"
        )
        print(
            "NIET PORTAL UNAVAILABLE"
        )
        print(
            "======================================"
        )

        print(e)
        print()


        return render_template(

            "dashboard.html",

            attendance=empty_attendance(),

            phase_1=None,

            calculator_step=0,

            portal_error="unavailable"
        )


    except PortalLoginError as e:

        print()
        print(
            "======================================"
        )
        print(
            "NIET LOGIN FAILED"
        )
        print(
            "======================================"
        )

        print(e)
        print()


        return render_template(

            "dashboard.html",

            attendance=empty_attendance(),

            phase_1=None,

            calculator_step=0,

            portal_error="login"
        )


    except Exception as e:

        print()
        print(
            "Unexpected portal error:"
        )

        print(e)
        print()


        return render_template(

            "dashboard.html",

            attendance=empty_attendance(),

            phase_1=None,

            calculator_step=0,

            portal_error="unavailable"
        )


    # =====================================
    # EMPTY RESULT
    # =====================================

    if not subjects:

        print(
            "No attendance data was returned."
        )


        return render_template(

            "dashboard.html",

            attendance=empty_attendance(),

            phase_1=None,

            calculator_step=0,

            portal_error="unavailable"
        )


    # =====================================
    # CALCULATE TOTALS
    # =====================================

    total_attended = 0

    total_absent = 0


    for subject in subjects:

        try:

            total_attended += int(

                subject.get(
                    "attendedLecture",
                    0
                )

            )

        except (
            TypeError,
            ValueError
        ):

            pass


        try:

            total_absent += int(

                subject.get(
                    "absentLecture",
                    0
                )

            )

        except (
            TypeError,
            ValueError
        ):

            pass


    total_classes = (
        total_attended +
        total_absent
    )


    # =====================================
    # OVERALL PERCENTAGE
    # =====================================

    if total_classes > 0:

        overall_percentage = round(

            (
                total_attended /
                total_classes
            ) * 100,

            2
        )

    else:

        overall_percentage = 0


    # =====================================
    # CREATE USER ATTENDANCE
    # =====================================

    attendance_data = {

        "subjects":
            subjects,

        "total_attended":
            total_attended,

        "total_absent":
            total_absent,

        "total_classes":
            total_classes,

        "overall_percentage":
            overall_percentage
    }


    # =====================================
    # SAVE TO THIS USER'S SESSION
    # =====================================

    session["attendance_data"] = (
        attendance_data
    )


    # =====================================
    # RESET THIS USER'S LEAVE PLAN
    # =====================================

    selected_leaves = {

        "2026-08-29": 0,

        "2026-10-10": 0,

        "2026-11-16": 0
    }


    save_user_leaves(
        selected_leaves
    )


    # =====================================
    # LOG
    # =====================================

    print()

    print(
        "Website received:",
        len(subjects),
        "subjects"
    )

    print(
        "Portal attendance:",
        total_attended,
        "/",
        total_classes
    )

    print(
        "Overall:",
        overall_percentage,
        "%"
    )


    # =====================================
    # FIRST CALCULATION
    # =====================================

    phase_1_result = run_phase_1(

        attendance_data,

        CHECKPOINT_CHOICES,

        selected_leaves
    )


    return render_template(

        "dashboard.html",

        attendance=attendance_data,

        phase_1=phase_1_result,

        calculator_step=1,

        portal_error=None
    )


# =========================================
# SESSIONAL 1
# =========================================

@app.route(
    "/sessional-1",
    methods=["POST"]
)
def sessional_1():
    attendance_data = (
        get_user_attendance()
    )

    selected_leaves = (
        get_user_leaves()
    )

    # =====================================
    # CURRENT INPUT
    # =====================================

    leave_classes = get_requested_leave_classes(
        request.form,
        1
    )

    # =====================================
    # SAVE FOR THIS USER ONLY
    # =====================================

    selected_leaves[
        "2026-08-29"
    ] = leave_classes

    save_user_leaves(
        selected_leaves
    )

    print()
    print(
        "First Sessional:",
        leave_classes,
        "classes"
    )

    # =====================================
    # RECALCULATE
    # =====================================

    phase_1_result = run_phase_1(
        attendance_data,
        CHECKPOINT_CHOICES,
        selected_leaves
    )

    return render_template(
        "dashboard.html",
        attendance=attendance_data,
        phase_1=phase_1_result,
        calculator_step=2,
        portal_error=None
    )


@app.route(
    "/sessional-2",
    methods=["POST"]
)
def sessional_2():
    attendance_data = (
        get_user_attendance()
    )

    selected_leaves = (
        get_user_leaves()
    )

    # =====================================
    # CURRENT INPUT
    # =====================================

    leave_classes = get_requested_leave_classes(
        request.form,
        2
    )

    # =====================================
    # SAVE FOR THIS USER ONLY
    # =====================================

    selected_leaves[
        "2026-10-10"
    ] = leave_classes

    save_user_leaves(
        selected_leaves
    )

    print()
    print(
        "Second Sessional:",
        leave_classes,
        "classes"
    )

    # =====================================
    # RECALCULATE
    # =====================================

    phase_1_result = run_phase_1(
        attendance_data,
        CHECKPOINT_CHOICES,
        selected_leaves
    )

    return render_template(
        "dashboard.html",
        attendance=attendance_data,
        phase_1=phase_1_result,
        calculator_step=3,
        portal_error=None
    )


@app.route(
    "/sessional-3",
    methods=["POST"]
)
def sessional_3():
    attendance_data = (
        get_user_attendance()
    )

    selected_leaves = (
        get_user_leaves()
    )

    # =====================================
    # CURRENT INPUT
    # =====================================

    leave_classes = get_requested_leave_classes(
        request.form,
        3
    )

    # =====================================
    # SAVE FOR THIS USER ONLY
    # =====================================

    selected_leaves[
        "2026-11-16"
    ] = leave_classes

    save_user_leaves(
        selected_leaves
    )

    print()
    print(
        "Third Sessional:",
        leave_classes,
        "classes"
    )

    # =====================================
    # RECALCULATE
    # =====================================

    phase_1_result = run_phase_1(
        attendance_data,
        CHECKPOINT_CHOICES,
        selected_leaves
    )

    return render_template(
        "dashboard.html",
        attendance=attendance_data,
        phase_1=phase_1_result,
        calculator_step=4,
        portal_error=None
    )


# =========================================
# LOGOUT / RESET SESSION
# =========================================

@app.route(
    "/reset"
)
def reset_session():

    session.clear()

    return render_template(

        "dashboard.html",

        attendance=empty_attendance(),

        phase_1=None,

        calculator_step=0,

        portal_error=None
    )


# =========================================
# RUN SERVER
# =========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
```


# ============================================================
# CURRENT BUNK_CALCULATOR.PY SNAPSHOT
# ============================================================

```python
from datetime import date, timedelta
import math

from academic_calendar import (
    TEACHING_CLASSES_PER_DAY,
    ATTENDANCE_TARGET,
    is_teaching_day
)


# =========================================
# BUNKMASTER CALCULATOR
# =========================================

CLASSES_PER_DAY = TEACHING_CLASSES_PER_DAY
TARGET_ATTENDANCE = ATTENDANCE_TARGET


# =========================================
# CHECKPOINTS
# =========================================

CHECKPOINTS = [
    (
        "First Sessional",
        date(2026, 8, 29)
    ),
    (
        "Second Sessional",
        date(2026, 10, 10)
    ),
    (
        "Third Sessional",
        date(2026, 11, 16)
    )
]


# =========================================
# ATTENDANCE PERCENTAGE
# =========================================

def calculate_percentage(attended, total):

    if total == 0:
        return 0

    return (
        attended /
        total
    ) * 100


# =========================================
# CLASSES NEEDED TO REACH TARGET
# =========================================

def classes_needed_to_reach_target(
    attended,
    total_classes
):

    if total_classes == 0:
        return 0

    current_percentage = calculate_percentage(
        attended,
        total_classes
    )

    if current_percentage >= TARGET_ATTENDANCE:
        return 0

    required_classes = math.ceil(
        (
            (TARGET_ATTENDANCE / 100)
            * total_classes
            - attended
        )
        /
        (1 - (TARGET_ATTENDANCE / 100))
    )

    return max(
        0,
        required_classes
    )


# =========================================
# LEAVE CONVERSION
# =========================================

def days_and_classes_to_classes(
    days=0,
    classes=0
):

    try:
        days = int(days)
    except (
        TypeError,
        ValueError
    ):
        days = 0

    try:
        classes = int(classes)
    except (
        TypeError,
        ValueError
    ):
        classes = 0

    days = max(
        0,
        days
    )

    classes = max(
        0,
        classes
    )

    return (
        days * CLASSES_PER_DAY
        +
        classes
    )


def classes_to_leave_display(
    total_classes
):

    try:
        total_classes = int(
            total_classes
        )
    except (
        TypeError,
        ValueError
    ):
        total_classes = 0

    total_classes = max(
        0,
        total_classes
    )

    days, remaining_classes = divmod(
        total_classes,
        CLASSES_PER_DAY
    )

    if days == 0:

        return (
            f"{remaining_classes} "
            f"class(es)"
        )

    if remaining_classes == 0:

        return (
            f"{days} day(s)"
        )

    return (
        f"{days} day(s) "
        f"{remaining_classes} class(es)"
    )


# =========================================
# COUNT TEACHING DAYS
# =========================================

def count_teaching_days(
    start_date,
    end_date
):

    if start_date > end_date:
        return 0

    count = 0

    current = start_date

    while current <= end_date:

        date_string = current.strftime(
            "%Y-%m-%d"
        )

        if is_teaching_day(
            date_string
        ):
            count += 1

        current += timedelta(
            days=1
        )

    return count


# =========================================
# FIND MAXIMUM SAFE LEAVE
# =========================================

def find_maximum_safe_leave(
    attended,
    total_classes,
    future_classes
):

    current_percentage = calculate_percentage(
        attended,
        total_classes
    )

    if current_percentage < TARGET_ATTENDANCE:
        return 0

    maximum_leave_classes = 0

    for missed_classes in range(
        0,
        future_classes + 1
    ):

        future_attended = (
            future_classes -
            missed_classes
        )

        final_attended = (
            attended +
            future_attended
        )

        final_total = (
            total_classes +
            future_classes
        )

        percentage = calculate_percentage(
            final_attended,
            final_total
        )

        if percentage >= TARGET_ATTENDANCE:

            maximum_leave_classes = (
                missed_classes
            )

        else:

            break

    return maximum_leave_classes


# =========================================
# CALCULATE USER'S ACTUAL LEAVE
# =========================================

def calculate_requested_leave(
    attended,
    total_classes,
    future_classes,
    requested_days,
    requested_classes,
    maximum_safe_classes
):

    requested_classes_total = (
        days_and_classes_to_classes(
            requested_days,
            requested_classes
        )
    )

    # =====================================
    # NEVER MISS MORE CLASSES THAN EXIST
    # =====================================

    requested_classes_total = min(
        requested_classes_total,
        max(
            0,
            future_classes
        )
    )

    # =====================================
    # NEVER EXCEED SAFE LEAVE
    # =====================================

    requested_classes_total = min(
        requested_classes_total,
        max(
            0,
            maximum_safe_classes
        )
    )

    missed_classes = (
        requested_classes_total
    )

    future_attended = (
        future_classes -
        missed_classes
    )

    projected_attended = (
        attended +
        future_attended
    )

    projected_total = (
        total_classes +
        future_classes
    )

    projected_percentage = (
        calculate_percentage(
            projected_attended,
            projected_total
        )
    )

    return {

        "requested_leave_classes":
            requested_classes_total,

        "requested_leave":
            requested_classes_total,

        "requested_classes_missed":
            missed_classes,

        "projected_attended":
            projected_attended,

        "projected_total":
            projected_total,

        "projected_percentage":
            round(
                projected_percentage,
                2
            )
    }


# =========================================
# DETERMINE ATTENDANCE STATUS
# =========================================

def determine_status(
    attended,
    total_classes,
    future_classes
):

    current_percentage = calculate_percentage(
        attended,
        total_classes
    )

    if current_percentage >= TARGET_ATTENDANCE:

        return "safe"

    classes_needed = (
        classes_needed_to_reach_target(
            attended,
            total_classes
        )
    )

    maximum_attended = (
        attended +
        future_classes
    )

    maximum_total = (
        total_classes +
        future_classes
    )

    maximum_possible_percentage = (
        calculate_percentage(
            maximum_attended,
            maximum_total
        )
    )

    if maximum_possible_percentage >= TARGET_ATTENDANCE:

        return "recovery"

    return "impossible"


# =========================================
# CHECKPOINT DATE STATUS
# =========================================

def get_checkpoint_state(
    checkpoint_date,
    current_date
):

    if current_date >= checkpoint_date:

        return "completed"

    return "upcoming"


# =========================================
# FIND ACTIVE CHECKPOINT
# =========================================

def get_active_checkpoint_index(
    current_date
):

    for index, (
        checkpoint_name,
        checkpoint_date
    ) in enumerate(CHECKPOINTS):

        if current_date < checkpoint_date:

            return index

    return None


# =========================================
# PHASE 1 CALCULATOR
# =========================================

def run_phase_1(
    attendance_data,
    checkpoint_choices=None,
    requested_leaves=None
):

    starting_attended = (
        attendance_data[
            "total_attended"
        ]
    )

    starting_total = (
        attendance_data[
            "total_classes"
        ]
    )

    if checkpoint_choices is None:
        checkpoint_choices = {}

    if requested_leaves is None:
        requested_leaves = {}

    # =====================================
    # TODAY
    # =====================================

    current_date = date.today()

    active_index = (
        get_active_checkpoint_index(
            current_date
        )
    )

    results = []

    # =====================================
    # CURRENT ATTENDANCE
    #
    # This is the real portal attendance.
    # =====================================

    actual_attended = (
        starting_attended
    )

    actual_total = (
        starting_total
    )

    # =====================================
    # LOOP THROUGH ALL CHECKPOINTS
    # =====================================

    for index, (
        checkpoint_name,
        checkpoint_date
    ) in enumerate(CHECKPOINTS):

        checkpoint_key = (
            checkpoint_date.strftime(
                "%Y-%m-%d"
            )
        )

        state = get_checkpoint_state(
            checkpoint_date,
            current_date
        )

        # =================================
        # COMPLETED CHECKPOINT
        # =================================

        if state == "completed":

            current_percentage = (
                calculate_percentage(
                    actual_attended,
                    actual_total
                )
            )

            results.append({

                "checkpoint":
                    checkpoint_name,

                "date":
                    checkpoint_date.strftime(
                        "%d %B %Y"
                    ),

                "date_key":
                    checkpoint_key,

                "is_teaching_day":
                    is_teaching_day(
                        checkpoint_key
                    ),

                "included":
                    True,

                "state":
                    "completed",

                "is_completed":
                    True,

                "is_active":
                    False,

                "is_upcoming":
                    False,

                "status":
                    determine_status(
                        actual_attended,
                        actual_total,
                        0
                    ),

                "starting_attended":
                    actual_attended,

                "starting_total":
                    actual_total,

                "starting_percentage":
                    round(
                        current_percentage,
                        2
                    ),

                "teaching_days":
                    0,

                "future_classes":
                    0,

                "maximum_leave":
                    0,

                "maximum_leave_classes":
                    0,

                "maximum_leave_days":
                    0,

                "maximum_leave_remaining_classes":
                    0,

                "maximum_leave_display":
                    "0 class(es)",

                "classes_needed_for_75":
                    classes_needed_to_reach_target(
                        actual_attended,
                        actual_total
                    ),

                "maximum_possible_percentage":
                    round(
                        current_percentage,
                        2
                    ),

                "projected_without_leave":
                    round(
                        current_percentage,
                        2
                    ),

                # No new leave is applied to a
                # checkpoint that has already passed.
                "requested_leave":
                    0,

                "requested_leave_classes":
                    0,

                "requested_leave_days":
                    0,

                "requested_leave_remaining_classes":
                    0,

                "requested_leave_display":
                    "0 class(es)",

                "requested_classes_missed":
                    0,

                "requested_projected_attended":
                    actual_attended,

                "requested_projected_total":
                    actual_total,

                "requested_projected_percentage":
                    round(
                        current_percentage,
                        2
                    ),

                "requested_leave_is_safe":
                    True,

                "remaining_safe_leave":
                    0,

                "remaining_safe_leave_classes":
                    0,

                "remaining_safe_leave_days":
                    0,

                "remaining_safe_leave_remaining_classes":
                    0,

                "remaining_safe_leave_display":
                    "0 class(es)",

                "final_attended":
                    actual_attended,

                "final_total":
                    actual_total,

                "final_percentage":
                    round(
                        current_percentage,
                        2
                    ),

                "classes_missed":
                    0
            })

            continue

        # =================================
        # UPCOMING CHECKPOINT
        # =================================

        # ---------------------------------
        # Determine where this calculation
        # starts.
        #
        # If this is the first upcoming
        # checkpoint, use TOMORROW.
        #
        # If a previous upcoming checkpoint
        # was processed immediately before
        # this one, start the next day after
        # that checkpoint.
        # ---------------------------------

        if index == active_index:

            calculation_start = (
                current_date +
                timedelta(days=1)
            )

        else:

            previous_checkpoint_date = (
                CHECKPOINTS[index - 1][1]
            )

            calculation_start = (
                previous_checkpoint_date +
                timedelta(days=1)
            )

        # ---------------------------------
        # Check whether the checkpoint day
        # itself is a teaching day.
        # ---------------------------------

        checkpoint_is_teaching_day = (
            is_teaching_day(
                checkpoint_key
            )
        )

        if checkpoint_is_teaching_day:

            calculation_end = (
                checkpoint_date
            )

        else:

            calculation_end = (
                checkpoint_date -
                timedelta(days=1)
            )

        # ---------------------------------
        # Make sure we never calculate
        # backwards.
        # ---------------------------------

        if calculation_start > calculation_end:

            teaching_days = 0

        else:

            teaching_days = (
                count_teaching_days(
                    calculation_start,
                    calculation_end
                )
            )

        future_classes = (
            teaching_days *
            CLASSES_PER_DAY
        )

        # =================================
        # CURRENT STATUS
        # =================================

        status = determine_status(
            actual_attended,
            actual_total,
            future_classes
        )

        starting_percentage = (
            calculate_percentage(
                actual_attended,
                actual_total
            )
        )

        # =================================
        # RECOVERY INFORMATION
        # =================================

        classes_needed = (
            classes_needed_to_reach_target(
                actual_attended,
                actual_total
            )
        )

        maximum_attended_if_no_leave = (
            actual_attended +
            future_classes
        )

        maximum_total_if_no_leave = (
            actual_total +
            future_classes
        )

        maximum_possible_percentage = (
            calculate_percentage(
                maximum_attended_if_no_leave,
                maximum_total_if_no_leave
            )
        )

        # =================================
        # MAXIMUM SAFE LEAVE
        # =================================

        maximum_leave_classes = (
            find_maximum_safe_leave(
                actual_attended,
                actual_total,
                future_classes
            )
        )

        (
            maximum_leave_days,
            maximum_leave_remaining_classes
        ) = divmod(
            maximum_leave_classes,
            CLASSES_PER_DAY
        )

        # =================================
        # USER'S ACTUAL CHOICE
        # =================================

        raw_requested = (
            requested_leaves.get(
                checkpoint_key,
                0
            )
        )

        if isinstance(
            raw_requested,
            dict
        ):

            requested_days = (
                raw_requested.get(
                    "days",
                    0
                )
            )

            requested_classes = (
                raw_requested.get(
                    "classes",
                    0
                )
            )

        else:

            requested_days = 0

            requested_classes = (
                raw_requested
            )

        requested_result = (
            calculate_requested_leave(
                actual_attended,
                actual_total,
                future_classes,
                requested_days,
                requested_classes,
                maximum_leave_classes
            )
        )

        requested_leave_classes = (
            requested_result[
                "requested_leave_classes"
            ]
        )

        (
            requested_leave_days,
            requested_leave_remaining_classes
        ) = divmod(
            requested_leave_classes,
            CLASSES_PER_DAY
        )

        requested_leave_is_safe = (
            requested_leave_classes
            <= maximum_leave_classes
            and
            requested_result[
                "projected_percentage"
            ]
            >= TARGET_ATTENDANCE
        )

        # =================================
        # PROJECTED WITHOUT LEAVE
        # =================================

        projected_without_leave = (
            calculate_percentage(
                maximum_attended_if_no_leave,
                maximum_total_if_no_leave
            )
        )

        # =================================
        # REMAINING SAFE LEAVE
        # =================================

        remaining_safe_leave_classes = max(
            0,
            maximum_leave_classes
            -
            requested_leave_classes
        )

        (
            remaining_safe_leave_days,
            remaining_safe_leave_remaining_classes
        ) = divmod(
            remaining_safe_leave_classes,
            CLASSES_PER_DAY
        )

        # =================================
        # SAVE RESULT
        # =================================

        results.append({

            "checkpoint":
                checkpoint_name,

            "date":
                checkpoint_date.strftime(
                    "%d %B %Y"
                ),

            "date_key":
                checkpoint_key,

            "is_teaching_day":
                checkpoint_is_teaching_day,

            "included":
                True,

            "state":
                "active"
                if index == active_index
                else "upcoming",

            "is_completed":
                False,

            "is_active":
                index == active_index,

            "is_upcoming":
                True,

            "status":
                status,

            "starting_attended":
                actual_attended,

            "starting_total":
                actual_total,

            "starting_percentage":
                round(
                    starting_percentage,
                    2
                ),

            "teaching_days":
                teaching_days,

            "future_classes":
                future_classes,

            "maximum_leave":
                maximum_leave_classes,

            "maximum_leave_classes":
                maximum_leave_classes,

            "maximum_leave_days":
                maximum_leave_days,

            "maximum_leave_remaining_classes":
                maximum_leave_remaining_classes,

            "maximum_leave_display":
                classes_to_leave_display(
                    maximum_leave_classes
                ),

            "classes_needed_for_75":
                classes_needed,

            "maximum_possible_percentage":
                round(
                    maximum_possible_percentage,
                    2
                ),

            "projected_without_leave":
                round(
                    projected_without_leave,
                    2
                ),

            "requested_leave":
                requested_leave_classes,

            "requested_leave_classes":
                requested_leave_classes,

            "requested_leave_days":
                requested_leave_days,

            "requested_leave_remaining_classes":
                requested_leave_remaining_classes,

            "requested_leave_display":
                classes_to_leave_display(
                    requested_leave_classes
                ),

            "requested_classes_missed":
                requested_result[
                    "requested_classes_missed"
                ],

            "requested_projected_attended":
                requested_result[
                    "projected_attended"
                ],

            "requested_projected_total":
                requested_result[
                    "projected_total"
                ],

            "requested_projected_percentage":
                requested_result[
                    "projected_percentage"
                ],

            "requested_leave_is_safe":
                requested_leave_is_safe,

            "remaining_safe_leave":
                remaining_safe_leave_classes,

            "remaining_safe_leave_classes":
                remaining_safe_leave_classes,

            "remaining_safe_leave_days":
                remaining_safe_leave_days,

            "remaining_safe_leave_remaining_classes":
                remaining_safe_leave_remaining_classes,

            "remaining_safe_leave_display":
                classes_to_leave_display(
                    remaining_safe_leave_classes
                ),

            "final_attended":
                requested_result[
                    "projected_attended"
                ],

            "final_total":
                requested_result[
                    "projected_total"
                ],

            "final_percentage":
                requested_result[
                    "projected_percentage"
                ],

            "classes_missed":
                requested_result[
                    "requested_classes_missed"
                ]
        })

        # =================================
        # CARRY PROJECTED ATTENDANCE
        # =================================
        #
        # IMPORTANT:
        #
        # Only future checkpoints are carried
        # forward.
        #
        # This means:
        #
        # Before Aug 29:
        #     First choice -> Second start
        #
        # But after Aug 29:
        #     We do NOT apply the old First
        #     choice again.
        #
        # The portal's current attendance is
        # already the real starting point.
        # =================================

        actual_attended = (
            requested_result[
                "projected_attended"
            ]
        )

        actual_total = (
            requested_result[
                "projected_total"
            ]
        )

    # =====================================
    # FINAL CURRENT ATTENDANCE
    # =====================================

    current_percentage = (
        calculate_percentage(
            actual_attended,
            actual_total
        )
    )

    # =====================================
    # SEMESTER COMPLETE?
    # =====================================

    semester_completed = (
        active_index is None
    )

    # =====================================
    # ACTIVE CHECKPOINT
    # =====================================

    if active_index is None:

        active_checkpoint = None

    else:

        active_checkpoint = (
            CHECKPOINTS[
                active_index
            ][0]
        )

    return {

        "current_attended":
            actual_attended,

        "current_total":
            actual_total,

        "current_percentage":
            round(
                current_percentage,
                2
            ),

        "active_checkpoint_index":
            active_index,

        "active_checkpoint":
            active_checkpoint,

        "semester_completed":
            semester_completed,

        "today":
            current_date.strftime(
                "%d %B %Y"
            ),

        "checkpoints":
            results
    }
```


# ============================================================
# CURRENT PORTAL.PY SNAPSHOT
# ============================================================

```python
from playwright.sync_api import sync_playwright
import time


# =========================================
# PORTAL ERRORS
# =========================================

class PortalUnavailableError(Exception):
    """The NIET portal could not be reached or loaded."""
    pass


class PortalLoginError(Exception):
    """The NIET portal was reachable but login failed."""
    pass


# =========================================
# GET ATTENDANCE
# =========================================

def get_attendance(username, password):

    total_start = time.perf_counter()

    attendance_data = []
    browser = None

    try:

        with sync_playwright() as p:

            # ---------------------------------
            # 1. Launch browser
            # ---------------------------------

            t0 = time.perf_counter()

            try:

                browser = p.chromium.launch(
                    headless=True
                )

                page = browser.new_page()

            except Exception as e:

                print("Could not launch browser:")
                print(e)

                raise PortalUnavailableError(
                    "Unable to start the browser."
                )


            t1 = time.perf_counter()

            print(
                f"[TIME] Browser launch: "
                f"{t1 - t0:.2f}s"
            )


            # ---------------------------------
            # 2. Open login page
            # ---------------------------------

            t0 = time.perf_counter()

            try:

                page.goto(
                    "https://nietcloud.niet.co.in/login.htm",
                    wait_until="domcontentloaded",
                    timeout=15000
                )

            except Exception as e:

                print()
                print("======================================")
                print("NIET PORTAL UNAVAILABLE")
                print("======================================")
                print(
                    "Could not reach the college portal."
                )
                print(e)
                print()

                raise PortalUnavailableError(
                    "The NIET college portal is currently "
                    "unreachable."
                )


            t1 = time.perf_counter()

            print(
                f"[TIME] Login page: "
                f"{t1 - t0:.2f}s"
            )


            # ---------------------------------
            # 3. Login
            # ---------------------------------

            t0 = time.perf_counter()

            try:

                page.locator(
                    "#j_username"
                ).fill(username)

                page.locator(
                    "#password-1"
                ).fill(password)

                page.locator(
                    "button[type='submit']"
                ).click()

            except Exception as e:

                print("Could not submit login:")
                print(e)

                raise PortalUnavailableError(
                    "The NIET login page could not "
                    "be used."
                )


            try:

                page.wait_for_url(
                    "**/home.htm",
                    timeout=15000
                )

            except Exception:

                print()
                print("======================================")
                print("NIET LOGIN FAILED")
                print("======================================")

                print(
                    "Current URL:",
                    page.url
                )

                print()

                # ---------------------------------
                # If the portal itself disappeared
                # after login attempt, treat it as
                # unavailable.
                # ---------------------------------

                if (
                    "nietcloud.niet.co.in"
                    not in page.url
                ):

                    raise PortalUnavailableError(
                        "The NIET portal became "
                        "unreachable."
                    )

                raise PortalLoginError(
                    "The NIET portal was reached, "
                    "but login was not successful."
                )


            t1 = time.perf_counter()

            print(
                f"[TIME] Login: "
                f"{t1 - t0:.2f}s"
            )

            print(
                "Logged in:",
                page.url
            )


            # ---------------------------------
            # 4. Attendance API listener
            # ---------------------------------

            def handle_response(response):

                if (
                    "stu_getStudentBatchCourseAttendanceList.json"
                    in response.url
                ):

                    print(
                        "Subject-wise attendance "
                        "request found."
                    )

                    try:

                        data = response.json()

                        if isinstance(data, list):

                            attendance_data.clear()

                            attendance_data.extend(
                                data
                            )

                        print(
                            "Captured",
                            len(attendance_data),
                            "subjects"
                        )

                    except Exception as e:

                        print(
                            "Could not read attendance:",
                            e
                        )


            page.on(
                "response",
                handle_response
            )


            # ---------------------------------
            # 5. Academic Functions
            # ---------------------------------

            t0 = time.perf_counter()

            try:

                academic = page.locator(
                    'a[pid="20009"]'
                )

                academic.wait_for(
                    state="visible",
                    timeout=10000
                )

                academic.click()

            except Exception as e:

                print(
                    "Academic Functions page "
                    "could not be opened:"
                )

                print(e)

                raise PortalUnavailableError(
                    "The NIET portal did not respond "
                    "correctly after login."
                )


            t1 = time.perf_counter()

            print(
                f"[TIME] Academic Functions: "
                f"{t1 - t0:.2f}s"
            )


            # ---------------------------------
            # 6. Courses
            # ---------------------------------

            t0 = time.perf_counter()

            try:

                courses = page.locator(
                    'a[pid="24732"]'
                )

                courses.wait_for(
                    state="visible",
                    timeout=10000
                )

                courses.click()

            except Exception as e:

                print(
                    "Courses page "
                    "could not be opened:"
                )

                print(e)

                raise PortalUnavailableError(
                    "The NIET portal did not respond "
                    "correctly while opening courses."
                )


            t1 = time.perf_counter()

            print(
                f"[TIME] Courses: "
                f"{t1 - t0:.2f}s"
            )


            # ---------------------------------
            # 7. Attendance + API
            # ---------------------------------

            t0 = time.perf_counter()

            try:

                attendance_button = page.locator(
                    'button[data-tab="attendanceTab"]'
                )

                attendance_button.wait_for(
                    state="visible",
                    timeout=10000
                )

                attendance_button.click()

                print(
                    "Attendance clicked."
                )

            except Exception as e:

                print(
                    "Attendance section "
                    "could not be opened:"
                )

                print(e)

                raise PortalUnavailableError(
                    "The NIET attendance page "
                    "could not be opened."
                )


            # ---------------------------------
            # Wait for attendance API
            # ---------------------------------

            deadline = (
                time.perf_counter() + 10
            )

            while (
                not attendance_data
                and time.perf_counter() < deadline
            ):

                page.wait_for_timeout(50)


            t1 = time.perf_counter()

            print(
                f"[TIME] Attendance + API: "
                f"{t1 - t0:.2f}s"
            )

            print(
                "Subjects received:",
                len(attendance_data)
            )


            # ---------------------------------
            # Attendance request succeeded but
            # returned no subjects.
            # ---------------------------------

            if not attendance_data:

                raise PortalUnavailableError(
                    "The attendance data could not "
                    "be retrieved from the NIET portal."
                )


            # ---------------------------------
            # Total processing time
            # ---------------------------------

            total_end = time.perf_counter()

            print()
            print(
                "======================================"
            )

            print(
                f"[TIME] TOTAL: "
                f"{total_end - total_start:.2f}s"
            )

            print(
                "======================================"
            )

            print()


            return attendance_data


    except (
        PortalUnavailableError,
        PortalLoginError
    ):

        raise


    except Exception as e:

        print()
        print(
            "======================================"
        )
        print(
            "UNEXPECTED PORTAL ERROR"
        )
        print(
            "======================================"
        )
        print(e)
        print()

        raise PortalUnavailableError(
            "The NIET portal is currently unavailable."
        )


    finally:

        # -------------------------------------
        # Always close browser
        # -------------------------------------

        if browser:

            try:

                browser.close()

            except Exception:

                pass
```



# 32. FUTURE CHANGE LOG

When making a change, append a short entry here.

Format:

```text
DATE:
CHANGE:
FILES:
WHY:
TEST:
RESULT:
```

Do not delete previous entries. This section is the project's running backend history.
