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