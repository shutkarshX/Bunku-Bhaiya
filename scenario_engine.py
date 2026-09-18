"""What-if scenario calculations built on the shared planning state."""

from datetime import date, timedelta
import math

from attendance_state import build_attendance_state
from bunk_calculator import (
    calculate_percentage,
    classes_needed_to_reach_target,
    CLASSES_PER_DAY,
    is_teaching_day,
    TEACHING_DAYS,
    _get_pending_event_adjustment,
)


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
    if (
        isinstance(pending_event, dict)
        and pending_event.get("date") == date.today().isoformat()
    ):
        event_classes, event_attended = _get_pending_event_adjustment(pending_event)
        event_classes = min(event_classes, remaining_today)
        event_attended = min(event_attended, event_classes)
        remaining_today -= event_classes

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


def _safe_nonnegative_int(value):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _count_teaching_days(start_date, end_date):
    if start_date > end_date:
        return 0
    current = start_date
    count = 0
    while current <= end_date:
        if is_teaching_day(current.isoformat()):
            count += 1
        current += timedelta(days=1)
    return count


def get_future_classes_until(target_date, attendance_data, pending_event=None):
    """Return unposted classes remaining from now through target_date, inclusive."""
    target_date = target_date if isinstance(target_date, date) else date.fromisoformat(str(target_date))
    today = date.today()
    if target_date < today:
        return 0

    starting = get_effective_starting_state(attendance_data, pending_event)
    if target_date == today:
        return starting["today_remaining"]

    # Today's remaining classes are already represented separately. All later
    # teaching days contribute their full daily class count.
    later_days = _count_teaching_days(today + timedelta(days=1), target_date)
    return starting["today_remaining"] + later_days * CLASSES_PER_DAY


def calculate_today_scenario(attendance_data, pending_event=None, attended=0, leave=0):
    """Project today's effective attendance after a chosen attend/leave split."""
    starting = get_effective_starting_state(attendance_data, pending_event)
    attended = _safe_nonnegative_int(attended)
    leave = _safe_nonnegative_int(leave)
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
        calculate_percentage(projected_attended, projected_total), 2
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


def calculate_until_date_scenario(
    attendance_data,
    pending_event=None,
    target_date=None,
    attended=0,
    leave=0,
):
    """Project attendance through a selected date."""
    starting = get_effective_starting_state(attendance_data, pending_event)

    try:
        target_date = date.fromisoformat(str(target_date))
    except (TypeError, ValueError):
        return {"valid": False, "error": "Choose a valid date.", "starting": starting}

    if target_date < date.today():
        return {"valid": False, "error": "The date must be today or later.", "starting": starting}

    future_classes = get_future_classes_until(target_date, attendance_data, pending_event)
    attended = _safe_nonnegative_int(attended)
    leave = _safe_nonnegative_int(leave)

    if attended + leave > future_classes:
        return {
            "valid": False,
            "error": f"You can only plan {future_classes} class(es) through {target_date.strftime('%d %b %Y')}.",
            "starting": starting,
            "target_date": target_date.isoformat(),
            "future_classes": future_classes,
            "attended": attended,
            "leave": leave,
        }

    projected_attended = starting["attended"] + attended
    projected_total = starting["total"] + attended + leave
    return {
        "valid": True,
        "starting": starting,
        "target_date": target_date.isoformat(),
        "target_date_display": target_date.strftime("%d %B %Y"),
        "future_classes": future_classes,
        "attended": attended,
        "leave": leave,
        "planned_classes": attended + leave,
        "remaining_after_plan": future_classes - attended - leave,
        "projected_attended": projected_attended,
        "projected_total": projected_total,
        "projected_percentage": round(
            calculate_percentage(projected_attended, projected_total), 2
        ),
    }


def calculate_target_scenario(attendance_data, pending_event=None, target_attendance=75):
    """Calculate consecutive classes required to reach a target percentage."""
    starting = get_effective_starting_state(attendance_data, pending_event)
    target_attendance = _safe_nonnegative_int(target_attendance)
    target_attendance = min(100, target_attendance)

    if target_attendance <= 0:
        return {
            "valid": False,
            "error": "Target attendance must be above 0%.",
            "starting": starting,
        }

    needed = classes_needed_to_reach_target(
        starting["attended"],
        starting["total"],
        target_attendance,
    )
    available = get_future_classes_until(
        date(max(TEACHING_DAYS)),
        attendance_data,
        pending_event,
    )

    if needed == 0:
        status = "already_reached"
    elif needed <= available:
        status = "reachable"
    else:
        status = "not_reachable"

    projected_attended = starting["attended"] + needed
    projected_total = starting["total"] + needed

    return {
        "valid": True,
        "starting": starting,
        "target_attendance": target_attendance,
        "classes_needed": needed,
        "available_classes": available,
        "status": status,
        "projected_attended": projected_attended,
        "projected_total": projected_total,
        "projected_percentage": round(
            calculate_percentage(projected_attended, projected_total), 2
        ),
    }


def calculate_safe_leaves_scenario(attendance_data, pending_event=None, target_attendance=75):
    """Calculate the maximum classes that can be missed through the calendar end."""
    starting = get_effective_starting_state(attendance_data, pending_event)
    target_attendance = min(99, _safe_nonnegative_int(target_attendance))

    semester_end = max(date.fromisoformat(value) for value in TEACHING_DAYS)
    future_classes = get_future_classes_until(
        semester_end,
        attendance_data,
        pending_event,
    )

    # Future classes are split between attended and missed. Find the largest
    # number of missed classes that still leaves the final attendance at target.
    maximum_leave = 0
    for missed in range(future_classes + 1):
        final_attended = starting["attended"] + future_classes - missed
        final_total = starting["total"] + future_classes
        if calculate_percentage(final_attended, final_total) >= target_attendance:
            maximum_leave = missed
        else:
            break

    projected_attended = starting["attended"] + future_classes - maximum_leave
    projected_total = starting["total"] + future_classes

    return {
        "valid": True,
        "starting": starting,
        "target_attendance": target_attendance,
        "semester_end": semester_end.isoformat(),
        "semester_end_display": semester_end.strftime("%d %B %Y"),
        "future_classes": future_classes,
        "maximum_leave": maximum_leave,
        "maximum_leave_days": maximum_leave // CLASSES_PER_DAY,
        "maximum_leave_remaining_classes": maximum_leave % CLASSES_PER_DAY,
        "projected_attended": projected_attended,
        "projected_total": projected_total,
        "projected_percentage": round(
            calculate_percentage(projected_attended, projected_total), 2
        ),
    }
