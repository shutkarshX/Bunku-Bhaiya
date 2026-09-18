from datetime import date, timedelta
import math

from academic_calendar import (
    TEACHING_CLASSES_PER_DAY,
    ATTENDANCE_TARGET,
    CHECKPOINTS as CHECKPOINT_DEFINITIONS,
    is_teaching_day,
)
from attendance_state import build_attendance_state


CLASSES_PER_DAY = TEACHING_CLASSES_PER_DAY
TARGET_ATTENDANCE = ATTENDANCE_TARGET
CHECKPOINTS = tuple(
    (name, date.fromisoformat(date_key))
    for name, date_key in CHECKPOINT_DEFINITIONS
)


def calculate_percentage(attended, total):
    if total == 0:
        return 0
    return (attended / total) * 100


def classes_needed_to_reach_target(attended, total_classes, target_attendance=TARGET_ATTENDANCE):
    if total_classes == 0:
        return 0
    if calculate_percentage(attended, total_classes) >= target_attendance:
        return 0
    required_classes = math.ceil(
        ((target_attendance / 100) * total_classes - attended)
        / (1 - (TARGET_ATTENDANCE / 100))
    )
    return max(0, required_classes)


def days_and_classes_to_classes(days=0, classes=0):
    try:
        days = int(days)
    except (TypeError, ValueError):
        days = 0
    try:
        classes = int(classes)
    except (TypeError, ValueError):
        classes = 0
    return max(0, days) * CLASSES_PER_DAY + max(0, classes)


def classes_to_leave_display(total_classes):
    try:
        total_classes = int(total_classes)
    except (TypeError, ValueError):
        total_classes = 0
    days, remaining_classes = divmod(max(0, total_classes), CLASSES_PER_DAY)
    if days == 0:
        return f"{remaining_classes} class(es)"
    if remaining_classes == 0:
        return f"{days} day(s)"
    return f"{days} day(s) {remaining_classes} class(es)"


def count_teaching_days(start_date, end_date):
    if start_date > end_date:
        return 0
    count = 0
    current = start_date
    while current <= end_date:
        if is_teaching_day(current.strftime("%Y-%m-%d")):
            count += 1
        current += timedelta(days=1)
    return count


def find_maximum_safe_leave(attended, total_classes, future_classes, target_attendance=TARGET_ATTENDANCE):
    if calculate_percentage(attended, total_classes) < target_attendance:
        return 0
    maximum_leave_classes = 0
    for missed_classes in range(future_classes + 1):
        future_attended = future_classes - missed_classes
        final_attended = attended + future_attended
        final_total = total_classes + future_classes
        if calculate_percentage(final_attended, final_total) >= target_attendance:
            maximum_leave_classes = missed_classes
        else:
            break
    return maximum_leave_classes


def calculate_requested_leave(
    attended,
    total_classes,
    future_classes,
    requested_days,
    requested_classes,
    maximum_safe_classes,
):
    requested_classes_total = days_and_classes_to_classes(requested_days, requested_classes)
    requested_classes_total = min(
        requested_classes_total,
        max(0, future_classes),
        max(0, maximum_safe_classes),
    )
    future_attended = future_classes - requested_classes_total
    projected_attended = attended + future_attended
    projected_total = total_classes + future_classes
    projected_percentage = calculate_percentage(projected_attended, projected_total)
    return {
        "requested_leave_classes": requested_classes_total,
        "requested_leave": requested_classes_total,
        "requested_classes_missed": requested_classes_total,
        "projected_attended": projected_attended,
        "projected_total": projected_total,
        "projected_percentage": round(projected_percentage, 2),
    }


def determine_status(attended, total_classes, future_classes, target_attendance=TARGET_ATTENDANCE):
    if calculate_percentage(attended, total_classes) >= target_attendance:
        return "safe"
    maximum_attended = attended + future_classes
    maximum_total = total_classes + future_classes
    maximum_possible_percentage = calculate_percentage(maximum_attended, maximum_total)
    if maximum_possible_percentage >= target_attendance:
        return "recovery"
    return "impossible"


def get_checkpoint_state(checkpoint_date, current_date):
    return "completed" if current_date >= checkpoint_date else "upcoming"


def get_active_checkpoint_index(current_date):
    for index, (_, checkpoint_date) in enumerate(CHECKPOINTS):
        if current_date < checkpoint_date:
            return index
    return None


def _completed_checkpoint(checkpoint_name, checkpoint_date, actual_attended, actual_total):
    current_percentage = calculate_percentage(actual_attended, actual_total)
    checkpoint_key = checkpoint_date.strftime("%Y-%m-%d")
    return {
        "checkpoint": checkpoint_name,
        "date": checkpoint_date.strftime("%d %B %Y"),
        "date_key": checkpoint_key,
        "is_teaching_day": is_teaching_day(checkpoint_key),
        "included": True,
        "state": "completed",
        "is_completed": True,
        "is_active": False,
        "is_upcoming": False,
        "status": determine_status(actual_attended, actual_total, 0),
        "starting_attended": actual_attended,
        "starting_total": actual_total,
        "starting_percentage": round(current_percentage, 2),
        "teaching_days": 0,
        "future_classes": 0,
        "maximum_leave": 0,
        "maximum_leave_classes": 0,
        "maximum_leave_days": 0,
        "maximum_leave_remaining_classes": 0,
        "maximum_leave_display": "0 class(es)",
        "classes_needed_for_75": classes_needed_to_reach_target(actual_attended, actual_total),
        "maximum_possible_percentage": round(current_percentage, 2),
        "projected_without_leave": round(current_percentage, 2),
        "requested_leave": 0,
        "requested_leave_classes": 0,
        "requested_leave_days": 0,
        "requested_leave_remaining_classes": 0,
        "requested_leave_display": "0 class(es)",
        "requested_classes_missed": 0,
        "requested_projected_attended": actual_attended,
        "requested_projected_total": actual_total,
        "requested_projected_percentage": round(current_percentage, 2),
        "requested_leave_is_safe": True,
        "remaining_safe_leave": 0,
        "remaining_safe_leave_classes": 0,
        "remaining_safe_leave_days": 0,
        "remaining_safe_leave_remaining_classes": 0,
        "remaining_safe_leave_display": "0 class(es)",
        "final_attended": actual_attended,
        "final_total": actual_total,
        "final_percentage": round(current_percentage, 2),
        "classes_missed": 0,
    }


def _future_checkpoint(
    checkpoint_name,
    checkpoint_date,
    index,
    active_index,
    current_date,
    actual_attended,
    actual_total,
    requested_leaves,
    remaining_today,
    target_attendance=TARGET_ATTENDANCE,
):
    checkpoint_key = checkpoint_date.strftime("%Y-%m-%d")
    if index == active_index:
        calculation_start = current_date + timedelta(days=1)
    else:
        calculation_start = CHECKPOINTS[index - 1][1] + timedelta(days=1)
    checkpoint_is_teaching_day = is_teaching_day(checkpoint_key)
    calculation_end = checkpoint_date if checkpoint_is_teaching_day else checkpoint_date - timedelta(days=1)
    teaching_days = count_teaching_days(calculation_start, calculation_end)
    future_classes = teaching_days * CLASSES_PER_DAY

    # Today's remaining classes have not happened yet, but they belong to the
    # active checkpoint's planning window and must be included before any
    # leave/safety calculations are made.
    if index == active_index:
        future_classes += remaining_today

    starting_percentage = calculate_percentage(actual_attended, actual_total)
    status = determine_status(actual_attended, actual_total, future_classes, target_attendance)
    classes_needed = classes_needed_to_reach_target(actual_attended, actual_total, target_attendance)
    maximum_attended_if_no_leave = actual_attended + future_classes
    maximum_total_if_no_leave = actual_total + future_classes
    maximum_possible_percentage = calculate_percentage(maximum_attended_if_no_leave, maximum_total_if_no_leave)
    maximum_leave_classes = find_maximum_safe_leave(actual_attended, actual_total, future_classes, target_attendance)
    maximum_leave_days, maximum_leave_remaining_classes = divmod(maximum_leave_classes, CLASSES_PER_DAY)

    raw_requested = requested_leaves.get(checkpoint_key, 0)
    if isinstance(raw_requested, dict):
        requested_days = raw_requested.get("days", 0)
        requested_classes = raw_requested.get("classes", 0)
    else:
        requested_days = 0
        requested_classes = raw_requested

    requested_result = calculate_requested_leave(
        actual_attended,
        actual_total,
        future_classes,
        requested_days,
        requested_classes,
        maximum_leave_classes,
    )
    requested_leave_classes = requested_result["requested_leave_classes"]
    requested_leave_days, requested_leave_remaining_classes = divmod(requested_leave_classes, CLASSES_PER_DAY)
    requested_leave_is_safe = (
        requested_leave_classes <= maximum_leave_classes
        and requested_result["projected_percentage"] >= target_attendance
    )
    projected_without_leave = calculate_percentage(maximum_attended_if_no_leave, maximum_total_if_no_leave)
    remaining_safe_leave_classes = max(0, maximum_leave_classes - requested_leave_classes)
    remaining_safe_leave_days, remaining_safe_leave_remaining_classes = divmod(remaining_safe_leave_classes, CLASSES_PER_DAY)

    return {
        "checkpoint": checkpoint_name,
        "date": checkpoint_date.strftime("%d %B %Y"),
        "date_key": checkpoint_key,
        "is_teaching_day": checkpoint_is_teaching_day,
        "included": True,
        "state": "active" if index == active_index else "upcoming",
        "is_completed": False,
        "is_active": index == active_index,
        "is_upcoming": True,
        "status": status,
        "target_attendance": target_attendance,
        "starting_attended": actual_attended,
        "starting_total": actual_total,
        "starting_percentage": round(starting_percentage, 2),
        "teaching_days": teaching_days,
        "future_classes": future_classes,
        "maximum_leave": maximum_leave_classes,
        "maximum_leave_classes": maximum_leave_classes,
        "maximum_leave_days": maximum_leave_days,
        "maximum_leave_remaining_classes": maximum_leave_remaining_classes,
        "maximum_leave_display": classes_to_leave_display(maximum_leave_classes),
        "classes_needed_for_75": classes_needed,
        "maximum_possible_percentage": round(maximum_possible_percentage, 2),
        "projected_without_leave": round(projected_without_leave, 2),
        "requested_leave": requested_leave_classes,
        "requested_leave_classes": requested_leave_classes,
        "requested_leave_days": requested_leave_days,
        "requested_leave_remaining_classes": requested_leave_remaining_classes,
        "requested_leave_display": classes_to_leave_display(requested_leave_classes),
        "requested_classes_missed": requested_result["requested_classes_missed"],
        "requested_projected_attended": requested_result["projected_attended"],
        "requested_projected_total": requested_result["projected_total"],
        "requested_projected_percentage": requested_result["projected_percentage"],
        "requested_leave_is_safe": requested_leave_is_safe,
        "remaining_safe_leave": remaining_safe_leave_classes,
        "remaining_safe_leave_classes": remaining_safe_leave_classes,
        "remaining_safe_leave_days": remaining_safe_leave_days,
        "remaining_safe_leave_remaining_classes": remaining_safe_leave_remaining_classes,
        "remaining_safe_leave_display": classes_to_leave_display(remaining_safe_leave_classes),
        "final_attended": requested_result["projected_attended"],
        "final_total": requested_result["projected_total"],
        "final_percentage": requested_result["projected_percentage"],
        "classes_missed": requested_result["requested_classes_missed"],
    }


def _get_pending_event_adjustment(pending_event):
    """Return planning-only classes/attendance for an event not yet posted."""
    if not isinstance(pending_event, dict):
        return 0, 0

    try:
        event_classes = int(pending_event.get("classes", 0) or 0)
    except (TypeError, ValueError):
        event_classes = 0

    event_classes = max(0, min(CLASSES_PER_DAY, event_classes))
    event_attended = event_classes if pending_event.get("attended") is True else 0
    return event_classes, event_attended


def _get_remaining_today(attendance_data):
    subjects = attendance_data.get("subjects", [])
    if not subjects:
        return 0
    try:
        value = int(subjects[0].get("_bunkmaster_remaining_today", 0) or 0)
    except (TypeError, ValueError):
        value = 0
    return max(0, value)


def run_phase_1(attendance_data, requested_leaves=None, pending_event=None, checkpoint_targets=None):
    """Run checkpoint planning from normalized effective attendance state."""
    requested_leaves = requested_leaves or {}
    checkpoint_targets = checkpoint_targets or {}
    state = build_attendance_state(attendance_data)
    remaining_today = _get_remaining_today(attendance_data)
    event_classes, event_attended = _get_pending_event_adjustment(pending_event)

    portal_attended = state["portal"]["present"]
    portal_total = state["portal"]["total"]
    portal_percentage = state["portal"]["percentage"]
    site_attended = state["site"]["present"]
    site_total = state["site"]["total"]
    site_percentage = state["site"]["percentage"]
    effective_attended = state["effective"]["present"]
    effective_total = state["effective"]["total"]
    effective_percentage = state["effective"]["percentage"]

    current_date = date.today()
    active_index = get_active_checkpoint_index(current_date)
    if event_classes and pending_event.get("date") == current_date.isoformat():
        remaining_today = max(0, remaining_today - event_classes)

    # Pending event classes have already happened but are not yet portal-posted.
    # They affect planning only; the raw portal/effective state remains unchanged.
    actual_attended = effective_attended + event_attended
    actual_total = effective_total + event_classes
    results = []

    for index, (checkpoint_name, checkpoint_date) in enumerate(CHECKPOINTS):
        if get_checkpoint_state(checkpoint_date, current_date) == "completed":
            results.append(_completed_checkpoint(checkpoint_name, checkpoint_date, actual_attended, actual_total))
            continue
        target_attendance = checkpoint_targets.get(
            checkpoint_date.strftime("%Y-%m-%d"),
            TARGET_ATTENDANCE,
        )
        result = _future_checkpoint(
            checkpoint_name,
            checkpoint_date,
            index,
            active_index,
            current_date,
            actual_attended,
            actual_total,
            requested_leaves,
            remaining_today,
            target_attendance,
        )
        results.append(result)
        actual_attended = result["final_attended"]
        actual_total = result["final_total"]

    return {
        "current_attended": effective_attended,
        "current_total": effective_total,
        "current_percentage": round(effective_percentage, 2),
        "portal_attended": portal_attended,
        "portal_total": portal_total,
        "portal_percentage": round(portal_percentage, 2),
        "unmarked_classes": state["unmarked"],
        "site_attended": site_attended,
        "site_total": site_total,
        "site_percentage": round(site_percentage, 2),
        "effective_attended": effective_attended,
        "effective_total": effective_total,
        "effective_percentage": round(effective_percentage, 2),
        "pending_event": {
            "classes": event_classes,
            "attended": event_attended == event_classes and event_classes > 0,
        },
        "planning_attended": actual_attended,
        "planning_total": actual_total,
        "checkpoints": results,
        "active_checkpoint_index": active_index,
        "active_checkpoint": results[active_index]["checkpoint"] if active_index is not None else None,
        "semester_completed": active_index is None,
        "attendance_state": state,
    }
