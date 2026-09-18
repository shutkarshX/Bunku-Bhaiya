import os
from datetime import date

from flask import Flask, render_template, request, session

from portal import (
    get_attendance,
    get_subject_details,
    get_today_attendance,
    PortalUnavailableError,
    PortalLoginError,
)
from bunk_calculator import (
    run_phase_1,
    classes_to_leave_display,
    days_and_classes_to_classes,
    CHECKPOINTS,
)
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

CHECKPOINT_KEYS = tuple(
    checkpoint_date.strftime("%Y-%m-%d")
    for _, checkpoint_date in CHECKPOINTS
)
DEFAULT_SELECTED_LEAVES = {checkpoint: 0 for checkpoint in CHECKPOINT_KEYS}


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


def get_pending_event():
    event = session.get("pending_event")
    return event if isinstance(event, dict) else None


def save_user_event(event):
    if event is None:
        session.pop("pending_event", None)
    else:
        session["pending_event"] = event
    session.modified = True


def save_user_leaves(leaves):
    session["selected_leaves"] = leaves
    session.modified = True


def get_planner_token(attendance_data):
    subjects = attendance_data.get("subjects") or []
    if not subjects:
        return None
    return subjects[0].get("_bunkmaster_subject_details_token")


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
    token = get_planner_token(attendance)
    attendance["subject_details"] = get_subject_details(token)
    current_state = build_attendance_state(attendance)

    return render_template(
        "dashboard.html",
        attendance=attendance,
        current_state=current_state,
        phase_1=phase_1,
        calculator_step=calculator_step,
        portal_error=portal_error,
        planner_loaded=session.get("planner_loaded", False),
    )


@app.route("/")
def dashboard():
    attendance_data = get_user_attendance()
    if not attendance_data["subjects"]:
        return render_dashboard(attendance_data)

    if not session.get("planner_loaded", False):
        return render_dashboard(attendance_data)

    phase_1_result = run_phase_1(
        attendance_data,
        get_user_leaves(),
        get_pending_event(),
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
    session["planner_loaded"] = False
    session.pop("planner_event_checked", None)
    session.pop("pending_event", None)

    print("Website received:", len(subjects), "subjects")
    print("Portal attendance:", state["portal"]["present"], "/", state["portal"]["total"])
    print("Portal:", state["portal"]["percentage"], "%")
    print("Site:", state["site"]["percentage"], "%")
    print("Effective:", state["effective"]["percentage"], "%")

    # The initial login intentionally does not fetch subject-wise attendance
    # history. That expensive request is deferred until the planner is opened.
    phase_1_result = None

    print("Planner data is deferred until the user opens the planner.")

    return render_dashboard(attendance_data, phase_1_result)


@app.route("/load-planner", methods=["POST"])
def load_planner():
    """Load expensive subject-wise data only when planning is requested."""
    attendance_data = get_user_attendance()
    token = get_planner_token(attendance_data)

    if not token:
        return render_dashboard(
            attendance_data,
            portal_error="unavailable",
        )

    try:
        today_logged, remaining_today = get_today_attendance(token)
    except PortalUnavailableError as e:
        print("\\nDeferred planner load failed\\n", e)
        return render_dashboard(
            attendance_data,
            portal_error="unavailable",
        )

    subjects = attendance_data.get("subjects") or []
    if subjects:
        subjects[0]["_bunkmaster_today_logged"] = today_logged
        subjects[0]["_bunkmaster_remaining_today"] = remaining_today
        attendance_data["subjects"] = subjects
        session["attendance_data"] = attendance_data
        session["planner_loaded"] = True
        session.pop("planner_event_checked", None)
        session.pop("pending_event", None)
        session.modified = True

    if not session.get("planner_event_checked", False):
        return render_dashboard(attendance_data)

    phase_1_result = run_phase_1(
        attendance_data,
        get_user_leaves(),
        get_pending_event(),
    )
    return render_dashboard(attendance_data, phase_1_result)


def handle_checkpoint_submission(checkpoint_index):
    """Apply one checkpoint leave submission using the shared checkpoint flow."""
    attendance_data = get_user_attendance()
    selected_leaves = get_user_leaves()
    form_step = checkpoint_index + 1
    checkpoint_key = CHECKPOINTS[checkpoint_index][1].strftime("%Y-%m-%d")

    selected_leaves[checkpoint_key] = get_requested_leave_classes(
        request.form,
        form_step,
    )
    save_user_leaves(selected_leaves)

    phase_1_result = run_phase_1(
        attendance_data,
        selected_leaves,
        get_pending_event(),
    )
    return render_dashboard(
        attendance_data,
        phase_1_result,
        calculator_step=checkpoint_index + 2,
    )




@app.route("/event", methods=["POST"])
def save_event():
    """Save today's optional event as a planning-only pending attendance."""
    attendance_data = get_user_attendance()
    if not attendance_data.get("subjects") or not session.get("planner_loaded", False):
        return render_dashboard(attendance_data, portal_error="unavailable")

    action = request.form.get("event_action")
    if action == "none":
        save_user_event(None)
    elif action == "save":
        try:
            classes = int(request.form.get("event_classes", 0) or 0)
        except (TypeError, ValueError):
            classes = 0

        today_remaining = 0
        subjects = attendance_data.get("subjects") or []
        if subjects:
            try:
                today_remaining = int(
                    subjects[0].get("_bunkmaster_remaining_today", 0) or 0
                )
            except (TypeError, ValueError):
                today_remaining = 0

        classes = max(1, min(classes, today_remaining))
        attended = request.form.get("event_attended") == "yes"

        if classes <= 0:
            save_user_event(None)
        else:
            save_user_event({
                "date": date.today().isoformat(),
                "classes": classes,
                "attended": attended,
            })
    else:
        return render_dashboard(attendance_data, portal_error="unavailable")

    session["planner_event_checked"] = True
    session.modified = True

    phase_1_result = run_phase_1(
        attendance_data,
        get_user_leaves(),
        get_pending_event(),
    )
    return render_dashboard(attendance_data, phase_1_result)


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
