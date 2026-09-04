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

    if active_index is None:
        return result

    if not 0 <= active_index < len(checkpoints):
        return result

    active = checkpoints[active_index]

    adjusted_future_classes = (
        active.get("future_classes", 0)
        + remaining_today
    )

    actual_starting_percentage = calculate_percentage(
        actual_attended,
        actual_total
    )

    active["starting_attended"] = actual_attended
    active["starting_total"] = actual_total
    active["starting_percentage"] = round(
        actual_starting_percentage,
        2
    )

    active["future_classes"] = adjusted_future_classes

    active["classes_needed_for_75"] = (
        classes_needed_to_reach_target(
            actual_attended,
            actual_total
        )
    )

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
