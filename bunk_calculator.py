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
# PHASE 1 CALCULATOR
# =========================================

def run_phase_1(
    attendance_data,
    checkpoint_choices=None
):

    # -------------------------------------
    # Current portal attendance
    # -------------------------------------

    attended = attendance_data[
        "total_attended"
    ]

    total_classes = attendance_data[
        "total_classes"
    ]

    # -------------------------------------
    # Default choices
    # -------------------------------------

    if checkpoint_choices is None:

        checkpoint_choices = {}

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
    # Current calculation starts from
    # today's teaching-calendar position
    # -------------------------------------

    current_date = date(
        2026,
        8,
        23
    )

    # =====================================
    # PROCESS CHECKPOINTS
    # =====================================

    for checkpoint_name, checkpoint_date in checkpoints:

        checkpoint_key = (
            checkpoint_date.strftime("%Y-%m-%d")
        )

        # ---------------------------------
        # Is checkpoint itself a teaching day?
        # ---------------------------------

        checkpoint_is_teaching_day = (
            is_teaching_day(checkpoint_key)
        )

        # ---------------------------------
        # First Sessional
        #
        # 29 Aug is not a teaching day,
        # so it is automatically excluded.
        # ---------------------------------

        if not checkpoint_is_teaching_day:

            include_checkpoint = False

        else:

            # Website sends True / False
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
        # Count actual teaching days
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

        # ---------------------------------
        # Maximum safe leave
        # ---------------------------------

        maximum_leave = (
            find_maximum_safe_leave(
                attended,
                total_classes,
                future_classes,
                teaching_days
            )
        )

        # ---------------------------------
        # Project attendance assuming
        # maximum safe leave is taken
        # ---------------------------------

        missed_classes = (
            maximum_leave *
            CLASSES_PER_DAY
        )

        future_attended = (
            future_classes -
            missed_classes
        )

        new_attended = (
            attended +
            future_attended
        )

        new_total = (
            total_classes +
            future_classes
        )

        new_percentage = calculate_percentage(
            new_attended,
            new_total
        )

        # ---------------------------------
        # Save result
        # ---------------------------------

        results.append({

            "checkpoint": checkpoint_name,

            "date": checkpoint_date.strftime(
                "%d %B %Y"
            ),

            "date_key": checkpoint_key,

            "is_teaching_day":
                checkpoint_is_teaching_day,

            "included":
                include_checkpoint,

            "starting_percentage": round(
                calculate_percentage(
                    attended,
                    total_classes
                ),
                2
            ),

            "teaching_days":
                teaching_days,

            "future_classes":
                future_classes,

            "maximum_leave":
                maximum_leave,

            "classes_missed":
                missed_classes,

            "final_attended":
                new_attended,

            "final_total":
                new_total,

            "final_percentage":
                round(
                    new_percentage,
                    2
                )
        })

        # ---------------------------------
        # Carry result forward
        # ---------------------------------

        attended = new_attended

        total_classes = new_total

        if include_checkpoint:

            current_date = (
                checkpoint_date +
                timedelta(days=1)
            )

        else:

            current_date = checkpoint_date

    # =====================================
    # RETURN COMPLETE RESULT
    # =====================================

    return {

        "current_attended":
            attended,

        "current_total":
            total_classes,

        "checkpoints":
            results
    }