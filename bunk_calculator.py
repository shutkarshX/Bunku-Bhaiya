from datetime import date, timedelta

from academic_calendar import (
    TEACHING_CLASSES_PER_DAY,
    ATTENDANCE_TARGET,
    is_teaching_day
)


# =========================================
# BUNKMASTER - PHASE 1
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
# COUNT TEACHING DAYS
# =========================================

def count_teaching_days(start_date, end_date):

    count = 0

    current = start_date

    while current <= end_date:

        date_string = current.strftime("%Y-%m-%d")

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

    maximum_leave = 0

    for leave_days in range(teaching_days + 1):

        missed_classes = (
            leave_days * CLASSES_PER_DAY
        )

        future_attended = (
            future_classes - missed_classes
        )

        final_attended = (
            attended + future_attended
        )

        final_total = (
            total_classes + future_classes
        )

        percentage = calculate_percentage(
            final_attended,
            final_total
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

    # Maximum number of complete teaching
    # days available in this period.
    maximum_possible_leave = (
        future_classes // CLASSES_PER_DAY
    )

    # We don't silently allow a value larger
    # than the actual number of teaching days.
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

    projected_percentage = calculate_percentage(
        projected_attended,
        projected_total
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
# PHASE 1 CALCULATOR
# =========================================

def run_phase_1(
    attendance_data,
    checkpoint_choices=None,
    requested_leaves=None
):

    # -------------------------------------
    # Current portal attendance
    # -------------------------------------

    starting_attended = attendance_data[
        "total_attended"
    ]

    starting_total = attendance_data[
        "total_classes"
    ]

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
    # Calculation starts from current date
    # -------------------------------------

    current_date = date(
        2026,
        8,
        23
    )

    # -------------------------------------
    # These represent the user's actual
    # attendance plan as we move forward.
    #
    # If no leave has been selected yet,
    # we assume all classes are attended.
    # -------------------------------------

    actual_attended = starting_attended
    actual_total = starting_total

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
        # Checkpoint teaching-day status
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
                    False
                )
            )

        # ---------------------------------
        # Calculation end date
        # ---------------------------------

        if include_checkpoint:

            calculation_end = checkpoint_date

        else:

            calculation_end = (
                checkpoint_date -
                timedelta(days=1)
            )

        # ---------------------------------
        # Count teaching days
        # ---------------------------------

        teaching_days = count_teaching_days(
            current_date,
            calculation_end
        )

        # ---------------------------------
        # Convert teaching days to classes
        # ---------------------------------

        future_classes = (
            teaching_days *
            CLASSES_PER_DAY
        )

        # =================================
        # MAXIMUM SAFE LEAVE
        #
        # This is calculated using the
        # user's ACTUAL current plan.
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
        # USER REQUESTED LEAVE
        #
        # Normally this is empty during
        # the first calculation.
        # =================================

        requested_leave = requested_leaves.get(
            checkpoint_key,
            None
        )

        # ---------------------------------
        # If the user has not selected
        # leave yet, assume ZERO leave.
        # ---------------------------------

        if requested_leave is None:

            requested_leave = 0

        requested_result = (
            calculate_requested_leave(
                actual_attended,
                actual_total,
                future_classes,
                requested_leave
            )
        )

        # =================================
        # IMPORTANT SAFETY CHECK
        # =================================

        requested_leave_is_safe = (
            requested_result[
                "requested_leave"
            ] <= maximum_leave
        )

        # =================================
        # Remaining safe leave
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

            "starting_attended":
                actual_attended,

            "starting_total":
                actual_total,

            "starting_percentage":
                round(
                    calculate_percentage(
                        actual_attended,
                        actual_total
                    ),
                    2
                ),

            "teaching_days":
                teaching_days,

            "future_classes":
                future_classes,

            # Maximum safe leave
            "maximum_leave":
                maximum_leave,

            # User's choice
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

            # For compatibility with the
            # existing dashboard
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
        # CARRY FORWARD THE USER'S ACTUAL
        # PLAN — NOT THE MAXIMUM LEAVE
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

            current_date = checkpoint_date

    # =====================================
    # RETURN RESULT
    # =====================================

    return {

        "current_attended":
            actual_attended,

        "current_total":
            actual_total,

        "checkpoints":
            results
    }