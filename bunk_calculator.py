from legacy_bunk_calculator import *
from legacy_bunk_calculator import run_phase_1 as _legacy_run_phase_1


# =========================================
# TODAY'S REMAINING CLASSES
# =========================================


def _get_remaining_today(attendance_data):
    """Read today's remaining classes preserved by portal.py."""
    subjects = attendance_data.get("subjects", [])

    if not subjects:
        return 0

    try:
        remaining = int(
            subjects[0].get(
                "_bunkmaster_remaining_today",
                0
            )
        )
    except (TypeError, ValueError):
        remaining = 0

    return max(0, remaining)


def _restore_current_attendance(checkpoint, attended, total):
    """Restore fields that must describe real current attendance."""
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
    """Run the original calculator while including today's classes."""
    remaining_today = _get_remaining_today(attendance_data)

    if remaining_today == 0:
        return _legacy_run_phase_1(
            attendance_data,
            checkpoint_choices,
            requested_leaves
        )

    # Treat today's remaining classes as classes that will be attended.
    # This is mathematically equivalent to adding them to future_classes,
    # while keeping the real current attendance unchanged for display.
    effective_attendance = dict(attendance_data)

    effective_attendance["total_attended"] = (
        attendance_data.get("total_attended", 0)
        + remaining_today
    )

    effective_attendance["total_classes"] = (
        attendance_data.get("total_classes", 0)
        + remaining_today
    )

    result = _legacy_run_phase_1(
        effective_attendance,
        checkpoint_choices,
        requested_leaves
    )

    actual_attended = attendance_data.get(
        "total_attended",
        0
    )
    actual_total = attendance_data.get(
        "total_classes",
        0
    )

    active_index = result.get(
        "active_checkpoint_index"
    )

    checkpoints = result.get(
        "checkpoints",
        []
    )

    if not checkpoints:
        return result

    # -----------------------------------------
    # Completed checkpoints must describe the
    # real portal attendance, not the synthetic
    # today's-attended classes used internally.
    # -----------------------------------------

    for checkpoint in checkpoints:
        if checkpoint.get("state") != "completed":
            continue

        current_percentage = _restore_current_attendance(
            checkpoint,
            actual_attended,
            actual_total
        )

        checkpoint["status"] = determine_status(
            actual_attended,
            actual_total,
            0
        )
        checkpoint["maximum_possible_percentage"] = round(
            current_percentage,
            2
        )
        checkpoint["projected_without_leave"] = round(
            current_percentage,
            2
        )
        checkpoint["requested_projected_attended"] = actual_attended
        checkpoint["requested_projected_total"] = actual_total
        checkpoint["requested_projected_percentage"] = round(
            current_percentage,
            2
        )
        checkpoint["final_attended"] = actual_attended
        checkpoint["final_total"] = actual_total
        checkpoint["final_percentage"] = round(
            current_percentage,
            2
        )

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
        actual_attended,
        actual_total
    )

    active["future_classes"] = adjusted_future_classes

    active["status"] = determine_status(
        actual_attended,
        actual_total,
        adjusted_future_classes
    )

    active["maximum_possible_percentage"] = round(
        calculate_percentage(
            actual_attended + adjusted_future_classes,
            actual_total + adjusted_future_classes
        ),
        2
    )

    return result
