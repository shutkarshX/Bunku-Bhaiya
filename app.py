import os
from datetime import date

from flask import Flask, redirect, render_template, request, session

from portal import (
    get_attendance,
    get_subject_details,
    load_subject_details,
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
from scenario_engine import calculate_today_scenario, get_effective_starting_state


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


def get_planner_target():
    return session.get("planner_target_attendance")


def save_planner_target(value):
    try:
        target = int(value)
    except (TypeError, ValueError):
        return False
    if target < 1 or target > 100:
        return False
    session["planner_target_attendance"] = target
    session.modified = True
    return True


def get_today_scenario_result():
    result = session.get("today_scenario_result")
    return result if isinstance(result, dict) else None


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


def build_checkpoint_tracker_data(phase_1_result=None, choice_made=False):
    current_date = date.today()

    if phase_1_result:
        source = phase_1_result.get("checkpoints", [])
        active_index = phase_1_result.get("active_checkpoint_index")
        return [
            {
                "checkpoint": item.get("checkpoint", ""),
                "state_class": (
                    "passed"
                    if item.get("is_completed")
                    else "current"
                    if index == active_index
                    else "upcoming"
                ),
                "icon": (
                    "✓"
                    if item.get("is_completed")
                    else "●"
                    if index == active_index
                    else "○"
                ),
                "label": (
                    "Passed"
                    if item.get("is_completed")
                    else "Current"
                    if index == active_index
                    else "Upcoming"
                ),
                "show_projection": (
                    choice_made
                    and index == active_index
                    and not item.get("is_completed")
                ),
                "projected_percentage": item.get("requested_projected_percentage", 0),
                "projected_attended": item.get("requested_projected_attended", 0),
                "projected_total": item.get("requested_projected_total", 0),
            }
            for index, item in enumerate(source)
        ]

    active_index = next(
        (
            index
            for index, (_, checkpoint_date) in enumerate(CHECKPOINTS)
            if current_date < checkpoint_date
        ),
        None,
    )
    return [
        {
            "checkpoint": checkpoint_name,
            "state_class": (
                "passed"
                if current_date >= checkpoint_date
                else "current"
                if index == active_index
                else "upcoming"
            ),
            "icon": (
                "✓"
                if current_date >= checkpoint_date
                else "●"
                if index == active_index
                else "○"
            ),
            "label": (
                "Passed"
                if current_date >= checkpoint_date
                else "Current"
                if index == active_index
                else "Upcoming"
            ),
            "show_projection": False,
            "projected_percentage": 0,
            "projected_attended": 0,
            "projected_total": 0,
        }
        for index, (checkpoint_name, checkpoint_date) in enumerate(CHECKPOINTS)
    ]


def render_dashboard(
    attendance_data,
    phase_1=None,
    portal_error=None,
    calculator_step=None,
    page="home",
):
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
        planner_choice_made=session.get("planner_choice_made", False),
        planner_target_attendance=get_planner_target(),
        planner_target_required=get_planner_target() is None,
        today_scenario=get_today_scenario_result(),
        today_scenario_start=get_effective_starting_state(attendance, get_pending_event()),
        tracker_checkpoints=build_checkpoint_tracker_data(
            phase_1,
            session.get("planner_choice_made", False),
        ),
        page=page,
        scenario=request.args.get("scenario") if page == "what_if" else None,
    )


@app.route("/")
def dashboard():
    attendance_data = get_user_attendance()
    return render_dashboard(attendance_data, page="home")


@app.route("/planner")
def planner_page():
    """Show the attendance planner without re-fetching portal data."""
    attendance_data = get_user_attendance()
    if not attendance_data.get("subjects"):
        return render_dashboard(attendance_data, page="home")

    if not session.get("planner_loaded", False):
        return render_dashboard(attendance_data, page="planner")

    # The event decision must happen before checkpoint calculations.
    if not session.get("planner_event_checked", False):
        return render_dashboard(attendance_data, page="planner")

    if get_planner_target() is None:
        return render_dashboard(attendance_data, page="planner")

    phase_1_result = run_phase_1(
        attendance_data,
        get_user_leaves(),
        get_pending_event(),
        get_planner_target(),
    )
    return render_dashboard(attendance_data, phase_1_result, page="planner")


