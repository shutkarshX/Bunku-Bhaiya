import os

from flask import Blueprint, jsonify, render_template, request

from scenario_lab import run_lab

scenario_lab_bp = Blueprint("scenario_lab", __name__)


def enabled():
    return os.environ.get("TEIN_SCENARIO_LAB") == "1"


@scenario_lab_bp.route("/scenario-lab")
def page():
    if not enabled():
        return jsonify({"error": "scenario_lab_disabled"}), 404
    return render_template("scenario-lab.html")


@scenario_lab_bp.route("/scenario-lab/run", methods=["POST"])
def run():
    if not enabled():
        return jsonify({"error": "scenario_lab_disabled"}), 404
    payload = request.get_json(silent=True) or {}
    try:
        result = run_lab(
            payload.get("attended", 0),
            payload.get("total", 0),
            payload.get("scheduled_today", 0),
            payload.get("posted_today", 0),
            payload.get("actual_remaining_today", 0),
            payload.get("missed_today", 0),
            payload.get("checkpoint_future", 0),
        )
    except (TypeError, ValueError):
        return jsonify({"error": "invalid_scenario_values"}), 400
    return jsonify(result)
