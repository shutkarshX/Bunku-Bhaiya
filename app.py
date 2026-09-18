import os

from flask import Flask, render_template, request, session

from portal import (
    get_attendance,
    get_subject_details,
    PortalUnavailableError,
    PortalLoginError,
)
from bunk_calculator import (
    run_phase_1,
    classes_to_leave_display,
    days_and_classes_to_classes,
)
from academic_calendar import CHECKPOINTS
from attendance_state import build_attendance_state


app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set. "
        "Please configure it before running BunkMaster."
    )
app.secret_key = SECRET_KEY

app.jinja_env.globals["classes_to_leave_display"] = classes_to_leave_display

DEFAULT_SELECTED_LEAVES = {checkpoint: 0 for checkpoint in CHECKPOINTS}


def empty_attendance():
    return {
        "subjects": [],
        "total_attended": 0,
        "total_absent": 0,
        "total_classes": 0,
        "overall_percentage": 0,
    }


def get_user_attendance():
    return session.get("attendance_data", empty_attendance())


def get_user_leaves():
    return session.get("selected_leaves", dict(DEFAULT_SELECTED_LEAVES))


def save_user_leaves(leaves):
    session["selected_leaves"] = leaves
    session.modified = True


def get_dashboard_step(phase_1_result):
    active_index = phase_1_result.get("active_checkpoint_index")
    if active_index is None:
        return 4
    return active_index + 1


def get_requested_leave_classes(form, step):
    try:
        days = int(form.get(f"leave_{step}_days", 0))
    except (TypeError, ValueError):
        days = 0
    try:
        classes = int(form.get(f"leave_{step}_classes", 0))
    except (TypeError, ValueError):
        classes = 0
    return days_and_classes_to_classes(days, classes)


def render_dashboard(attendance_data, phase_1=None, portal_error=None, calculator_step=None):
    if phase_1 is None:
        calculator_step = 0
    elif calculator_step is None:
        calculator_step = get_dashboard_step(phase_1)

    attendance = dict(attendance_data)
    subjects = attendance.get("subjects") or []
    token = subjects[0].get("_bunkmaster_subject_details_token") if subjects else None
    attendance["subject_details"] = get_subject_details(token)

    return render_template(
        "dashboard.html",
        attendance=attendance,
        phase_1=phase_1,
        calculator_step=calculator_step,
        portal_error=portal_error,
    )


@app.route("/")
def dashboard():
    attendance_data = get_user_attendance()
    if not attendance_data["subjects"]:
        return render_dashboard(attendance_data)

    phase_1_result = run_phase_1(
        attendance_data,
        get_user_leaves(),
    )
    return render_dashboard(attendance_data, phase_1_result)


@app.route("/get-attendance", methods=["POST"])
def get_attendance_page():
    username = request.form.get("username")
    password = request.form.get("password")

    print("\nStarting attendance retrieval...")

    try:
        subjects = get_attendance(username, password)
    except PortalUnavailableError as e:
        print("\nNIET PORTAL UNAVAILABLE\n", e)
        return render_dashboard(empty_attendance(), portal_error="unavailable")
    except PortalLoginError as e:
        print("\nNIET LOGIN FAILED\n", e)
        return render_dashboard(empty_attendance(), portal_error="login")
    except Exception as e:
        print("\nUnexpected portal error:\n", e)
        return render_dashboard(empty_attendance(), portal_error="unavailable")

    if not subjects:
        print("No attendance data was returned.")
        return render_dashboard(empty_attendance(), portal_error="unavailable")

    state = build_attendance_state({"subjects": subjects})
    attendance_data = {
        "subjects": subjects,
        "total_attended": state["portal"]["present"],
        "total_absent": state["portal"]["absent"],
        "total_classes": state["portal"]["total"],
        "overall_percentage": state["portal"]["percentage"],
    }

    session["attendance_data"] = attendance_data
    selected_leaves = dict(DEFAULT_SELECTED_LEAVES)
    save_user_leaves(selected_leaves)

    print("Website received:", len(subjects), "subjects")
    print("Portal attendance:", state["portal"]["present"], "/", state["portal"]["total"])
    print("Portal:", state["portal"]["percentage"], "%")
    print("Site:", state["site"]["percentage"], "%")
    print("Effective:", state["effective"]["percentage"], "%")

    phase_1_result = run_phase_1(
        attendance_data,
        selected_leaves,
    )

    print("Active checkpoint:", phase_1_result.get("active_checkpoint"))
    print("Active index:", phase_1_result.get("active_checkpoint_index"))
    print("Semester completed:", phase_1_result.get("semester_completed"))

    return render_dashboard(attendance_data, phase_1_result)


def handle_checkpoint_submission(checkpoint_index):
    """Apply one checkpoint leave submission using the shared checkpoint flow."""
    attendance_data = get_user_attendance()
    selected_leaves = get_user_leaves()
    form_step = checkpoint_index + 1
    checkpoint_key = CHECKPOINTS[checkpoint_index]

    selected_leaves[checkpoint_key] = get_requested_leave_classes(
        request.form,
        form_step,
    )
    save_user_leaves(selected_leaves)

    phase_1_result = run_phase_1(attendance_data, selected_leaves)
    return render_dashboard(
        attendance_data,
        phase_1_result,
        calculator_step=checkpoint_index + 2,
    )


@app.route("/sessional-1", methods=["POST"])
def sessional_1():
    return handle_checkpoint_submission(0)


@app.route("/sessional-2", methods=["POST"])
def sessional_2():
    return handle_checkpoint_submission(1)


@app.route("/sessional-3", methods=["POST"])
def sessional_3():
    return handle_checkpoint_submission(2)

@app.route("/reset")
def reset_session():
    session.clear()
    return render_dashboard(empty_attendance())


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )
