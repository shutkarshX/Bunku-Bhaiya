"""Unified TEIN scenario calculations.

This module is simulation-only: it never mutates Flask session state.
"""

TARGET = 75.0


def _pct(attended, total):
    return round((attended / total) * 100, 2) if total else 0.0


def _status(attended, total, future):
    current = _pct(attended, total)
    if current >= TARGET:
        return "safe"
    maximum = _pct(attended + future, total + future)
    return "recovery" if maximum >= TARGET else "impossible"


def _max_safe_leave(attended, total, future):
    if _pct(attended, total) < TARGET:
        return 0
    safe = 0
    for missed in range(future + 1):
        if _pct(attended + future - missed, total + future) >= TARGET:
            safe = missed
        else:
            break
    return safe


def _project(attended, total, future, missed):
    missed = max(0, min(int(missed), future))
    projected_attended = attended + future - missed
    projected_total = total + future
    return {
        "attended": projected_attended,
        "total": projected_total,
        "percentage": _pct(projected_attended, projected_total),
        "missed": missed,
    }


def _int_value(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def calculate_scenario(
    attendance_data,
    phase_1,
    scope="today",
    classes_missed=0,
    today_remaining_override=None,
    event_mode=False,
    event_attended=0,
    planner_period_classes=None,
    planned_attended=0,
    planned_bunked=None,
):
    """Calculate a non-persistent attendance scenario or date-range plan."""
    scope = scope if scope in {"today", "checkpoint"} else "today"
    requested = max(0, _int_value(classes_missed))
    subjects = attendance_data.get("subjects") or []

    def metadata(key):
        return max(0, _int_value(subjects[0].get(key, 0))) if subjects else 0

    unmarked = metadata("_bunkmaster_unmarked_classes")
    portal_today_remaining = metadata("_bunkmaster_remaining_today")

    attended_event = max(0, _int_value(event_attended)) if event_mode else 0
    attended_event = min(attended_event, portal_today_remaining)

    if today_remaining_override is None:
        today_remaining = portal_today_remaining - attended_event
    else:
        today_remaining = max(0, _int_value(today_remaining_override, portal_today_remaining - attended_event))
    today_remaining = min(today_remaining, portal_today_remaining - attended_event)

    base_attended = max(0, _int_value(attendance_data.get("total_attended"))) + unmarked
    base_total = max(0, _int_value(attendance_data.get("total_classes"))) + unmarked
    attended = base_attended + attended_event
    total = base_total + attended_event

    checkpoints = (phase_1 or {}).get("checkpoints") or []
    active_index = (phase_1 or {}).get("active_checkpoint_index")
    active = checkpoints[active_index] if isinstance(active_index, int) and 0 <= active_index < len(checkpoints) else None
    checkpoint_future = max(0, _int_value(active.get("future_classes"))) if active else 0
    checkpoint_future_adjusted = max(0, checkpoint_future - portal_today_remaining + attended_event + today_remaining)

    # Date-range planner mode. The frontend supplies the number of scheduled
    # classes in the selected range and how many the student plans to attend.
    if planner_period_classes is not None:
        period_classes = max(0, _int_value(planner_period_classes))
        planned_attend = max(0, _int_value(planned_attended))
        planned_bunk = planned_attend if planned_bunked is None else max(0, _int_value(planned_bunked))
        available_after_event = max(0, period_classes - attended_event)
        planned_attend = min(planned_attend, available_after_event)
        planned_bunk = min(planned_bunk, max(0, available_after_event - planned_attend))

        projected_attended = attended + planned_attend
        projected_total = total + planned_attend + planned_bunk
        planner_pct = _pct(projected_attended, projected_total)
        current_pct = _pct(attended, total)
        return {
            "scope": "planner",
            "available_classes": available_after_event,
            "classes_missed": planned_bunk,
            "current_percentage": current_pct,
            "current_attended": attended,
            "current_total": total,
            "portal_today_remaining": portal_today_remaining,
            "today_remaining": today_remaining,
            "event_mode": bool(event_mode),
            "event_attended": attended_event,
            "today_override_active": today_remaining_override is not None,
            "planner_period_classes": period_classes,
            "planned_attended": planned_attend,
            "planned_bunked": planned_bunk,
            "planner_projected_attended": projected_attended,
            "planner_projected_total": projected_total,
            "planner_percentage": planner_pct,
            "planner_change": round(planner_pct - current_pct, 2),
            "planner_status": "safe" if planner_pct >= TARGET else "below_target",
            "checkpoint_name": active.get("name") if active else "Semester overview",
            "checkpoint_date": active.get("date", "") if active else "",
        }

    if scope == "today":
        available = today_remaining
        missed = min(requested, available)
        today_result = _project(attended, total, today_remaining, missed)
        checkpoint_result = _project(attended, total, checkpoint_future_adjusted, missed)
        checkpoint_status = _status(
            attended + max(0, today_remaining - missed),
            total + today_remaining,
            max(0, checkpoint_future_adjusted - today_remaining),
        )
    else:
        available = checkpoint_future_adjusted
        missed = min(requested, available)
        today_result = None
        checkpoint_result = _project(attended, total, checkpoint_future_adjusted, missed)
        checkpoint_status = _status(attended, total, max(0, checkpoint_future_adjusted - missed))

    checkpoint_safe_leave = _max_safe_leave(attended, total, checkpoint_future_adjusted)
    remaining_safe_leave = max(0, checkpoint_safe_leave - missed)

    return {
        "scope": scope,
        "available_classes": available,
        "classes_missed": missed,
        "current_percentage": _pct(attended, total),
        "current_attended": attended,
        "current_total": total,
        "portal_today_remaining": portal_today_remaining,
        "today_remaining": today_remaining,
        "event_mode": bool(event_mode),
        "event_attended": attended_event,
        "today_override_active": today_remaining_override is not None,
        "checkpoint_name": active.get("name") if active else "Semester overview",
        "checkpoint_date": active.get("date", "") if active else "",
        "today": today_result,
        "checkpoint": checkpoint_result,
        "checkpoint_status": checkpoint_status,
        "remaining_safe_leave": remaining_safe_leave,
        "maximum_safe_leave": checkpoint_safe_leave,
    }
