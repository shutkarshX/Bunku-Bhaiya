import os
from datetime import date, datetime, timedelta

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
from academic_calendar import TEACHING_CLASSES_PER_DAY, is_teaching_day

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

# ... existing app code remains unchanged below this point ...
