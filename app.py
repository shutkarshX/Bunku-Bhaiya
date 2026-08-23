from flask import Flask, render_template, request
from portal import get_attendance
from bunk_calculator import run_phase_1
import academic_calendar


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
# HOME PAGE
# =========================================

@app.route("/")
def dashboard():

    return render_template(
        "dashboard.html",
        attendance=attendance_data,
        phase_1=None
    )


# =========================================
# GET ATTENDANCE
# =========================================

@app.route("/get-attendance", methods=["POST"])
def get_attendance_page():

    global attendance_data

    username = request.form.get("username")
    password = request.form.get("password")

    print("\nStarting attendance retrieval...")

    # -------------------------------------
    # Get attendance from college portal
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
    # Don't run calculator yet.
    #
    # Website will now ask the user
    # whether checkpoint dates should
    # be included.
    # -------------------------------------

    return render_template(
        "dashboard.html",
        attendance=attendance_data,
        phase_1=None,
        checkpoint_options=True
    )


# =========================================
# RUN BUNK CALCULATOR
# =========================================

@app.route(
    "/calculate-bunk",
    methods=["POST"]
)
def calculate_bunk():

    # -------------------------------------
    # Read choices from website
    # -------------------------------------

    checkpoint_choices = {}

    # 10 October
    if request.form.get(
        "checkpoint_2026_10_10"
    ) == "yes":

        checkpoint_choices[
            "2026-10-10"
        ] = True

    else:

        checkpoint_choices[
            "2026-10-10"
        ] = False

    # 16 November
    if request.form.get(
        "checkpoint_2026_11_16"
    ) == "yes":

        checkpoint_choices[
            "2026-11-16"
        ] = True

    else:

        checkpoint_choices[
            "2026-11-16"
        ] = False

    # -------------------------------------
    # Run calculator
    # -------------------------------------

    phase_1_result = run_phase_1(
        attendance_data,
        checkpoint_choices
    )

    print()
    print(
        "Phase 1 calculator result:",
        phase_1_result
    )

    # -------------------------------------
    # Show results
    # -------------------------------------

    return render_template(
        "dashboard.html",
        attendance=attendance_data,
        phase_1=phase_1_result,
        checkpoint_options=False
    )


# =========================================
# RUN SERVER
# =========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )