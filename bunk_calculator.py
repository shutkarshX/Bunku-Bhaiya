from legacy_bunk_calculator import *
from legacy_bunk_calculator import run_phase_1 as _legacy_run_phase_1


# =========================================
# TODAY'S REMAINING CLASSES + UNMARKED
# =========================================


def _get_metadata(attendance_data, key):
    """Read BunkMaster metadata preserved by portal.py."""
    subjects = attendance_data.get("subjects", [])
    if not subjects:
        return 0
    try:
        value = int(subjects[0].get(key, 0) or 0)
    except (TypeError, ValueError):
        value = 0
    return max(0, value)


def _get_remaining_today(attendance_data):
    return _get_metadata(attendance_data, "_bunkmaster_remaining_today")


def _get_unmarked_classes(attendance_data):
    """Return classes already held but not yet included in portal totals."""
    subjects = attendance_data.get("subjects", [])
    total_unmarked = 0
    for subject in subjects:
        try:
            total_unmarked += int(subject.get("totalUnFreezedAttendance") or 0)
        except (TypeError, ValueError):
            pass
    if total_unmarked == 0:
        total_unmarked = _get_metadata(
            attendance_data,
            "_bunkmaster_unmarked_classes"
        )
    return max(0, total_unmarked)


def _restore_current_attendance(checkpoint, attended, total):
    percentage = calculate_percentage(attended, total)
    checkpoint["starting_attended"] = attended
    checkpoint["starting_total"] = total
    checkpoint["starting_percentage"] = round(percentage, 2)
    checkpoint["classes_needed_for_75"] = classes_needed_to_reach_target(
        attended, total
    )
    return percentage


def run_phase_1(
    attendance_data,
    checkpoint_choices=None,
    requested_leaves=None
):
    """Run the calculator using current attendance = portal present / portal total + unmarked."""
    remaining_today = _get_remaining_today(attendance_data)
    unmarked_classes = _get_unmarked_classes(attendance_data)

    # Raw values reported by the college portal.
    portal_attended = attendance_data.get("total_attended", 0)
    portal_total = attendance_data.get("total_classes", 0)
    portal_percentage = calculate_percentage(portal_attended, portal_total)

    # IMPORTANT:
    # Unmarked/freeze classes have already happened, but they are NOT yet
    # counted as present. They increase the current denominator only.
    current_attended = portal_attended
    current_total = portal_total + unmarked_classes
    current_percentage = calculate_percentage(
        current_attended,
        current_total
    )

    # The legacy calculator receives the corrected current attendance.
    current_attendance = dict(attendance_data)
    current_attendance["total_attended"] = current_attended
    current_attendance["total_classes"] = current_total

    result = _legacy_run_phase_1(
        current_attendance,
        checkpoint_choices,
        requested_leaves
    )

    result["portal_attended"] = portal_attended
    result["portal_total"] = portal_total
    result["portal_percentage"] = round(portal_percentage, 2)
    result["unmarked_classes"] = unmarked_classes
    result["current_attended"] = current_attended
    result["current_total"] = current_total
    result["current_percentage"] = round(current_percentage, 2)

    checkpoints = result.get("checkpoints", [])
    active_index = result.get("active_checkpoint_index")

    if not checkpoints:
        return result
    if active_index is None or not 0 <= active_index < len(checkpoints):
        return result

    active = checkpoints[active_index]

    # Today's remaining classes are future classes, so they do not change
    # current attendance. They are added only to the active checkpoint plan.
    adjusted_future_classes = (
        active.get("future_classes", 0) + remaining_today
    )

    current_percentage = _restore_current_attendance(
        active,
        current_attended,
        current_total
    )

    active["future_classes"] = adjusted_future_classes
    active["status"] = determine_status(
        current_attended,
        current_total,
        adjusted_future_classes
    )
    active["maximum_possible_percentage"] = round(
        calculate_percentage(
            current_attended + adjusted_future_classes,
            current_total + adjusted_future_classes
        ),
        2
    )

    result["current_attended"] = current_attended
    result["current_total"] = current_total
    result["current_percentage"] = round(current_percentage, 2)

    return result