@app.route("/subjects")
def subjects_page():
    """Show subject-wise attendance using the shared server-side cache."""
    attendance_data = get_user_attendance()
    if not attendance_data.get("subjects"):
        return render_dashboard(attendance_data, page="home")

    token = get_planner_token(attendance_data)
    try:
        load_subject_details(token)
    except PortalUnavailableError as e:
        print("\nSubject attendance load failed\n", e)
        return render_dashboard(
            attendance_data,
            portal_error="unavailable",
            page="subjects",
        )

    return render_dashboard(attendance_data, page="subjects")


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
    save_user_leaves(dict(DEFAULT_SELECTED_LEAVES))
    session["planner_loaded"] = False
    session["planner_choice_made"] = False
    session.pop("planner_target_attendance", None)
    session.pop("planner_event_checked", None)
    session.pop("pending_event", None)
    session.pop("today_scenario_result", None)

    print("Website received:", len(subjects), "subjects")
    print("Portal attendance:", state["portal"]["present"], "/", state["portal"]["total"])
    print("Portal:", state["portal"]["percentage"], "%")
    print("Site:", state["site"]["percentage"], "%")
    print("Effective:", state["effective"]["percentage"], "%")
    print("Planner data is deferred until the user opens the planner.")

    return render_dashboard(attendance_data)


@app.route("/load-planner", methods=["POST"])
def load_planner():
    """Load expensive subject-wise data only when planning is requested."""
    attendance_data = get_user_attendance()
    token = get_planner_token(attendance_data)

    if not token:
        return render_dashboard(
            attendance_data,
            portal_error="unavailable",
            page="planner",
        )

    try:
        today_logged, remaining_today = get_today_attendance(token)
    except PortalUnavailableError as e:
        print("\nDeferred planner load failed\n", e)
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
        session["planner_choice_made"] = False
        session.pop("planner_event_checked", None)
        session.pop("pending_event", None)

        if remaining_today <= 0:
            session["planner_event_checked"] = True

        session.modified = True

    return redirect(request.form.get("next", "/planner"))


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
    session["planner_choice_made"] = True
    session.modified = True

    next_index = checkpoint_index + 1
    if next_index < len(CHECKPOINTS):
        return redirect("/what-if?scenario=sessional")

    phase_1_result = run_phase_1(
        attendance_data,
        selected_leaves,
        get_pending_event(),
        get_planner_target(),
    )
    return render_dashboard(
        attendance_data,
        phase_1_result,
        calculator_step=checkpoint_index + 2,
        page="what_if",
    )


@app.route("/event", methods=["POST"])
def save_event():
    """Save today's optional event as a planning-only pending attendance."""
    attendance_data = get_user_attendance()
    if not attendance_data.get("subjects") or not session.get("planner_loaded", False):
        return render_dashboard(attendance_data, portal_error="unavailable", page="planner")

    action = request.form.get("event_action")
    if action == "none":
        # Explicitly record the user's "No event today" decision.
        save_user_event(None)
        session["planner_event_checked"] = True
        session.modified = True
        return redirect("/planner")
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

        classes = min(max(0, classes), max(0, today_remaining))
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

    # Redirect after the event decision so the planner route becomes the
    # single source of truth for the next screen/state.
    return redirect(request.form.get("return_to", "/planner"))


@app.route("/planner-target", methods=["POST"])
def planner_target():
    attendance_data = get_user_attendance()
    if not attendance_data.get("subjects") or not session.get("planner_loaded", False):
        return redirect("/")

    if not save_planner_target(request.form.get("target_attendance")):
        return redirect("/planner")

    return redirect(request.form.get("return_to", "/planner"))


@app.route("/scenario/today", methods=["POST"])
def today_scenario():
    """Calculate a planning-only projection for today's remaining classes."""
    attendance_data = get_user_attendance()
    if not attendance_data.get("subjects") or not session.get("planner_loaded", False):
        return redirect("/planner")

    if not session.get("planner_event_checked", False):
        return redirect("/planner")

    result = calculate_today_scenario(
        attendance_data,
        get_pending_event(),
        request.form.get("attended", 0),
        request.form.get("leave", 0),
    )
    session["today_scenario_result"] = result
    session.modified = True
    return redirect(request.form.get("return_to", "/planner"))


@app.route("/what-if")
def what_if_page():
    """Show all What-If scenarios together on one page."""
    attendance_data = get_user_attendance()
    if not attendance_data.get("subjects"):
        return render_dashboard(attendance_data, page="home")

    phase_1_result = None
    if (
        session.get("planner_loaded", False)
        and session.get("planner_event_checked", False)
        and get_planner_target() is not None
    ):
        phase_1_result = run_phase_1(
            attendance_data,
            get_user_leaves(),
            get_pending_event(),
            get_planner_target(),
        )

    return render_dashboard(
        attendance_data,
        phase_1_result,
        page="what_if",
    )


@app.route("/what-if/today")
def today_scenario_page():
    """Compatibility route for the Today scenario."""
    return redirect("/what-if")


@app.route("/sessional")
def sessional_scenario_page():
    """Compatibility route for the Sessional scenario."""
    return redirect("/what-if")


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
    return render_dashboard(empty_attendance(), page="home")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )
