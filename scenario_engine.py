"""What-if scenario calculations built on the shared planning state."""

from datetime import date, timedelta
from attendance_state import build_attendance_state
from academic_calendar import TEACHING_DAYS, is_teaching_day
from bunk_calculator import (
    calculate_percentage,
    classes_needed_to_reach_target,
    CLASSES_PER_DAY,
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


def get_teaching_classes_between(start_date, end_date, attendance_data, pending_event=None):
    """Return planning classes available inside an inclusive date range."""
    if start_date > end_date:
        return 0

    today = date.today()
    total = 0
    current = start_date
    while current <= end_date:
        if is_teaching_day(current.isoformat()):
            if current == today:
                remaining = get_effective_starting_state(
                    attendance_data,
                    pending_event,
                )["today_remaining"]
                total += remaining
            elif current > today:
                total += CLASSES_PER_DAY
        current += timedelta(days=1)
    return total


def calculate_date_range_scenario(
    attendance_data,
    pending_event=None,
    start_date=None,
    end_date=None,
    attended=0,
    leave=0,
):
    """Project attendance for a selected inclusive future date range."""
    starting = get_effective_starting_state(attendance_data, pending_event)

    try:
        start_date = date.fromisoformat(str(start_date))
        end_date = date.fromisoformat(str(end_date))
    except (TypeError, ValueError):
        return {"valid": False, "error": "Choose valid start and end dates.", "starting": starting}

    today = date.today()
    if start_date < today:
        return {"valid": False, "error": "The start date must be today or later.", "starting": starting}
    if end_date < start_date:
        return {"valid": False, "error": "The end date must be on or after the start date.", "starting": starting}

    # Today's event only belongs to a range that actually includes today.
    range_starting = starting if start_date == today else get_effective_starting_state(attendance_data, None)
    future_classes = get_teaching_classes_between(
        start_date,
        end_date,
        attendance_data,
        pending_event if start_date == today else None,
    )

    attended = _safe_nonnegative_int(attended)
    leave = _safe_nonnegative_int(leave)
    planned_classes = attended + leave

    if planned_classes > future_classes:
        return {
            "valid": False,
            "error": f"You can only plan {future_classes} class(es) in this date range.",
            "starting": range_starting,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "start_date_display": start_date.strftime("%d %B %Y"),
            "end_date_display": end_date.strftime("%d %B %Y"),
            "future_classes": future_classes,
            "attended": attended,
            "leave": leave,
        }

    projected_attended = range_starting["attended"] + attended
    projected_total = range_starting["total"] + planned_classes
    return {
        "valid": True,
        "starting": range_starting,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "start_date_display": start_date.strftime("%d %B %Y"),
        "end_date_display": end_date.strftime("%d %B %Y"),
        "future_classes": future_classes,
        "attended": attended,
        "leave": leave,
        "planned_classes": planned_classes,
        "remaining_after_plan": future_classes - planned_classes,
        "projected_attended": projected_attended,
        "projected_total": projected_total,
        "projected_percentage": round(calculate_percentage(projected_attended, projected_total), 2),
    }


def calculate_date_selection_scenario(
    attendance_data,
    pending_event=None,
    plan=None,
):
    """Project attendance from today's effective state using selected teaching dates.

    plan maps ISO dates to {"action": "attend"|"bunk", "classes": optional int}.
    A selected day defaults to its full available class count.
    """
    starting = get_effective_starting_state(attendance_data, pending_event)
    plan = plan if isinstance(plan, dict) else {}

    today = date.today()
    selected = []
    invalid_dates = []

    for date_key, item in plan.items():
        try:
            selected_date = date.fromisoformat(str(date_key))
        except (TypeError, ValueError):
            invalid_dates.append(str(date_key))
            continue

        if selected_date < today:
            invalid_dates.append(str(date_key))
            continue

        if not is_teaching_day(selected_date.isoformat()):
            invalid_dates.append(str(date_key))
            continue

        action = item.get("action") if isinstance(item, dict) else str(item)
        if action not in {"attend", "bunk"}:
            invalid_dates.append(str(date_key))
            continue

        available = (
            starting["today_remaining"]
            if selected_date == today
            else CLASSES_PER_DAY
        )

        requested_classes = available
        if isinstance(item, dict) and item.get("classes") not in (None, ""):
            requested_classes = _safe_nonnegative_int(item.get("classes"))
            requested_classes = min(requested_classes, available)

        if requested_classes <= 0:
            continue

        selected.append({
            "date": selected_date,
            "action": action,
            "classes": requested_classes,
        })

    if invalid_dates:
        return {
            "valid": False,
            "error": "One or more selected dates are not available teaching days.",
            "starting": starting,
        }

    selected.sort(key=lambda item: item["date"])

    attended_classes = sum(
        item["classes"] for item in selected if item["action"] == "attend"
    )
    bunk_classes = sum(
        item["classes"] for item in selected if item["action"] == "bunk"
    )
    planned_classes = attended_classes + bunk_classes

    projected_attended = starting["attended"] + attended_classes
    projected_total = starting["total"] + planned_classes

    return {
        "valid": True,
        "starting": starting,
        "selected_dates": [
            {
                "date": item["date"].isoformat(),
                "date_display": item["date"].strftime("%d %b"),
                "action": item["action"],
                "classes": item["classes"],
            }
            for item in selected
        ],
        "attended": attended_classes,
        "leave": bunk_classes,
        "attended_days": sum(1 for item in selected if item["action"] == "attend"),
        "bunk_days": sum(1 for item in selected if item["action"] == "bunk"),
        "planned_days": len(selected),
        "planned_classes": planned_classes,
        "projected_attended": projected_attended,
        "projected_total": projected_total,
        "projected_percentage": round(
            calculate_percentage(projected_attended, projected_total), 2
        ),
    }


def calculate_until_date_scenario(
    attendance_data,
    pending_event=None,
    target_date=None,
    attended=0,
    leave=0,
):
    """Backward-compatible today-to-date wrapper."""
    return calculate_date_range_scenario(
        attendance_data,
        pending_event,
        date.today().isoformat(),
        target_date,
        attended,
        leave,
    )



def get_target_capacity(attendance_data, pending_event=None):
    """Return the maximum attendance percentage reachable by semester end."""
    starting = get_effective_starting_state(attendance_data, pending_event)
    semester_end = max(
        date.fromisoformat(value)
        for value in TEACHING_DAYS
    )
    available = get_future_classes_until(
        semester_end,
        attendance_data,
        pending_event,
    )
    maximum_attended = starting["attended"] + available
    maximum_total = starting["total"] + available
    return {
        "available_classes": available,
        "maximum_attended": maximum_attended,
        "maximum_total": maximum_total,
        "maximum_percentage": round(
            calculate_percentage(maximum_attended, maximum_total), 2
        ),
        # Browser/input bound uses the exact same maximum value.
        "maximum_input": round(
            calculate_percentage(maximum_attended, maximum_total), 2
        ),
    }


def _build_target_day_plan(needed, attendance_data, pending_event=None):
    """Break required consecutive classes into chronological teaching days."""
    if needed <= 0:
        return []

    starting = get_effective_starting_state(attendance_data, pending_event)
    today = date.today()
    remaining = needed
    plan = []
    current = today

    while current <= max(date.fromisoformat(value) for value in TEACHING_DAYS) and remaining > 0:
        if is_teaching_day(current.isoformat()):
            available = (
                starting["today_remaining"]
                if current == today
                else CLASSES_PER_DAY
            )
            classes = min(remaining, available)
            if classes > 0:
                plan.append({
                    "date": current.isoformat(),
                    "date_display": current.strftime("%d %b %Y"),
                    "classes": classes,
                })
                remaining -= classes
        current += timedelta(days=1)

    return plan
def calculate_target_scenario(attendance_data, pending_event=None, target_attendance=75):
    """Calculate consecutive classes required to reach a target percentage."""
    starting = get_effective_starting_state(attendance_data, pending_event)
    try:
        target_attendance = float(target_attendance)
    except (TypeError, ValueError):
        target_attendance = 0

    if isinstance(target_attendance, float) and target_attendance.is_integer():
        target_attendance = int(target_attendance)

    capacity = get_target_capacity(attendance_data, pending_event)
    maximum_input = capacity["maximum_percentage"]

    if target_attendance <= 0:
        return {
            "valid": False,
            "error": "Target attendance must be above 0%.",
            "starting": starting,
            **capacity,
            "maximum_input": maximum_input,
        }

    if target_attendance > maximum_input:
        return {
            "valid": False,
            "error": f"Target cannot be above the maximum reachable attendance of {capacity['maximum_percentage']}%.",
            "starting": starting,
            "target_attendance": target_attendance,
            **capacity,
            "maximum_input": maximum_input,
        }

    needed = classes_needed_to_reach_target(
        starting["attended"],
        starting["total"],
        target_attendance,
    )

    if needed == 0:
        status = "already_reached"
    else:
        status = "reachable"

    return {
        "valid": True,
        "starting": starting,
        "target_attendance": target_attendance,
        "classes_needed": needed,
        **capacity,
        "status": status,
        "day_plan": _build_target_day_plan(
            needed,
            attendance_data,
            pending_event,
        ),
        "projected_attended": starting["attended"] + needed,
        "projected_total": starting["total"] + needed,
        "projected_percentage": round(
            calculate_percentage(
                starting["attended"] + needed,
                starting["total"] + needed,
            ),
            2,
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
