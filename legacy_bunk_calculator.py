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
# CHECKPOINTS
# =========================================

CHECKPOINTS = [
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


# =========================================
# ATTENDANCE PERCENTAGE
# =========================================

def calculate_percentage(attended, total):

    if total == 0:
        return 0

    return (
        attended /
        total
    ) * 100


# =========================================
# CLASSES NEEDED TO REACH TARGET
# =========================================

def classes_needed_to_reach_target(
    attended,
    total_classes
):

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
            (TARGET_ATTENDANCE / 100)
            * total_classes
            - attended
        )
        /
        (1 - (TARGET_ATTENDANCE / 100))
    )

    return max(
        0,
        required_classes
    )


# =========================================
# LEAVE CONVERSION
# =========================================

def days_and_classes_to_classes(
    days=0,
    classes=0
):

    try:
        days = int(days)
    except (
        TypeError,
        ValueError
    ):
        days = 0

    try:
        classes = int(classes)
    except (
        TypeError,
        ValueError
    ):
        classes = 0

    days = max(
        0,
        days
    )

    classes = max(
        0,
        classes
    )

    return (
        days * CLASSES_PER_DAY
        +
        classes
    )


def classes_to_leave_display(
    total_classes
):

    try:
        total_classes = int(
            total_classes
        )
    except (
        TypeError,
        ValueError
    ):
        total_classes = 0

    total_classes = max(
        0,
        total_classes
    )

    days, remaining_classes = divmod(
        total_classes,
        CLASSES_PER_DAY
    )

    if days == 0:

        return (
            f"{remaining_classes} "
            f"class(es)"
        )

    if remaining_classes == 0:

        return (
            f"{days} day(s)"
        )

    return (
        f"{days} day(s) "
        f"{remaining_classes} class(es)"
    )


# =========================================
# COUNT TEACHING DAYS
# =========================================

def count_teaching_days(
    start_date,
    end_date
):

    if start_date > end_date:
        return 0

    count = 0

    current = start_date

    while current <= end_date:

        date_string = current.strftime(
            "%Y-%m-%d"
        )

        if is_teaching_day(
            date_string
        ):
            count += 1

        current += timedelta(
            days=1
        )

    return count


# =========================================
# FIND MAXIMUM SAFE LEAVE
# =========================================

