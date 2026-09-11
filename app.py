import os

from flask import Flask, render_template, request, session, redirect, send_from_directory, jsonify

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
from scenario_planner import calculate_scenario

app = Flask(__name__)
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set. Please configure it before running BunkMaster.")
app.secret_key = SECRET_KEY
app.jinja_env.globals["classes_to_leave_display"] = classes_to_leave_display

CHECKPOINT_CHOICES = {
    "2026-08-29": True,
    "2026-10-10": True,
    "2026-11-16": True,
}


def empty_attendance():
    return {"subjects": [], "total_attended": 0, "total_absent": 0, "total_classes": 0, "overall_percentage": 0}


def get_user_attendance():
    return session.get("attendance_data", empty_attendance())


def get_user_leaves():
    return session.get("selected_leaves", {"2026-08-29": 0, "2026-10-10": 0, "2026-11-16": 0})


def save_user_leaves(leaves):
    session["selected_leaves"] = leaves
    session.modified = True


def get_dashboard_step(phase_1_result):
    active_index = phase_1_result.get("active_checkpoint_index")
    if active_index is None:
        return 4
    calendar_step = active_index + 1
    planner_step = session.get("planner_step", 0)
    if not isinstance(planner_step, int):
        planner_step = 0
    return min(4, max(calendar_step, planner_step))


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


def render_dashboard(attendance_data, phase_1=None, portal_error=None, calculator_step=None, initial_view="home"):
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
        initial_view=initial_view,
    )


@app.route("/sw.js")
def service_worker():
    return send_from_directory("static", "tein-sw.js", mimetype="application/javascript")


@app.route("/")
def dashboard():
    attendance_data = get_user_attendance()
    if not attendance_data["subjects"]:
        return render_dashboard(attendance_data)
    selected_leaves = get_user_leaves()
    phase_1_result = run_phase_1(attendance_data, CHECKPOINT_CHOICES, selected_leaves)
    requested_view = request.args.get("view", "home")
    initial_view = requested_view if requested_view in {"home", "plan", "subjects", "more"} else "home"
    return render_dashboard(attendance_data, phase_1_result, initial_view=initial_view)


@app.route("/scenario", methods=["POST"])
def scenario():
    """Return a non-persistent Today/Checkpoint attendance simulation."""
    attendance_data = get_user_attendance()
    if not attendance_data.get("subjects"):
        return jsonify({"error": "attendance_required"}), 400

    selected_leaves = get_user_leaves()
    phase_1_result = run_phase_1(attendance_data, CHECKPOINT_CHOICES, selected_leaves)
    payload = request.get_json(silent=True) or request.form
    scope = payload.get("scope", "today")
    classes_missed = payload.get("classes_missed", 0)
    return jsonify(calculate_scenario(attendance_data, phase_1_result, scope, classes_missed))


@app.route("/get-attendance", methods=["POST"])
def get_attendance_page():
    username = request.form.get("username")
    password = request.form.get("password")
    print("\nStarting attendance retrieval...")
    try:
        subjects = get_attendance(username, password)
    except PortalUnavailableError as e:
        print("NIET PORTAL UNAVAILABLE", e)
        return render_dashboard(empty_attendance(), portal_error="unavailable")
    except PortalLoginError as e:
        print("NIET LOGIN FAILED", e)
        return render_dashboard(empty_attendance(), portal_error="login")
    except Exception as e:
        print("Unexpected portal error:", e)
        return render_dashboard(empty_attendance(), portal_error="unavailable")
    if not subjects:
        return render_dashboard(empty_attendance(), portal_error="unavailable")

    total_attended = 0
    total_absent = 0
    for subject in subjects:
        try:
            total_attended += int(subject.get("attendedLecture", 0))
        except (TypeError, ValueError):
            pass
        try:
            total_absent += int(subject.get("absentLecture", 0))
        except (TypeError, ValueError):
            pass

    total_classes = total_attended + total_absent
    overall_percentage = round((total_attended / total_classes) * 100, 2) if total_classes > 0 else 0
    attendance_data = {
        "subjects": subjects,
        "total_attended": total_attended,
        "total_absent": total_absent,
        "total_classes": total_classes,
        "overall_percentage": overall_percentage,
    }
    session["attendance_data"] = attendance_data
    selected_leaves = {"2026-08-29": 0, "2026-10-10": 0, "2026-11-16": 0}
    save_user_leaves(selected_leaves)
    session["planner_step"] = 0
    phase_1_result = run_phase_1(attendance_data, CHECKPOINT_CHOICES, selected_leaves)
    print("Website received:", len(subjects), "subjects")
    print("Portal attendance:", total_attended, "/", total_classes)
    print("Overall:", overall_percentage, "%")
    return render_dashboard(attendance_data, phase_1_result)


@app.route("/sessional-1", methods=["POST"])
def sessional_1():
    attendance_data = get_user_attendance()
    selected_leaves = get_user_leaves()
    selected_leaves["2026-08-29"] = get_requested_leave_classes(request.form, 1)
    save_user_leaves(selected_leaves)
    session["planner_step"] = max(2, session.get("planner_step", 0))
    return redirect("/?view=plan")


@app.route("/sessional-2", methods=["POST"])
def sessional_2():
    attendance_data = get_user_attendance()
    selected_leaves = get_user_leaves()
    selected_leaves["2026-10-10"] = get_requested_leave_classes(request.form, 2)
    save_user_leaves(selected_leaves)
    session["planner_step"] = max(3, session.get("planner_step", 0))
    return redirect("/?view=plan")


@app.route("/sessional-3", methods=["POST"])
def sessional_3():
    attendance_data = get_user_attendance()
    selected_leaves = get_user_leaves()
    selected_leaves["2026-11-16"] = get_requested_leave_classes(request.form, 3)
    save_user_leaves(selected_leaves)
    session["planner_step"] = 4
    return redirect("/?view=plan")


@app.route("/reset")
def reset_session():
    session.clear()
    return render_dashboard(empty_attendance())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
