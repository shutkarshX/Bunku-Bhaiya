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
    return _get_metadata(
        attendance_data,
        "_bunkmaster_remaining_today"
    )


def _get_unmarked_classes(attendance_data):
    """Sum each subject's classes that are to be marked present.

    The portal exposes this per subject as totalUnFreezedAttendance.
    These classes have already happened and are expected to become
    present, so they are added to the effective current attendance.
    """
    subjects = attendance_data.get("subjects", [])

    total_unmarked = 0

    for subject in subjects:
        try:
            total_unmarked += int(
                subject.get("totalUnFreezedAttendance") or 0
            )
        except (TypeError, ValueError):
            pass

    # Backwards-compatible fallback for older saved attendance sessions
    # where the raw subject field may not be available.
    if total_unmarked == 0:
        total_unmarked = _get_metadata(
            attendance_data,
            "_bunkmaster_unmarked_classes"
        )

    return max(0, total_unmarked)


def _restore_current_attendance(checkpoint, attended, total):
    """Restore the effective current attendance for display."""
    percentage = calculate_percentage(
        attended,
        total
    )

    checkpoint["starting_attended"] = attended
    checkpoint["starting_total"] = total
    checkpoint["starting_percentage"] = round(
        percentage,
        2
    )
    checkpoint["classes_needed_for_75"] = (
        classes_needed_to_reach_target(
            attended,
            total
        )
    )

    return percentage


def run_phase_1(
    attendance_data,
    checkpoint_choices=None,
    requested_leaves=None
):
    """Run the calculator from effective attendance, including unmarked classes."""
    remaining_today = _get_remaining_today(attendance_data)
    unmarked_classes = _get_unmarked_classes(attendance_data)

    # Portal totals are already calculated from:
    #   total_attended = sum(subject.attendedLecture)
    #   total_absent   = sum(subject.absentLecture)
    #   total_classes  = total_attended + total_absent
    #
    # Unmarked/freeze classes are intentionally kept separate from those
    # portal totals until the effective-attendance calculation below.
    portal_attended = attendance_data.get("total_attended", 0)
    portal_total = attendance_data.get("total_classes", 0)
    portal_percentage = calculate_percentage(
        portal_attended,
        portal_total
    )

    # Unmarked classes have already happened and are attended classes.
    # Therefore they belong in the current starting attendance, not future_classes.
    effective_attended = (
        portal_attended
        + unmarked_classes
    )
    effective_total = (
        portal_total
        + unmarked_classes
    )
    effective_percentage = calculate_percentage(
        effective_attended,
        effective_total
    )

    # Keep the raw portal totals intact for display/data consumers while the
    # legacy calculator receives the effective starting attendance.
    effective_attendance = dict(attendance_data)
    effective_attendance["total_attended"] = effective_attended
    effective_attendance["total_classes"] = effective_total

    result = _legacy_run_phase_1(
        effective_attendance,
        checkpoint_choices,
        requested_leaves
    )

    # Make both attendance layers explicit in the result.
    result["portal_attended"] = portal_attended
    result["portal_total"] = portal_total
    result["portal_percentage"] = round(
        portal_percentage,
        2
    )
    result["unmarked_classes"] = unmarked_classes
    result["current_attended"] = effective_attended
    result["current_total"] = effective_total
    result["current_percentage"] = round(
        effective_percentage,
        2
    )

    checkpoints = result.get("checkpoints", [])

    if not checkpoints:
        return result

    # Add only today's remaining classes to the active checkpoint.
    active_index = result.get("active_checkpoint_index")

    if active_index is None:
        return result

    if not 0 <= active_index < len(checkpoints):
        return result

    active = checkpoints[active_index]

    adjusted_future_classes = (
        active.get("future_classes", 0)
        + remaining_today
    )

    current_percentage = _restore_current_attendance(
        active,
        effective_attended,
        effective_total
    )

    active["future_classes"] = adjusted_future_classes

    active["status"] = determine_status(
        effective_attended,
        effective_total,
        adjusted_future_classes
    )

    active["maximum_possible_percentage"] = round(
        calculate_percentage(
            effective_attended + adjusted_future_classes,
            effective_total + adjusted_future_classes
        ),
        2
    )

    # Keep the result's current attendance aligned with the effective starting point.
    # Unmarked classes are already attended; today's remaining classes are future only.
    result["current_attended"] = effective_attended
    result["current_total"] = effective_total
    result["current_percentage"] = round(
        current_percentage,
        2
    )

    return result
