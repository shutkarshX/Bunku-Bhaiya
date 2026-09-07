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

def save_user_leaves(leaves):
    session["selected_leaves"] = leaves
    session.modified = True


# =========================================
# DETERMINE AUTOMATIC DASHBOARD STEP
# =========================================

def get_dashboard_step(phase_1_result):
    active_index = phase_1_result.get(
        "active_checkpoint_index"
    )

    if active_index is None:
        return 4

    if active_index == 0:
        return 1

    if active_index == 1:
        return 2

    if active_index == 2:
        return 3

    return 1


# =========================================
# PARSE DAYS + CLASSES
# =========================================

def get_requested_leave_classes(form, step):
    days_raw = form.get(f"leave_{step}_days", 0)
    classes_raw = form.get(f"leave_{step}_classes", 0)

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
# RENDER DASHBOARD
# =========================================

def render_dashboard(
    attendance_data,
    phase_1=None,
    portal_error=None,
    calculator_step=None
):
    if phase_1 is None:
        calculator_step = 0
    elif calculator_step is None:
        calculator_step = get_dashboard_step(phase_1)

    attendance = dict(attendance_data)
    subjects = attendance.get("subjects") or []
    token = subjects[0].get(
        "_bunkmaster_subject_details_token"
    ) if subjects else None
    attendance["subject_details"] = get_subject_details(token)

    return render_template(
        "dashboard.html",
        attendance=attendance,
        phase_1=phase_1,
        calculator_step=calculator_step,
        portal_error=portal_error
    )


# =========================================
# HOME
# =========================================

@app.route("/")
def dashboard():
    attendance_data = get_user_attendance()

    if not attendance_data["subjects"]:
        return render_dashboard(attendance_data)

    selected_leaves = get_user_leaves()
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
    username = request.form.get("username")
    password = request.form.get("password")

    print()
    print("Starting attendance retrieval...")

    try:
        subjects = get_attendance(
            username,
            password
        )
    except PortalUnavailableError as e:
        print()
        print("======================================")
        print("NIET PORTAL UNAVAILABLE")
        print("======================================")
        print(e)
        print()
        return render_dashboard(
            empty_attendance(),
            portal_error="unavailable"
        )
    except PortalLoginError as e:
        print()
        print("======================================")
        print("NIET LOGIN FAILED")
        print("======================================")
        print(e)
        print()
        return render_dashboard(
            empty_attendance(),
            portal_error="login"
        )
    except Exception as e:
        print()
        print("Unexpected portal error:")
        print(e)
        print()
        return render_dashboard(
            empty_attendance(),
            portal_error="unavailable"
        )

    if not subjects:
        print("No attendance data was returned.")
        return render_dashboard(
            empty_attendance(),
            portal_error="unavailable"
        )

    total_attended = 0
    total_absent = 0

    for subject in subjects:
        try:
            total_attended += int(
                subject.get("attendedLecture", 0)
            )
        except (TypeError, ValueError):
            pass

        try:
            total_absent += int(
                subject.get("absentLecture", 0)
            )
        except (TypeError, ValueError):
            pass

    total_classes = total_attended + total_absent

    if total_classes > 0:
        overall_percentage = round(
            (total_attended / total_classes) * 100,
            2
        )
    else:
        overall_percentage = 0

    attendance_data = {
        "subjects": subjects,
        "total_attended": total_attended,
        "total_absent": total_absent,
        "total_classes": total_classes,
        "overall_percentage": overall_percentage
    }

    session["attendance_data"] = attendance_data

    selected_leaves = {
        "2026-08-29": 0,
        "2026-10-10": 0,
        "2026-11-16": 0
    }
    save_user_leaves(selected_leaves)

    print()
    print("Website received:", len(subjects), "subjects")
    print("Portal attendance:", total_attended, "/", total_classes)
    print("Overall:", overall_percentage, "%")

    phase_1_result = run_phase_1(
        attendance_data,
        CHECKPOINT_CHOICES,
        selected_leaves
    )

    print()
    print(
        "Active checkpoint:",
        phase_1_result.get("active_checkpoint")
    )
    print(
        "Active index:",
        phase_1_result.get("active_checkpoint_index")
    )
    print(
        "Semester completed:",
        phase_1_result.get("semester_completed")
    )

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
    attendance_data = get_user_attendance()
    selected_leaves = get_user_leaves()

    leave_classes = get_requested_leave_classes(
        request.form,
        1
    )

    selected_leaves["2026-08-29"] = leave_classes
    save_user_leaves(selected_leaves)

    print()
    print("First Sessional:", leave_classes, "classes")

    phase_1_result = run_phase_1(
        attendance_data,
        CHECKPOINT_CHOICES,
        selected_leaves
    )

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
    attendance_data = get_user_attendance()
    selected_leaves = get_user_leaves()

    leave_classes = get_requested_leave_classes(
        request.form,
        2
    )

    selected_leaves["2026-10-10"] = leave_classes
    save_user_leaves(selected_leaves)

    print()
    print("Second Sessional:", leave_classes, "classes")

    phase_1_result = run_phase_1(
        attendance_data,
        CHECKPOINT_CHOICES,
        selected_leaves
    )

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
    attendance_data = get_user_attendance()
    selected_leaves = get_user_leaves()

    leave_classes = get_requested_leave_classes(
        request.form,
        3
    )

    selected_leaves["2026-11-16"] = leave_classes
    save_user_leaves(selected_leaves)

    print()
    print("Third Sessional:", leave_classes, "classes")

    phase_1_result = run_phase_1(
        attendance_data,
        CHECKPOINT_CHOICES,
        selected_leaves
    )

    return render_dashboard(
        attendance_data,
        phase_1_result,
        calculator_step=4
    )


# =========================================
# RESET / LOGOUT
# =========================================

@app.route("/reset")
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
