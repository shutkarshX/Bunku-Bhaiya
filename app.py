import os

from flask import (
    Flask,
    render_template,
    request,
    session
)

from portal import (
    get_attendance,
    get_subject_details,
    PortalUnavailableError,
    PortalLoginError
)

from bunk_calculator import (
    run_phase_1,
    classes_to_leave_display,
    days_and_classes_to_classes
)


app = Flask(__name__)


# =========================================
# FLASK SESSION
# =========================================

SECRET_KEY = os.environ.get(
    "SECRET_KEY"
)

if not SECRET_KEY:

    raise RuntimeError(
        "SECRET_KEY environment variable is not set. "
        "Please configure it before running BunkMaster."
    )

app.secret_key = SECRET_KEY


# =========================================
# JINJA HELPERS
# =========================================

app.jinja_env.globals[
    "classes_to_leave_display"
] = classes_to_leave_display


# =========================================
# CHECKPOINT SETTINGS
# =========================================

CHECKPOINT_CHOICES = {

    "2026-08-29": True,

    "2026-10-10": True,

    "2026-11-16": True
}


# =========================================
# EMPTY ATTENDANCE
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
# GET ATTENDANCE FROM SESSION
# =========================================

def get_user_attendance():

    return session.get(

        "attendance_data",

        empty_attendance()
    )


# =========================================
# GET USER LEAVE PLAN
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
# SAVE USER LEAVE PLAN
# =========================================

def save_user_leaves(
    leaves
):

    session[
        "selected_leaves"
    ] = leaves

    session.modified = True


# =========================================
# DETERMINE AUTOMATIC DASHBOARD STEP
# =========================================

def get_dashboard_step(
    phase_1_result
):

    active_index = (

        phase_1_result.get(
            "active_checkpoint_index"
        )

    )


    # =====================================
    # SEMESTER COMPLETE
    # =====================================

    if active_index is None:

        return 4


    # =====================================
    # FIRST SESSIONAL
    # =====================================

    if active_index == 0:

        return 1


    # =====================================
    # SECOND SESSIONAL
    # =====================================

    if active_index == 1:

        return 2


    # =====================================
    # THIRD SESSIONAL
    # =====================================

    if active_index == 2:

        return 3


    return 1


# =========================================
# PARSE DAYS + CLASSES
# =========================================

def get_requested_leave_classes(
    form,
    step
):

    days_raw = form.get(

        f"leave_{step}_days",

        0
    )


    classes_raw = form.get(

        f"leave_{step}_classes",

        0
    )


    try:

        days = int(
            days_raw
        )

    except (
        TypeError,
        ValueError
    ):

        days = 0


    try:

        classes = int(
            classes_raw
        )

    except (
        TypeError,
        ValueError
    ):

        classes = 0


    return days_and_classes_to_classes(

        days,

        classes
    )


# =========================================
# RENDER DASHBOARD
# =========================================
#
# IMPORTANT:
#
# calculator_step can now be explicitly
# supplied by the sessional routes.
#
# This prevents today's date from forcing
# the user back to the current calendar
# checkpoint after they click Continue.
#
# If calculator_step is NOT supplied,
# the normal date-based logic is used.
# =========================================

def render_dashboard(

    attendance_data,

    phase_1=None,

    portal_error=None,

    calculator_step=None
):

    # =====================================
    # NO CALCULATOR RESULT
    # =====================================

    if phase_1 is None:

        calculator_step = 0


    # =====================================
    # AUTOMATIC STEP
    #
    # Only use this when the caller has
    # NOT explicitly selected a step.
    # =====================================

    elif calculator_step is None:

        calculator_step = (

            get_dashboard_step(
                phase_1
            )

        )


    return render_template(

        "dashboard.html",

        attendance=(lambda d: (d.update({"subject_details": get_subject_details((d.get("subjects") or [{}])[0].get("_bunkmaster_subject_details_token"))}), d)[1])(dict(attendance_data)),

        phase_1=phase_1,

        calculator_step=calculator_step,

        portal_error=portal_error

    )


# =========================================
# HOME
# =========================================

@app.route("/")
def dashboard():

    attendance_data = (

        get_user_attendance()

    )


    # =====================================
    # NO LOGIN YET
    # =====================================

    if not attendance_data[
        "subjects"
    ]:

        return render_dashboard(

            attendance_data

        )


    # =====================================
    # RECALCULATE CURRENT STATE
    #
    # This allows the active checkpoint
    # to change automatically as today's
    # date changes.
    # =====================================

    selected_leaves = (

        get_user_leaves()

    )


    phase_1_result = run_phase_1(

        attendance_data,

        CHECKPOINT_CHOICES,

        selected_leaves

    )


    return render_dashboard(

        attendance_data,

        phase_1_result

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
    # PORTAL
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


        return render_dashboard(

            empty_attendance(),

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


        return render_dashboard(

            empty_attendance(),

            portal_error="login"

        )


    except Exception as e:

        print()

        print(
            "Unexpected portal error:"
        )

        print(e)

        print()


        return render_dashboard(

            empty_attendance(),

            portal_error="unavailable"

        )


    # =====================================
    # EMPTY RESULT
    # =====================================

    if not subjects:

        print(
            "No attendance data was returned."
        )


        return render_dashboard(

            empty_attendance(),

            portal_error="unavailable"

        )


    # =====================================
    # TOTALS
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

        total_attended

        +

        total_absent

    )


    # =====================================
    # PERCENTAGE
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
    # ATTENDANCE DATA
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
    # SAVE ATTENDANCE
    # =====================================

    session[
        "attendance_data"
    ] = attendance_data


    # =====================================
    # RESET LEAVE PLAN
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
    # CALCULATE
    # =====================================

    phase_1_result = run_phase_1(

        attendance_data,

        CHECKPOINT_CHOICES,

        selected_leaves

    )


    print()

    print(

        "Active checkpoint:",

        phase_1_result.get(

            "active_checkpoint"

        )

    )


    print(

        "Active index:",

        phase_1_result.get(

            "active_checkpoint_index"

        )

    )


    print(

        "Semester completed:",

        phase_1_result.get(

            "semester_completed"

        )

    )


    # =====================================
    # RENDER
    #
    # Do NOT force a manual step here.
    #
    # This is a fresh attendance retrieval,
    # so the automatic calendar checkpoint
    # should be shown.
    # =====================================

    return render_dashboard(

        attendance_data,

        phase_1_result

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

    leave_classes = (

        get_requested_leave_classes(

            request.form,

            1

        )

    )


    # =====================================
    # SAVE FIRST SESSIONAL LEAVE
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


    # =====================================
    # IMPORTANT:
    #
    # User explicitly clicked Continue.
    #
    # Therefore show SECOND SESSIONAL,
    # even if today's calendar date still
    # says First Sessional is active.
    # =====================================

    return render_dashboard(

        attendance_data,

        phase_1_result,

        calculator_step=2

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

    leave_classes = (

        get_requested_leave_classes(

            request.form,

            2

        )

    )


    # =====================================
    # SAVE SECOND SESSIONAL LEAVE
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


    # =====================================
    # SHOW THIRD SESSIONAL
    # =====================================

    return render_dashboard(

        attendance_data,

        phase_1_result,

        calculator_step=3

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

    leave_classes = (

        get_requested_leave_classes(

            request.form,

            3

        )

    )


    # =====================================
    # SAVE THIRD SESSIONAL LEAVE
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


    # =====================================
    # SHOW FINAL RESULT
    # =====================================

    return render_dashboard(

        attendance_data,

        phase_1_result,

        calculator_step=4

    )


# =========================================
# RESET / LOGOUT
# =========================================

@app.route(

    "/reset"
)
def reset_session():

    session.clear()


    return render_dashboard(

        empty_attendance()

    )


# =========================================
# RUN SERVER
# =========================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )