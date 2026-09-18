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


def get_checkpoint_targets():
    return session.get("checkpoint_targets", {})


def get_active_checkpoint_target():
    targets = get_checkpoint_targets()
    current_date = date.today()
    for index, (_, checkpoint_date) in enumerate(CHECKPOINTS):
        if current_date < checkpoint_date:
            key = checkpoint_date.strftime("%Y-%m-%d")
            return index, targets.get(key)
    return None, None


def save_checkpoint_target(index, value):
    try:
        target = float(value)
    except (TypeError, ValueError):
        return False
    if target < 1 or target > 100:
        return False
    key = CHECKPOINTS[index][1].strftime("%Y-%m-%d")
    targets = get_checkpoint_targets()
    targets[key] = target
    session["checkpoint_targets"] = targets
    session.modified = True
    return True


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


def build_checkpoint_tracker(phase_1_result=None, choice_made=False):
    current_date = date.today()

    if phase_1_result:
        checkpoints = phase_1_result.get("checkpoints", [])
        active_index = phase_1_result.get("active_checkpoint_index")
    else:
        active_index = next(
            (
                index
                for index, (_, checkpoint_date) in enumerate(CHECKPOINTS)
                if current_date < checkpoint_date
            ),
            None,
        )
        checkpoints = [
            {
                "checkpoint": checkpoint_name,
                "date": checkpoint_date.strftime("%d %B %Y"),
                "is_completed": current_date >= checkpoint_date,
            }
            for checkpoint_name, checkpoint_date in CHECKPOINTS
        ]

    cards = []

    for index, checkpoint in enumerate(checkpoints):
        if checkpoint.get("is_completed"):
            state_class = "passed"
            icon = "✓"
            label = "Passed"
        elif index == active_index:
            state_class = "current"
            icon = "●"
            label = "Current"
        else:
            state_class = "upcoming"
            icon = "○"
            label = "Upcoming"

        carry_forward = ""
        if (
            phase_1_result
            and choice_made
            and index == active_index
            and not checkpoint.get("is_completed")
        ):
            carry_forward = f"""
                <div class="checkpoint-projection">
                    <span>Your checkpoint attendance</span>
                    <strong>{checkpoint.get("requested_projected_percentage", 0):.2f}%</strong>
                    <small>
                        {checkpoint.get("requested_projected_attended", 0)}
                        /
                        {checkpoint.get("requested_projected_total", 0)}
                        classes
                    </small>
                    <em>This becomes the starting attendance for the next sessional.</em>
                </div>
            """

        cards.append(f"""
            <div class="checkpoint-item {state_class}">
                <div class="checkpoint-marker">{icon}</div>
                <div class="checkpoint-copy">
                    <strong>{checkpoint.get("checkpoint", "")}</strong>
                    <span>{label}</span>
                    {carry_forward}
                </div>
            </div>
        """)

    return f"""
        <style>
            .sessional-tracker {{
                position: fixed;
                top: 132px;
                right: max(24px, calc((100vw - 1180px) / 2));
                width: 270px;
                box-sizing: border-box;
                padding: 20px;
                border: 1px solid #e5e7eb;
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.97);
                box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
                z-index: 20;
            }}

            .sessional-tracker h3 {{
                margin: 0 0 18px;
                font-size: 17px;
            }}

            .checkpoint-item {{
                display: flex;
                gap: 11px;
                position: relative;
                padding-bottom: 18px;
            }}

            .checkpoint-item:not(:last-child)::after {{
                content: "";
                position: absolute;
                left: 8px;
                top: 21px;
                bottom: 0;
                width: 2px;
                background: #e5e7eb;
            }}

            .checkpoint-marker {{
                width: 18px;
                height: 18px;
                flex: 0 0 18px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 13px;
                font-weight: 800;
                position: relative;
                z-index: 1;
                background: #fff;
            }}

            .checkpoint-copy {{
                min-width: 0;
                display: flex;
                flex-direction: column;
                gap: 2px;
            }}

            .checkpoint-copy > strong {{
                font-size: 14px;
            }}

            .checkpoint-copy > span {{
                font-size: 12px;
                color: #6b7280;
            }}

            .checkpoint-item.passed .checkpoint-marker {{
                color: #15803d;
                border: 2px solid #22c55e;
            }}

            .checkpoint-item.current .checkpoint-marker {{
                color: #2563eb;
                border: 2px solid #3b82f6;
                background: #eff6ff;
            }}

            .checkpoint-item.current .checkpoint-copy > strong {{
                color: #1d4ed8;
            }}

            .checkpoint-item.upcoming .checkpoint-marker {{
                color: #9ca3af;
                border: 2px solid #d1d5db;
            }}

            .checkpoint-projection {{
                margin-top: 10px;
                padding: 12px;
                border-radius: 12px;
                background: #eff6ff;
                border: 1px solid #bfdbfe;
            }}

            .checkpoint-projection span,
            .checkpoint-projection small,
            .checkpoint-projection em {{
                display: block;
            }}

            .checkpoint-projection span {{
                font-size: 11px;
                color: #1e40af;
            }}

            .checkpoint-projection strong {{
                display: block;
                margin: 3px 0;
                font-size: 23px;
                color: #1d4ed8;
            }}

            .checkpoint-projection small {{
                font-size: 11px;
                color: #475569;
            }}

            .checkpoint-projection em {{
                margin-top: 7px;
                font-size: 10px;
                font-style: normal;
                color: #64748b;
            }}

            @media (min-width: 1050px) {{
                body:has(.sessional-tracker) .container {{
                    padding-right: 330px;
                    box-sizing: border-box;
                }}
            }}

            @media (max-width: 1049px) {{
                .sessional-tracker {{
                    position: static;
                    width: 100%;
                    margin: 0 0 24px;
                }}
            }}
        </style>

        <aside class="sessional-tracker" aria-label="Sessional checkpoint tracker">
            <h3>Sessional Checkpoints</h3>
            {''.join(cards)}
        </aside>
    """


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

    rendered = render_template(
        "dashboard.html",
        attendance=attendance,
        current_state=current_state,
        phase_1=phase_1,
        calculator_step=calculator_step,
        portal_error=portal_error,
        planner_loaded=session.get("planner_loaded", False),
        planner_choice_made=session.get("planner_choice_made", False),
        checkpoint_targets=get_checkpoint_targets(),
        active_checkpoint_target=get_active_checkpoint_target()[1],
        page=page,
    )

    if page == "planner" and (
        phase_1 is not None or session.get("planner_loaded", False)
    ):
        rendered = rendered.replace(
            "</body>",
            build_checkpoint_tracker(
                phase_1,
                session.get("planner_choice_made", False),
            ) + "</body>",
        )

    return rendered


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

    active_index, active_target = get_active_checkpoint_target()
    if active_index is not None and active_target is None:
        return render_dashboard(attendance_data, page="planner")

    phase_1_result = run_phase_1(
        attendance_data,
        get_user_leaves(),
        get_pending_event(),
        get_checkpoint_targets(),
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
    session["checkpoint_targets"] = {}
    session.pop("planner_event_checked", None)
    session.pop("pending_event", None)

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

    return redirect("/planner")


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

    active_index, active_target = get_active_checkpoint_target()
    if active_index is not None and active_target is None:
        return redirect("/planner")

    phase_1_result = run_phase_1(
        attendance_data,
        selected_leaves,
        get_pending_event(),
        get_checkpoint_targets(),
    )
    return render_dashboard(
        attendance_data,
        phase_1_result,
        calculator_step=checkpoint_index + 2,
        page="planner",
    )


@app.route("/event", methods=["POST"])
def save_event():
    """Save today's optional event as a planning-only pending attendance."""
    attendance_data = get_user_attendance()
    if not attendance_data.get("subjects") or not session.get("planner_loaded", False):
        return render_dashboard(attendance_data, portal_error="unavailable", page="planner")

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

    phase_1_result = run_phase_1(
        attendance_data,
        get_user_leaves(),
        get_pending_event(),
        get_checkpoint_targets(),
    )
    return render_dashboard(attendance_data, phase_1_result, page="planner")


@app.route("/checkpoint-target", methods=["POST"])
def checkpoint_target():
    attendance_data = get_user_attendance()
    if not attendance_data.get("subjects") or not session.get("planner_loaded", False):
        return redirect("/")

    active_index, _ = get_active_checkpoint_target()
    if active_index is None:
        return redirect("/planner")

    if not save_checkpoint_target(active_index, request.form.get("target_attendance")):
        return redirect("/planner")

    return redirect("/planner")


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
