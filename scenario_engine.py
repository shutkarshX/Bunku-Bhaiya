"""What-if attendance scenarios.

Every scenario starts from the effective attendance state as it exists right now.
If today's known event is still unposted, its planning-only attendance is applied
to that starting state and its classes are removed from today's remaining window.

Scenario calculations never modify the real portal attendance.
"""

from datetime import date

from attendance_state import build_attendance_state
from bunk_calculator import calculate_percentage, _get_pending_event_adjustment


def _get_remaining_today(attendance_data):
    subjects = attendance_data.get("subjects") or []
    if not subjects:
        return 0
    try:
        value = int(subjects[0].get("_bunkmaster_remaining_today", 0) or 0)
    except (TypeError, ValueError):
        value = 0
    return max(0, value)


def get_effective_starting_state(attendance_data, pending_event=None):
    """Build the effective state from which every what-if scenario starts."""
    state = build_attendance_state(attendance_data)

    effective_attended = state["effective"]["present"]
    effective_total = state["effective"]["total"]
    remaining_today = _get_remaining_today(attendance_data)

    event_classes = 0
    event_attended = 0
    if isinstance(pending_event, dict) and pending_event.get("date") == date.today().isoformat():
        event_classes, event_attended = _get_pending_event_adjustment(pending_event)
        remaining_today = max(0, remaining_today - event_classes)

    starting_attended = effective_attended + event_attended
    starting_total = effective_total + event_classes

    return {
        "attended": starting_attended,
        "total": starting_total,
        "percentage": round(calculate_percentage(starting_attended, starting_total), 2),
        "today_remaining": remaining_today,
        "event_classes": event_classes,
        "event_attended": event_attended,
    }


def calculate_today_scenario(attendance_data, pending_event=None, attended=0, leave=0):
    """Project today's effective attendance after a chosen attend/leave split."""
    starting = get_effective_starting_state(attendance_data, pending_event)

    try:
        attended = max(0, int(attended))
    except (TypeError, ValueError):
        attended = 0

    try:
        leave = max(0, int(leave))
    except (TypeError, ValueError):
        leave = 0

    requested = attended + leave
    remaining = starting["today_remaining"]

    if requested > remaining:
        return {
            "valid": False,
            "error": f"You can only plan {remaining} remaining class(es) today.",
            "starting": starting,
            "attended": attended,
            "leave": leave,
        }

    projected_attended = starting["attended"] + attended
    projected_total = starting["total"] + requested
    projected_percentage = round(
        calculate_percentage(projected_attended, projected_total),
        2,
    )

    return {
        "valid": True,
        "starting": starting,
        "attended": attended,
        "leave": leave,
        "planned_classes": requested,
        "projected_attended": projected_attended,
        "projected_total": projected_total,
        "projected_percentage": projected_percentage,
        "remaining_after_plan": remaining - requested,
    }
