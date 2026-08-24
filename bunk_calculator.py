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

def classes_needed_to_reach_target(attended, total_classes):
    if total_classes == 0:
        return 0

    current_percentage = calculate_percentage(
        attended,
        total_classes
    )

    if current_percentage >= TARGET_ATTENDANCE:
        return 0

    required_classes = math.ceil(
        (
            (TARGET_ATTENDANCE / 100) * total_classes
            - attended
        )
        /
        (1 - (TARGET_ATTENDANCE / 100))
    )

    return max(0, required_classes)


# =========================================
# LEAVE CONVERSION HELPERS
# =========================================

def days_and_classes_to_classes(days=0, classes=0):
    """
    Convert Days + Classes into one raw class count.

    Example:
        1 day + 10 classes
        = 8 + 10
        = 18 classes
    """

    try:
        days = int(days)
    except (TypeError, ValueError):
        days = 0

    try:
        classes = int(classes)
    except (TypeError, ValueError):
        classes = 0

    days = max(0, days)
    classes = max(0, classes)

    return (
        days * CLASSES_PER_DAY
        + classes
    )


def classes_to_leave_display(total_classes):
    """
    Convert raw classes into:

        X day(s) Y class(es)

    If there are no complete days:

        X class(es)
    """

    try:
        total_classes = int(total_classes)
    except (TypeError, ValueError):
        total_classes = 0

    total_classes = max(0, total_classes)

    days, remaining_classes = divmod(
        total_classes,
        CLASSES_PER_DAY
    )

    if days == 0:
        return f"{remaining_classes} class(es)"

    if remaining_classes == 0:
        return f"{days} day(s)"

    return (
        f"{days} day(s) "
        f"{remaining_classes} class(es)"
    )


# =========================================
# COUNT TEACHING DAYS
# =========================================

def count_teaching_days(start_date, end_date):
    """
    Count teaching days between two dates,
    inclusive.
    """

    if start_date > end_date:
        return 0

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
    future_classes
):
    """
    Find the true maximum number of individual
    future classes that can be missed while
    keeping attendance at or above 75%.

    Everything is calculated in raw classes.

    The result can NEVER exceed future_classes.
    """

    current_percentage = calculate_percentage(
        attended,
        total_classes
    )

    # If already below 75%, no leave is safe.
    if current_percentage < TARGET_ATTENDANCE:
        return 0

    maximum_leave_classes = 0

    # Test every possible number of missed classes.
    for missed_classes in range(
        0,
        future_classes + 1
    ):

        future_attended = (
            future_classes
            - missed_classes
        )

        final_attended = (
            attended
            + future_attended
        )

        final_total = (
            total_classes
            + future_classes
        )

        percentage = calculate_percentage(
            final_attended,
            final_total
        )

        if percentage >= TARGET_ATTENDANCE:

            maximum_leave_classes = (
                missed_classes
            )

        else:
            break

    # Absolute protection:
    # you cannot miss more classes than exist.
    return min(
        maximum_leave_classes,
        future_classes
    )


# =========================================
# CALCULATE USER'S ACTUAL LEAVE
# =========================================

def calculate_requested_leave(
    attended,
    total_classes,
    future_classes,
    requested_days,
    requested_classes,
    maximum_safe_classes
):
    """
    Convert Days + Classes into raw classes.

    Then clamp against:

    1. Actual future classes.
    2. Maximum safe leave.

    Finally calculate attendance at the
    checkpoint.
    """

    requested_classes_total = (
        days_and_classes_to_classes(
            requested_days,
            requested_classes
        )
    )

    # -------------------------------------
    # Cannot miss more classes than exist.
    # -------------------------------------

    requested_classes_total = min(
        requested_classes_total,
        max(0, future_classes)
    )

    # -------------------------------------
    # Cannot exceed maximum safe leave.
    # -------------------------------------

    requested_classes_total = min(
        requested_classes_total,
        max(0, maximum_safe_classes)
    )

    missed_classes = (
        requested_classes_total
    )

    # -------------------------------------
    # Future classes that the student
    # actually attends.
    # -------------------------------------

    future_attended = (
        future_classes
        - missed_classes
    )

    # -------------------------------------
    # Attendance at checkpoint.
    # -------------------------------------

    projected_attended = (
        attended
        + future_attended
    )

    projected_total = (
        total_classes
        + future_classes
    )

    projected_percentage = calculate_percentage(
        projected_attended,
        projected_total
    )

    return {
        "requested_leave_classes":
            requested_classes_total,

        "requested_leave":
            requested_classes_total,

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
    """
    Determine whether the student is:

    safe      -> already >= 75%
    recovery  -> below 75%, but can reach 75%
    impossible -> cannot reach 75% even by
                  attending every future class
    """

    current_percentage = calculate_percentage(
        attended,
        total_classes
    )

    if current_percentage >= TARGET_ATTENDANCE:
        return "safe"

    maximum_attended = (
        attended
        + future_classes
    )

    maximum_total = (
        total_classes
        + future_classes
    )

    maximum_possible_percentage = (
        calculate_percentage(
            maximum_attended,
            maximum_total
        )
    )

    if (
        maximum_possible_percentage
        >= TARGET_ATTENDANCE
    ):
        return "recovery"

    return "impossible"


# =========================================
# PHASE 1 CALCULATOR
# =========================================

def run_phase_1(
    attendance_data,
    checkpoint_choices=None,
    requested_leaves=None
):
    """
    Calculate all three sessional checkpoints.

    Important rules:

    - Today's attendance is already reflected
      in the portal data.
    - Therefore future calculation starts tomorrow.
    - After each checkpoint, the resulting
      attendance becomes the starting attendance
      for the next checkpoint.
    - Leave is always calculated in raw classes.
    """

    # =====================================
    # STARTING ATTENDANCE
    # =====================================

    starting_attended = (
        attendance_data["total_attended"]
    )

    starting_total = (
        attendance_data["total_classes"]
    )

    # =====================================
    # DEFAULT DATA
    # =====================================

    if checkpoint_choices is None:
        checkpoint_choices = {}

    if requested_leaves is None:
        requested_leaves = {}

    # =====================================
    # CHECKPOINTS
    # =====================================

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

    # =====================================
    # START FROM TOMORROW
    # =====================================
    #
    # Today's attendance is already included
    # in the portal attendance.
    #
    # Therefore today must NOT be counted
    # again as a future teaching day.
    # =====================================

    current_date = (
        date.today()
        + timedelta(days=1)
    )

    # =====================================
    # ATTENDANCE CARRIED FORWARD
    # =====================================

    actual_attended = starting_attended
    actual_total = starting_total

    # =====================================
    # PROCESS EACH CHECKPOINT
    # =====================================

    for checkpoint_name, checkpoint_date in checkpoints:

        checkpoint_key = (
            checkpoint_date.strftime(
                "%Y-%m-%d"
            )
        )

        # ---------------------------------
        # Check whether checkpoint itself
        # is a teaching day.
        # ---------------------------------

        checkpoint_is_teaching_day = (
            is_teaching_day(
                checkpoint_key
            )
        )

        # ---------------------------------
        # By default, include the checkpoint
        # date if it is a teaching day.
        # ---------------------------------

        if checkpoint_is_teaching_day:

            include_checkpoint = bool(
                checkpoint_choices.get(
                    checkpoint_key,
                    True
                )
            )

        else:

            include_checkpoint = False

        # ---------------------------------
        # Determine the end of the future
        # teaching period.
        # ---------------------------------

        if include_checkpoint:

            calculation_end = (
                checkpoint_date
            )

        else:

            calculation_end = (
                checkpoint_date
                - timedelta(days=1)
            )

        # ---------------------------------
        # Count future teaching days.
        # ---------------------------------

        teaching_days = count_teaching_days(
            current_date,
            calculation_end
        )

        # ---------------------------------
        # Convert teaching days into
        # actual future classes.
        # ---------------------------------

        future_classes = (
            teaching_days
            * CLASSES_PER_DAY
        )

        # =================================
        # CURRENT STATUS
        # =================================

        status = determine_status(
            actual_attended,
            actual_total,
            future_classes
        )

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

        # =================================
        # MAXIMUM POSSIBLE ATTENDANCE
        # =================================

        maximum_attended_if_no_leave = (
            actual_attended
            + future_classes
        )

        maximum_total_if_no_leave = (
            actual_total
            + future_classes
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

        maximum_leave_classes = (
            find_maximum_safe_leave(
                actual_attended,
                actual_total,
                future_classes
            )
        )

        (
            maximum_leave_days,
            maximum_leave_remaining_classes
        ) = divmod(
            maximum_leave_classes,
            CLASSES_PER_DAY
        )

        # =================================
        # USER REQUEST
        # =================================

        raw_requested = (
            requested_leaves.get(
                checkpoint_key,
                0
            )
        )

        # ---------------------------------
        # New format:
        #
        # {
        #     "days": 1,
        #     "classes": 2
        # }
        #
        # Old raw integer format is also
        # supported.
        # ---------------------------------

        if isinstance(
            raw_requested,
            dict
        ):

            requested_days = (
                raw_requested.get(
                    "days",
                    0
                )
            )

            requested_classes = (
                raw_requested.get(
                    "classes",
                    0
                )
            )

        else:

            requested_days = 0

            requested_classes = (
                raw_requested
            )

        # =================================
        # CALCULATE USER'S ACTUAL LEAVE
        # =================================

        requested_result = (
            calculate_requested_leave(
                actual_attended,
                actual_total,
                future_classes,
                requested_days,
                requested_classes,
                maximum_leave_classes
            )
        )

        requested_leave_classes = (
            requested_result[
                "requested_leave_classes"
            ]
        )

        (
            requested_leave_days,
            requested_leave_remaining_classes
        ) = divmod(
            requested_leave_classes,
            CLASSES_PER_DAY
        )

        # =================================
        # USER REQUEST SAFETY
        # =================================

        requested_leave_is_safe = (
            requested_leave_classes
            <= maximum_leave_classes
            and
            requested_result[
                "projected_percentage"
            ]
            >= TARGET_ATTENDANCE
        )

        # =================================
        # PROJECTED ATTENDANCE
        # IF NO LEAVE IS TAKEN
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

        remaining_safe_leave_classes = max(
            0,
            maximum_leave_classes
            - requested_leave_classes
        )

        (
            remaining_safe_leave_days,
            remaining_safe_leave_remaining_classes
        ) = divmod(
            remaining_safe_leave_classes,
            CLASSES_PER_DAY
        )

        # =================================
        # SAVE CHECKPOINT RESULT
        # =================================

        results.append({

            # --------------------------------
            # CHECKPOINT
            # --------------------------------

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

            # --------------------------------
            # STATUS
            # --------------------------------

            "status":
                status,

            # --------------------------------
            # STARTING ATTENDANCE
            # --------------------------------

            "starting_attended":
                actual_attended,

            "starting_total":
                actual_total,

            "starting_percentage":
                round(
                    starting_percentage,
                    2
                ),

            # --------------------------------
            # FUTURE PERIOD
            # --------------------------------

            "teaching_days":
                teaching_days,

            "future_classes":
                future_classes,

            # --------------------------------
            # MAXIMUM SAFE LEAVE
            # --------------------------------

            "maximum_leave":
                maximum_leave_classes,

            "maximum_leave_classes":
                maximum_leave_classes,

            "maximum_leave_days":
                maximum_leave_days,

            "maximum_leave_remaining_classes":
                maximum_leave_remaining_classes,

            "maximum_leave_display":
                classes_to_leave_display(
                    maximum_leave_classes
                ),

            # --------------------------------
            # RECOVERY
            # --------------------------------

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

            # --------------------------------
            # USER CHOICE
            # --------------------------------

            "requested_leave":
                requested_leave_classes,

            "requested_leave_classes":
                requested_leave_classes,

            "requested_leave_days":
                requested_leave_days,

            "requested_leave_remaining_classes":
                requested_leave_remaining_classes,

            "requested_leave_display":
                classes_to_leave_display(
                    requested_leave_classes
                ),

            "requested_classes_missed":
                requested_result[
                    "requested_classes_missed"
                ],

            # --------------------------------
            # CHECKPOINT ATTENDANCE
            # --------------------------------

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

            # --------------------------------
            # REMAINING SAFE LEAVE
            # --------------------------------

            "remaining_safe_leave":
                remaining_safe_leave_classes,

            "remaining_safe_leave_classes":
                remaining_safe_leave_classes,

            "remaining_safe_leave_days":
                remaining_safe_leave_days,

            "remaining_safe_leave_remaining_classes":
                remaining_safe_leave_remaining_classes,

            "remaining_safe_leave_display":
                classes_to_leave_display(
                    remaining_safe_leave_classes
                ),

            # --------------------------------
            # COMPATIBILITY VALUES
            # --------------------------------

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
        # CRITICAL CARRY-FORWARD
        # =================================
        #
        # The actual projected attendance
        # becomes the starting attendance
        # for the NEXT checkpoint.
        #
        # Example:
        #
        # Start:
        # 241 / 253
        #
        # 16 classes missed during future
        # period of 16 classes:
        #
        # 241 / 269
        #
        # The NEXT checkpoint starts from:
        # 241 / 269
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

        # =================================
        # MOVE PAST THIS CHECKPOINT
        # =================================
        #
        # The next checkpoint must begin
        # from the day AFTER this checkpoint.
        # This prevents classes from being
        # counted twice.
        # =================================

        current_date = (
            checkpoint_date
            + timedelta(days=1)
        )

    # =====================================
    # FINAL RETURN
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