def find_maximum_safe_leave(
    attended,
    total_classes,
    future_classes
):

    current_percentage = calculate_percentage(
        attended,
        total_classes
    )

    if current_percentage < TARGET_ATTENDANCE:
        return 0

    maximum_leave_classes = 0

    for missed_classes in range(
        0,
        future_classes + 1
    ):

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

    return maximum_leave_classes


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

    requested_classes_total = (
        days_and_classes_to_classes(
            requested_days,
            requested_classes
        )
    )

    # =====================================
    # NEVER MISS MORE CLASSES THAN EXIST
    # =====================================

    requested_classes_total = min(
        requested_classes_total,
        max(
            0,
            future_classes
        )
    )

    # =====================================
    # NEVER EXCEED SAFE LEAVE
    # =====================================

    requested_classes_total = min(
        requested_classes_total,
        max(
            0,
            maximum_safe_classes
        )
    )

    missed_classes = (
        requested_classes_total
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

    current_percentage = calculate_percentage(
        attended,
        total_classes
    )

    if current_percentage >= TARGET_ATTENDANCE:

        return "safe"

    classes_needed = (
        classes_needed_to_reach_target(
            attended,
            total_classes
        )
    )

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

    if maximum_possible_percentage >= TARGET_ATTENDANCE:

        return "recovery"

    return "impossible"


# =========================================
# CHECKPOINT DATE STATUS
# =========================================

def get_checkpoint_state(
    checkpoint_date,
    current_date
):

    if current_date >= checkpoint_date:

        return "completed"

    return "upcoming"


# =========================================
# FIND ACTIVE CHECKPOINT
# =========================================

def get_active_checkpoint_index(
    current_date
):

    for index, (
        checkpoint_name,
        checkpoint_date
    ) in enumerate(CHECKPOINTS):

        if current_date < checkpoint_date:

            return index

    return None


# =========================================
# PHASE 1 CALCULATOR
# =========================================

def run_phase_1(
    attendance_data,
    checkpoint_choices=None,
    requested_leaves=None
):

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

    if checkpoint_choices is None:
        checkpoint_choices = {}

    if requested_leaves is None:
        requested_leaves = {}

    # =====================================
    # TODAY
    # =====================================

    current_date = date.today()

    active_index = (
        get_active_checkpoint_index(
            current_date
        )
    )

    results = []

    # =====================================
    # CURRENT ATTENDANCE
    #
    # This is the real portal attendance.
    # =====================================

    actual_attended = (
        starting_attended
    )

    actual_total = (
        starting_total
    )

    # =====================================
    # LOOP THROUGH ALL CHECKPOINTS
    # =====================================

    for index, (
        checkpoint_name,
        checkpoint_date
    ) in enumerate(CHECKPOINTS):

        checkpoint_key = (
            checkpoint_date.strftime(
                "%Y-%m-%d"
            )
        )

        state = get_checkpoint_state(
            checkpoint_date,
            current_date
        )

        # =================================
        # COMPLETED CHECKPOINT
        # =================================

        if state == "completed":

            current_percentage = (
                calculate_percentage(
                    actual_attended,
                    actual_total
                )
            )

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
                    is_teaching_day(
                        checkpoint_key
                    ),

                "included":
                    True,

                "state":
                    "completed",

                "is_completed":
                    True,

                "is_active":
                    False,

                "is_upcoming":
                    False,

                "status":
                    determine_status(
                        actual_attended,
                        actual_total,
                        0
                    ),

                "starting_attended":
                    actual_attended,

                "starting_total":
                    actual_total,

                "starting_percentage":
                    round(
                        current_percentage,
                        2
                    ),

                "teaching_days":
                    0,

                "future_classes":
                    0,

                "maximum_leave":
                    0,

                "maximum_leave_classes":
                    0,

                "maximum_leave_days":
                    0,

                "maximum_leave_remaining_classes":
                    0,

                "maximum_leave_display":
                    "0 class(es)",

                "classes_needed_for_75":
                    classes_needed_to_reach_target(
                        actual_attended,
                        actual_total
                    ),

                "maximum_possible_percentage":
                    round(
                        current_percentage,
                        2
                    ),

                "projected_without_leave":
                    round(
                        current_percentage,
                        2
                    ),

                # No new leave is applied to a
                # checkpoint that has already passed.
                "requested_leave":
                    0,

                "requested_leave_classes":
                    0,

                "requested_leave_days":
                    0,

                "requested_leave_remaining_classes":
                    0,

                "requested_leave_display":
                    "0 class(es)",

                "requested_classes_missed":
                    0,

                "requested_projected_attended":
                    actual_attended,

                "requested_projected_total":
                    actual_total,

                "requested_projected_percentage":
                    round(
                        current_percentage,
                        2
                    ),

                "requested_leave_is_safe":
                    True,

                "remaining_safe_leave":
                    0,

                "remaining_safe_leave_classes":
                    0,

                "remaining_safe_leave_days":
                    0,

                "remaining_safe_leave_remaining_classes":
                    0,

                "remaining_safe_leave_display":
                    "0 class(es)",

                "final_attended":
                    actual_attended,

                "final_total":
                    actual_total,

                "final_percentage":
                    round(
                        current_percentage,
                        2
                    ),

                "classes_missed":
                    0
            })

            continue

        # =================================
        # UPCOMING CHECKPOINT
        # =================================

        # ---------------------------------
        # Determine where this calculation
        # starts.
        #
        # If this is the first upcoming
        # checkpoint, use TOMORROW.
        #
        # If a previous upcoming checkpoint
        # was processed immediately before
        # this one, start the next day after
        # that checkpoint.
        # ---------------------------------

        if index == active_index:

            calculation_start = (
                current_date +
                timedelta(days=1)
            )

        else:

            previous_checkpoint_date = (
                CHECKPOINTS[index - 1][1]
            )

            calculation_start = (
                previous_checkpoint_date +
                timedelta(days=1)
            )

        # ---------------------------------
        # Check whether the checkpoint day
        # itself is a teaching day.
        # ---------------------------------

        checkpoint_is_teaching_day = (
            is_teaching_day(
                checkpoint_key
            )
        )

        if checkpoint_is_teaching_day:

            calculation_end = (
                checkpoint_date
            )

        else:

            calculation_end = (
                checkpoint_date -
                timedelta(days=1)
            )

        # ---------------------------------
        # Make sure we never calculate
        # backwards.
        # ---------------------------------

        if calculation_start > calculation_end:

            teaching_days = 0

        else:

            teaching_days = (
                count_teaching_days(
                    calculation_start,
                    calculation_end
                )
            )

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
        # USER'S ACTUAL CHOICE
        # =================================

        raw_requested = (
            requested_leaves.get(
                checkpoint_key,
                0
            )
        )

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
        # PROJECTED WITHOUT LEAVE
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
            -
            requested_leave_classes
        )

        (
            remaining_safe_leave_days,
            remaining_safe_leave_remaining_classes
        ) = divmod(
            remaining_safe_leave_classes,
            CLASSES_PER_DAY
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
                True,

            "state":
                "active"
                if index == active_index
                else "upcoming",

            "is_completed":
                False,

            "is_active":
                index == active_index,

            "is_upcoming":
                True,

            "status":
                status,

            "starting_attended":
                actual_attended,

            "starting_total":
                actual_total,

            "starting_percentage":
                round(
                    starting_percentage,
                    2
                ),

            "teaching_days":
                teaching_days,

            "future_classes":
                future_classes,

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
        # CARRY PROJECTED ATTENDANCE
        # =================================
        #
        # IMPORTANT:
        #
        # Only future checkpoints are carried
        # forward.
        #
        # This means:
        #
        # Before Aug 29:
        #     First choice -> Second start
        #
        # But after Aug 29:
        #     We do NOT apply the old First
        #     choice again.
        #
        # The portal's current attendance is
        # already the real starting point.
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

    # =====================================
    # FINAL CURRENT ATTENDANCE
    # =====================================

    current_percentage = (
        calculate_percentage(
            actual_attended,
            actual_total
        )
    )

    # =====================================
    # SEMESTER COMPLETE?
    # =====================================

    semester_completed = (
        active_index is None
    )

    # =====================================
    # ACTIVE CHECKPOINT
    # =====================================

    if active_index is None:

        active_checkpoint = None

    else:

        active_checkpoint = (
            CHECKPOINTS[
                active_index
            ][0]
        )

    return {

        "current_attended":
            actual_attended,

        "current_total":
            actual_total,

        "current_percentage":
            round(
                current_percentage,
                2
            ),

        "active_checkpoint_index":
            active_index,

        "active_checkpoint":
            active_checkpoint,

        "semester_completed":
            semester_completed,

        "today":
            current_date.strftime(
                "%d %B %Y"
            ),

        "checkpoints":
            results
    }