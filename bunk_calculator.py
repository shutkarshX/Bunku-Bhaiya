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


def _restore_effective_attendance(checkpoint, attended, total):
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
    """Run planning from the current effective attendance state.

    P = portal present
    A = portal absent
    U = already-held unmarked/frozen classes

    Site attendance      = P / (P + A + U)
    Effective attendance = (P + U) / (P + A + U)

    The legacy calculator receives the effective state so its existing
    attendance-planning mathematics remains unchanged.
    """
    remaining_today = _get_remaining_today(attendance_data)
    unmarked_classes = _get_unmarked_classes(attendance_data)

    # Raw values reported by the college portal.
    portal_attended = attendance_data.get("total_attended", 0)
    portal_total = attendance_data.get("total_classes", 0)
    portal_percentage = calculate_percentage(portal_attended, portal_total)

    # Site attendance counts unmarked/freeze classes in the denominator,
    # while keeping the portal's present count as the numerator.
    site_attended = portal_attended
    site_total = portal_total + unmarked_classes
    site_percentage = calculate_percentage(site_attended, site_total)

    # Effective attendance treats already-held unmarked/freeze classes as
    # present for planning purposes.
    effective_attended = portal_attended + unmarked_classes
    effective_total = site_total
    effective_percentage = calculate_percentage(
        effective_attended,
        effective_total
    )

    # The legacy calculator receives the corrected effective attendance.
    # Its implicit absent count is therefore:
    # (P + A + U) - (P + U) = A.
    effective_attendance = dict(attendance_data)
    effective_attendance["total_attended"] = effective_attended
    effective_attendance["total_classes"] = effective_total

    result = _legacy_run_phase_1(
        effective_attendance,
        checkpoint_choices,
        requested_leaves
    )

    result["portal_attended"] = portal_attended
    result["portal_total"] = portal_total
    result["portal_percentage"] = round(portal_percentage, 2)
    result["unmarked_classes"] = unmarked_classes

    result["site_attended"] = site_attended
    result["site_total"] = site_total
    result["site_percentage"] = round(site_percentage, 2)

    result["effective_attended"] = effective_attended
    result["effective_total"] = effective_total
    result["effective_percentage"] = round(effective_percentage, 2)

    # Backward-compatible aliases for existing template/code paths.
    result["current_attended"] = effective_attended
    result["current_total"] = effective_total
    result["current_percentage"] = round(effective_percentage, 2)

    checkpoints = result.get("checkpoints", [])
    active_index = result.get("active_checkpoint_index")

    if not checkpoints:
        return result
    if active_index is None or not 0 <= active_index < len(checkpoints):
        return result

    active = checkpoints[active_index]

    # Today's remaining classes are future classes, so they do not change
    # portal/site/effective attendance yet. They are added only to the
    # active checkpoint plan.
    adjusted_future_classes = (
        active.get("future_classes", 0) + remaining_today
    )

    effective_percentage = _restore_effective_attendance(
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

    result["effective_attended"] = effective_attended
    result["effective_total"] = effective_total
    result["effective_percentage"] = round(effective_percentage, 2)

    # Keep compatibility aliases synchronized with the effective state.
    result["current_attended"] = effective_attended
    result["current_total"] = effective_total
    result["current_percentage"] = round(effective_percentage, 2)

    return result
