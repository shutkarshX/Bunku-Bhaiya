from flask import Flask, render_template, request
from portal import get_attendance
from bunk_calculator import run_phase_1


app = Flask(__name__)


# =========================================
# STORED ATTENDANCE DATA
# =========================================

attendance_data = {
    "subjects": [],
    "total_attended": 0,
    "total_absent": 0,
    "total_classes": 0,
    "overall_percentage": 0
}


# =========================================
# STORED CALCULATOR STATE
# =========================================

checkpoint_choices = {
    "2026-10-10": True,
    "2026-11-16": True
}

selected_leaves = {
    "2026-08-29": 0,
    "2026-10-10": 0,
    "2026-11-16": 0
}


# =========================================
# HOME
# =========================================

@app.route("/")
def dashboard():

    return render_template(
        "dashboard.html",
        attendance=attendance_data,
        phase_1=None,
        calculator_step=0
    )


# =========================================
# GET ATTENDANCE
# =========================================

@app.route("/get-attendance", methods=["POST"])
def get_attendance_page():

    global attendance_data
    global selected_leaves

    username = request.form.get("username")
    password = request.form.get("password")

    print("\nStarting attendance retrieval...")

    # -------------------------------------
    # Get attendance
    # -------------------------------------

    subjects = get_attendance(
        username,
        password
    )

    # -------------------------------------
    # Calculate totals
    # -------------------------------------

    total_attended = 0
    total_absent = 0

    for subject in subjects:

        total_attended += int(
            subject.get(
                "attendedLecture",
                0
            )
        )

        total_absent += int(
            subject.get(
                "absentLecture",
                0
            )
        )

    total_classes = (
        total_attended +
        total_absent
    )

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

    # -------------------------------------
    # Store attendance
    # -------------------------------------

    attendance_data = {

        "subjects": subjects,

        "total_attended":
            total_attended,

        "total_absent":
            total_absent,

        "total_classes":
            total_classes,

        "overall_percentage":
            overall_percentage
    }

    # -------------------------------------
    # Reset user's leave plan
    # -------------------------------------

    selected_leaves = {
        "2026-08-29": 0,
        "2026-10-10": 0,
        "2026-11-16": 0
    }

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

    # -------------------------------------
    # FIRST SESSIONAL
    #
    # Calculate maximum safe leave BEFORE
    # 29 August.
    # -------------------------------------

    phase_1_result = run_phase_1(
        attendance_data,
        checkpoint_choices,
        selected_leaves
    )

    return render_template(
        "dashboard.html",
        attendance=attendance_data,
        phase_1=phase_1_result,
        calculator_step=1
    )


# =========================================
# SESSION 1
# USER CHOOSES LEAVE BEFORE 29 AUGUST
# =========================================

@app.route(
    "/sessional-1",
    methods=["POST"]
)
def sessional_1():

    global selected_leaves

    try:

        leave = int(
            request.form.get(
                "leave_1",
                0
            )
        )

    except (TypeError, ValueError):

        leave = 0

    leave = max(0, leave)

    # -------------------------------------
    # Store actual user choice
    # -------------------------------------

    selected_leaves[
        "2026-08-29"
    ] = leave

    print()
    print(
        "First Sessional leave:",
        leave,
        "days"
    )

    # -------------------------------------
    # Recalculate everything.
    #
    # The calculator now carries the user's
    # first choice into the second sessional.
    # -------------------------------------

    phase_1_result = run_phase_1(
        attendance_data,
        checkpoint_choices,
        selected_leaves
    )

    return render_template(
        "dashboard.html",
        attendance=attendance_data,
        phase_1=phase_1_result,
        calculator_step=2
    )


# =========================================
# SESSION 2
# USER CHOOSES LEAVE BEFORE 10 OCTOBER
# =========================================

@app.route(
    "/sessional-2",
    methods=["POST"]
)
def sessional_2():

    global selected_leaves

    try:

        leave = int(
            request.form.get(
                "leave_2",
                0
            )
        )

    except (TypeError, ValueError):

        leave = 0

    leave = max(0, leave)

    # -------------------------------------
    # Store actual choice
    # -------------------------------------

    selected_leaves[
        "2026-10-10"
    ] = leave

    print()
    print(
        "Second Sessional leave:",
        leave,
        "days"
    )

    # -------------------------------------
    # Recalculate.
    #
    # First + second choices now carry
    # forward to the third checkpoint.
    # -------------------------------------

    phase_1_result = run_phase_1(
        attendance_data,
        checkpoint_choices,
        selected_leaves
    )

    return render_template(
        "dashboard.html",
        attendance=attendance_data,
        phase_1=phase_1_result,
        calculator_step=3
    )


# =========================================
# SESSION 3
# USER CHOOSES LEAVE BEFORE 16 NOVEMBER
# =========================================

@app.route(
    "/sessional-3",
    methods=["POST"]
)
def sessional_3():

    global selected_leaves

    try:

        leave = int(
            request.form.get(
                "leave_3",
                0
            )
        )

    except (TypeError, ValueError):

        leave = 0

    leave = max(0, leave)

    # -------------------------------------
    # Store actual choice
    # -------------------------------------

    selected_leaves[
        "2026-11-16"
    ] = leave

    print()
    print(
        "Third Sessional leave:",
        leave,
        "days"
    )

    # -------------------------------------
    # Final calculation
    # -------------------------------------

    phase_1_result = run_phase_1(
        attendance_data,
        checkpoint_choices,
        selected_leaves
    )

    return render_template(
        "dashboard.html",
        attendance=attendance_data,
        phase_1=phase_1_result,
        calculator_step=4
    )


# =========================================
# RUN SERVER
# =========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )