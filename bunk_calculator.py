from datetime import date, timedelta
import math

from academic_calendar import (
    TEACHING_CLASSES_PER_DAY,
    ATTENDANCE_TARGET,
    is_teaching_day
)


# =========================================
# BUNKMASTER CALCULATOR
# =========================================

CLASSES_PER_DAY = TEACHING_CLASSES_PER_DAY
TARGET_ATTENDANCE = ATTENDANCE_TARGET


# =========================================
# ATTENDANCE PERCENTAGE
# =========================================

def calculate_percentage(attended, total):

    if total == 0:
        return 0

    return (attended / total) * 100


# =========================================
# CLASSES NEEDED TO REACH TARGET
# =========================================

def classes_needed_to_reach_target(
    attended,
    total_classes
):

    if total_classes == 0:
        return 0

    current_percentage = (
        attended / total_classes
    ) * 100

    # Already at or above 75%
    if current_percentage >= TARGET_ATTENDANCE:
        return 0

    # Calculate how many consecutive
    # classes must be attended to reach
    # the attendance target.
    #
    # (attended + x)
    # ---------------------- >= 75%
    # (total_classes + x)

    target = TARGET_ATTENDANCE / 100

    required_classes = math.ceil(
        (
            target * total_classes
            - attended
        )
        /
        (1 - target)
    )

    return max(
        0,
        required_classes
    )


# =========================================
# COUNT TEACHING DAYS
# =========================================

def count_teaching_days(
    start_date,
    end_date
):

    count = 0

    current = start_date

    while current <= end_date:

        date_string = (
            current.strftime("%Y-%m-%d")
        )

        if is_teaching_day(date_string):

            count += 1

        current += timedelta(days=1)

    return count


# =========================================
# FIND MAXIMUM SAFE LEAVE
# =========================================

def find_maximum_safe_leave(
    attended,
    total_classes,
    future_classes,
    teaching_days
):

    # -------------------------------------
    # Already below target.
    #
    # No additional leave is safe.
    # -------------------------------------

    current_percentage = (
        calculate_percentage(
            attended,
            total_classes
        )
    )

    if current_percentage < TARGET_ATTENDANCE:

        return 0

    maximum_leave = 0

    for leave_days in range(
        teaching_days + 1
    ):

        missed_classes = (
            leave_days *
            CLASSES_PER_DAY
        )

        future_attended = (
            future_classes -
            missed_classes
        )

        final_attended = (
            attended +
            future_attended
        )

        final_total = (
            total_classes +
            future_classes
        )

        percentage = (
            calculate_percentage(
                final_attended,
                final_total
            )
        )

        if percentage >= TARGET_ATTENDANCE:

            maximum_leave = leave_days

        else:

            break

    return maximum_leave


# =========================================
# CALCULATE USER'S ACTUAL LEAVE
# =========================================

def calculate_requested_leave(
    attended,
    total_classes,
    future_classes,
    requested_leave
):

    requested_leave = max(
        0,
        int(requested_leave)
    )

    maximum_possible_leave = (
        future_classes //
        CLASSES_PER_DAY
    )

    requested_leave = min(
        requested_leave,
        maximum_possible_leave
    )

    missed_classes = (
        requested_leave *
        CLASSES_PER_DAY
    )

    future_attended = (
        future_classes -
        missed_classes
    )

    projected_attended = (
        attended +
        future_attended
    )

    projected_total = (
        total_classes +
        future_classes
    )

    projected_percentage = (
        calculate_percentage(
            projected_attended,
            projected_total
        )
    )

    return {

        "requested_leave":
            requested_leave,

        "requested_classes_missed":
            missed_classes,

        "projected_attended":
            projected_attended,

        "projected_total":
            projected_total,

        "projected_percentage":
            round(
                projected_percentage,
                2
            )
    }


# =========================================
# DETERMINE ATTENDANCE STATUS
# =========================================

