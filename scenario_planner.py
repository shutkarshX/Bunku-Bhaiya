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


def calculate_scenario(attendance_data, phase_1, scope="today", classes_missed=0, today_remaining_override=None):
    """Calculate TODAY or CHECKPOINT without changing saved attendance/planner state.

    ``today_remaining_override`` changes only the simulation's view of what is
    still physically happening today. Portal attendance that has not been posted
    yet remains untouched and will be picked up on the next attendance refresh.
    """
    scope = scope if scope in {"today", "checkpoint"} else "today"
    try:
        requested = max(0, int(classes_missed))
    except (TypeError, ValueError):
        requested = 0

    subjects = attendance_data.get("subjects") or []

    def metadata(key):
        try:
            return max(0, int(subjects[0].get(key, 0) or 0)) if subjects else 0
        except (TypeError, ValueError):
            return 0

    unmarked = metadata("_bunkmaster_unmarked_classes")
    portal_today_remaining = metadata("_bunkmaster_remaining_today")
    if today_remaining_override is None:
        today_remaining = portal_today_remaining
        override_active = False
    else:
        try:
            today_remaining = max(0, int(today_remaining_override))
        except (TypeError, ValueError):
            today_remaining = portal_today_remaining
        override_active = True

    attended = max(0, int(attendance_data.get("total_attended", 0))) + unmarked
    total = max(0, int(attendance_data.get("total_classes", 0))) + unmarked

    checkpoints = (phase_1 or {}).get("checkpoints") or []
    active_index = (phase_1 or {}).get("active_checkpoint_index")
    active = checkpoints[active_index] if isinstance(active_index, int) and 0 <= active_index < len(checkpoints) else None
    checkpoint_future = max(0, int(active.get("future_classes", 0) or 0)) if active else 0

    # The checkpoint engine includes the portal's estimate for today. Replace
    # that estimate for simulation only; do not modify attendance totals.
    checkpoint_future_adjusted = max(0, checkpoint_future - portal_today_remaining + today_remaining)

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
        "portal_today_remaining": portal_today_remaining,
        "today_remaining": today_remaining,
        "today_override_active": override_active,
        "checkpoint_name": active.get("name") if active else "Semester overview",
        "checkpoint_date": active.get("date", "") if active else "",
        "today": today_result,
        "checkpoint": checkpoint_result,
        "checkpoint_status": checkpoint_status,
        "remaining_safe_leave": remaining_safe_leave,
        "maximum_safe_leave": checkpoint_safe_leave,
    }
