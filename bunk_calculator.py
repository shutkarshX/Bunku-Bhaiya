from legacy_bunk_calculator import *
from legacy_bunk_calculator import run_phase_1 as _legacy_run_phase_1
from attendance_state import build_attendance_state, apply_effective_state


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
    return build_attendance_state(attendance_data)["unmarked"]


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
    """Run checkpoint planning from normalized effective attendance.

    P = portal present, A = portal absent, U = already-held unmarked/frozen.
    The normalized state is kept separate so future What-If features can use
    the same clean attendance model without re-reading portal field names.
    """
    remaining_today = _get_remaining_today(attendance_data)
    state = build_attendance_state(attendance_data)

    portal_attended = state["portal"]["present"]
    portal_total = state["portal"]["total"]
    portal_percentage = state["portal"]["percentage"]

    site_attended = state["site"]["present"]
    site_total = state["site"]["total"]
    site_percentage = state["site"]["percentage"]

    effective_attended = state["effective"]["present"]
    effective_total = state["effective"]["total"]
    effective_percentage = state["effective"]["percentage"]

    # The legacy calculator receives the corrected effective attendance.
    # Its implicit absent count remains exactly A:
    # (P + A + U) - (P + U) = A.
    effective_attendance = apply_effective_state(attendance_data, state)

    result = _legacy_run_phase_1(
        effective_attendance,
        checkpoint_choices,
        requested_leaves
    )

    result["attendance_state"] = state
    result["portal_attended"] = portal_attended
    result["portal_total"] = portal_total
    result["portal_percentage"] = round(portal_percentage, 2)
    result["unmarked_classes"] = state["unmarked"]

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

    # Today's remaining classes are future classes. They do not change
    # portal/site/effective attendance yet; they only affect the active plan.
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

    result["current_attended"] = effective_attended
    result["current_total"] = effective_total
    result["current_percentage"] = round(effective_percentage, 2)

    return result
