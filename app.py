from flask import Flask, render_template, request, session

from portal import (
    get_attendance,
    PortalUnavailableError,
    PortalLoginError
)

from bunk_calculator import run_phase_1


app = Flask(__name__)

# Required for Flask sessions.
# Change this to a long random value before deploying publicly.
app.secret_key = "bunkmaster-dev-secret-key"


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
    #
    # Supports the current backend format.
    # =====================================

    raw_leave = request.form.get(
        "leave_1_classes"
    )


    # Compatibility with the old form.

    if raw_leave is None:

        raw_leave = request.form.get(
            "leave_1",
            0
        )


    try:

        leave_classes = int(
            raw_leave
        )

    except (
        TypeError,
        ValueError
    ):

        leave_classes = 0


    leave_classes = max(
        0,
        leave_classes
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


# =========================================
# SESSIONAL 2
# =========================================

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

    raw_leave = request.form.get(
        "leave_2_classes"
    )


    if raw_leave is None:

        raw_leave = request.form.get(
            "leave_2",
            0
        )


    try:

        leave_classes = int(
            raw_leave
        )

    except (
        TypeError,
        ValueError
    ):

        leave_classes = 0


    leave_classes = max(
        0,
        leave_classes
    )


    # =====================================
    # SAVE FOR THIS USER
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


# =========================================
# SESSIONAL 3
# =========================================

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

    raw_leave = request.form.get(
        "leave_3_classes"
    )


    if raw_leave is None:

        raw_leave = request.form.get(
            "leave_3",
            0
        )


    try:

        leave_classes = int(
            raw_leave
        )

    except (
        TypeError,
        ValueError
    ):

        leave_classes = 0


    leave_classes = max(
        0,
        leave_classes
    )


    # =====================================
    # SAVE FOR THIS USER
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
    # FINAL CALCULATION
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