def determine_status(
    attended,
    total_classes,
    future_classes
):

    current_percentage = (
        calculate_percentage(
            attended,
            total_classes
        )
    )

    # -------------------------------------
    # SAFE
    # -------------------------------------

    if current_percentage >= TARGET_ATTENDANCE:

        return "safe"


    # -------------------------------------
    # CURRENTLY BELOW 75%
    # -------------------------------------

    # Calculate the maximum attendance
    # possible if every future class
    # is attended.

    maximum_attended = (
        attended +
        future_classes
    )

    maximum_total = (
        total_classes +
        future_classes
    )

    maximum_possible_percentage = (
        calculate_percentage(
            maximum_attended,
            maximum_total
        )
    )

    # -------------------------------------
    # RECOVERY POSSIBLE
    # -------------------------------------

    if (
        maximum_possible_percentage
        >= TARGET_ATTENDANCE
    ):

        return "recovery"


    # -------------------------------------
    # RECOVERY IMPOSSIBLE
    # -------------------------------------

    return "impossible"


# =========================================
# PHASE 1 CALCULATOR
# =========================================

def run_phase_1(
    attendance_data,
    checkpoint_choices=None,
    requested_leaves=None
):

    # -------------------------------------
    # Starting portal attendance
    # -------------------------------------

    starting_attended = (
        attendance_data[
            "total_attended"
        ]
    )

    starting_total = (
        attendance_data[
            "total_classes"
        ]
    )

    # -------------------------------------
    # Defaults
    # -------------------------------------

    if checkpoint_choices is None:

        checkpoint_choices = {}

    if requested_leaves is None:

        requested_leaves = {}

    # -------------------------------------
    # Checkpoints
    # -------------------------------------

    checkpoints = [

        (
            "First Sessional",
            date(2026, 8, 29)
        ),

        (
            "Second Sessional",
            date(2026, 10, 10)
        ),

        (
            "Third Sessional",
            date(2026, 11, 16)
        )
    ]

    results = []

    # -------------------------------------
    # Current calculation date
    # -------------------------------------

    current_date = date(
        2026,
        8,
        23
    )

    # -------------------------------------
    # Actual attendance carried forward
    # -------------------------------------

    actual_attended = (
        starting_attended
    )

    actual_total = (
        starting_total
    )

    # =====================================
    # PROCESS CHECKPOINTS
    # =====================================

    for checkpoint_name, checkpoint_date in checkpoints:

        checkpoint_key = (
            checkpoint_date.strftime(
                "%Y-%m-%d"
            )
        )

        # ---------------------------------
        # Is checkpoint itself a teaching day?
        # ---------------------------------

        checkpoint_is_teaching_day = (
            is_teaching_day(
                checkpoint_key
            )
        )

        # ---------------------------------
        # Decide whether checkpoint itself
        # is included.
        # ---------------------------------

        if not checkpoint_is_teaching_day:

            include_checkpoint = False

        else:

            include_checkpoint = bool(
                checkpoint_choices.get(
                    checkpoint_key,
                    True
                )
            )

        # ---------------------------------
        # Calculation end date
        # ---------------------------------

        if include_checkpoint:

            calculation_end = (
                checkpoint_date
            )

        else:

            calculation_end = (
                checkpoint_date -
                timedelta(days=1)
            )

        # ---------------------------------
        # Count teaching days
        # ---------------------------------

        teaching_days = (
            count_teaching_days(
                current_date,
                calculation_end
            )
        )

        # ---------------------------------
        # Convert teaching days into classes
        # ---------------------------------

        future_classes = (
            teaching_days *
            CLASSES_PER_DAY
        )

        # =================================
        # CURRENT STATUS
        # =================================

        status = determine_status(
            actual_attended,
            actual_total,
            future_classes
        )

        # =================================
        # CURRENT ATTENDANCE
        # =================================

        starting_percentage = (
            calculate_percentage(
                actual_attended,
                actual_total
            )
        )

        # =================================
        # RECOVERY INFORMATION
        # =================================

        classes_needed = (
            classes_needed_to_reach_target(
                actual_attended,
                actual_total
            )
        )

        maximum_attended_if_no_leave = (
            actual_attended +
            future_classes
        )

        maximum_total_if_no_leave = (
            actual_total +
            future_classes
        )

        maximum_possible_percentage = (
            calculate_percentage(
                maximum_attended_if_no_leave,
                maximum_total_if_no_leave
            )
        )

        # =================================
        # MAXIMUM SAFE LEAVE
        # =================================

        maximum_leave = (
            find_maximum_safe_leave(
                actual_attended,
                actual_total,
                future_classes,
                teaching_days
            )
        )

        # =================================
        # USER'S ACTUAL CHOICE
        # =================================

        requested_leave = requested_leaves.get(
            checkpoint_key,
            0
        )

        try:

            requested_leave = int(
                requested_leave
            )

        except (TypeError, ValueError):

            requested_leave = 0

        requested_leave = max(
            0,
            requested_leave
        )

        # ---------------------------------
        # Calculate requested leave
        # ---------------------------------

        requested_result = (
            calculate_requested_leave(
                actual_attended,
                actual_total,
                future_classes,
                requested_leave
            )
        )

        # ---------------------------------
        # Determine whether requested leave
        # keeps attendance at or above 75%.
        # ---------------------------------

        requested_leave_is_safe = (
            requested_leave <= maximum_leave
            and
            requested_result[
                "projected_percentage"
            ] >= TARGET_ATTENDANCE
        )

        # =================================
        # RECOVERY AFTER FUTURE CLASSES
        # =================================

        projected_without_leave = (
            calculate_percentage(
                maximum_attended_if_no_leave,
                maximum_total_if_no_leave
            )
        )

        # =================================
        # REMAINING SAFE LEAVE
        # =================================

        remaining_safe_leave = (
            maximum_leave -
            requested_result[
                "requested_leave"
            ]
        )

        remaining_safe_leave = max(
            0,
            remaining_safe_leave
        )

        # =================================
        # SAVE RESULT
        # =================================

        results.append({

            "checkpoint":
                checkpoint_name,

            "date":
                checkpoint_date.strftime(
                    "%d %B %Y"
                ),

            "date_key":
                checkpoint_key,

            "is_teaching_day":
                checkpoint_is_teaching_day,

            "included":
                include_checkpoint,

            # -----------------------------
            # STATUS
            # -----------------------------

            "status":
                status,

            # -----------------------------
            # STARTING ATTENDANCE
            # -----------------------------

            "starting_attended":
                actual_attended,

            "starting_total":
                actual_total,

            "starting_percentage":
                round(
                    starting_percentage,
                    2
                ),

            # -----------------------------
            # FUTURE CLASSES
            # -----------------------------

            "teaching_days":
                teaching_days,

            "future_classes":
                future_classes,

            # -----------------------------
            # SAFE LEAVE
            # -----------------------------

            "maximum_leave":
                maximum_leave,

            # -----------------------------
            # RECOVERY
            # -----------------------------

            "classes_needed_for_75":
                classes_needed,

            "maximum_possible_percentage":
                round(
                    maximum_possible_percentage,
                    2
                ),

            "projected_without_leave":
                round(
                    projected_without_leave,
                    2
                ),

            # -----------------------------
            # USER CHOICE
            # -----------------------------

            "requested_leave":
                requested_result[
                    "requested_leave"
                ],

            "requested_classes_missed":
                requested_result[
                    "requested_classes_missed"
                ],

            "requested_projected_attended":
                requested_result[
                    "projected_attended"
                ],

            "requested_projected_total":
                requested_result[
                    "projected_total"
                ],

            "requested_projected_percentage":
                requested_result[
                    "projected_percentage"
                ],

            "requested_leave_is_safe":
                requested_leave_is_safe,

            "remaining_safe_leave":
                remaining_safe_leave,

            # -----------------------------
            # COMPATIBILITY
            # -----------------------------

            "final_attended":
                requested_result[
                    "projected_attended"
                ],

            "final_total":
                requested_result[
                    "projected_total"
                ],

            "final_percentage":
                requested_result[
                    "projected_percentage"
                ],

            "classes_missed":
                requested_result[
                    "requested_classes_missed"
                ]
        })

        # =================================
        # CARRY FORWARD ACTUAL USER PLAN
        # =================================

        actual_attended = (
            requested_result[
                "projected_attended"
            ]
        )

        actual_total = (
            requested_result[
                "projected_total"
            ]
        )

        # ---------------------------------
        # Move to next checkpoint
        # ---------------------------------

        if include_checkpoint:

            current_date = (
                checkpoint_date +
                timedelta(days=1)
            )

        else:

            current_date = (
                checkpoint_date
            )

    # =====================================
    # RETURN
    # =====================================

    return {

        "current_attended":
            actual_attended,

        "current_total":
            actual_total,

        "current_percentage":
            round(
                calculate_percentage(
                    actual_attended,
                    actual_total
                ),
                2
            ),

        "checkpoints":
            results
    }