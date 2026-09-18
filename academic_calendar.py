# =========================================
# BUNKMASTER - ACADEMIC CALENDAR
# NIET Academic Calendar 2026-2027 (Odd Sem.)
# =========================================

TEACHING_CLASSES_PER_DAY = 8
ATTENDANCE_TARGET = 75

# Milestone/checkpoint dates. These are independent from teaching days:
# a checkpoint may also be a working day if that date is present in TEACHING_DAYS.
CHECKPOINTS = (
    ("First Sessional", "2026-08-29"),
    ("Second Sessional", "2026-10-10"),
    ("Third Sessional", "2026-11-16"),
)

# Visual calendar events. These describe what a date represents; they do NOT
# decide whether attendance classes exist. TEACHING_DAYS remains the source
# of truth for attendance-bearing days.
CALENDAR_EVENTS = {
    "2026-08-29": {"type": "detain_list", "label": "Detain List"},
    "2026-10-10": {"type": "detain_list", "label": "Detain List"},
    "2026-11-16": {"type": "detain_list", "label": "Detain List"},

    "2026-08-31": {"type": "sessional_exam", "label": "First Sessional Exam"},
    "2026-09-01": {"type": "sessional_exam", "label": "First Sessional Exam"},
    "2026-09-02": {"type": "sessional_exam", "label": "First Sessional Exam"},
    "2026-09-03": {"type": "sessional_exam", "label": "First Sessional Exam"},

    "2026-10-12": {"type": "sessional_exam", "label": "Second Sessional Exam"},
    "2026-10-13": {"type": "sessional_exam", "label": "Second Sessional Exam"},
    "2026-10-14": {"type": "sessional_exam", "label": "Second Sessional Exam"},
    "2026-10-15": {"type": "sessional_exam", "label": "Second Sessional Exam"},

    "2026-11-17": {"type": "sessional_exam", "label": "Third Sessional Exam"},
    "2026-11-18": {"type": "sessional_exam", "label": "Third Sessional Exam"},
    "2026-11-19": {"type": "sessional_exam", "label": "Third Sessional Exam"},
    "2026-11-20": {"type": "sessional_exam", "label": "Third Sessional Exam"},
}

# ONLY these dates are teaching days.
# Weekdays are NOT automatically teaching days.
# Sessional examination days are teaching days because attendance is recorded
# for the normal 8 classes on those days.
TEACHING_DAYS = {

    # July 2026
    "2026-07-13", "2026-07-14", "2026-07-15", "2026-07-16",
    "2026-07-17", "2026-07-20", "2026-07-21", "2026-07-22",
    "2026-07-23", "2026-07-24", "2026-07-27", "2026-07-28",
    "2026-07-29", "2026-07-30", "2026-07-31",

    # August 2026
    "2026-08-03", "2026-08-04", "2026-08-05", "2026-08-06",
    "2026-08-07", "2026-08-10", "2026-08-11", "2026-08-12",
    "2026-08-13", "2026-08-14", "2026-08-17", "2026-08-18",
    "2026-08-19", "2026-08-20", "2026-08-21", "2026-08-24",
    "2026-08-25", "2026-08-27",

    # September 2026
    "2026-09-07", "2026-09-08", "2026-09-09", "2026-09-10",
    "2026-09-11", "2026-09-14", "2026-09-15", "2026-09-16",
    "2026-09-17", "2026-09-18", "2026-09-21", "2026-09-22",
    "2026-09-23", "2026-09-24", "2026-09-25", "2026-09-28",
    "2026-09-29", "2026-09-30",

    # October 2026
    "2026-10-01", "2026-10-05", "2026-10-06", "2026-10-07",
    "2026-10-08", "2026-10-09", "2026-10-10", "2026-10-16",
    "2026-10-19", "2026-10-21", "2026-10-22", "2026-10-23",
    "2026-10-24", "2026-10-26", "2026-10-27", "2026-10-28",
    "2026-10-29", "2026-10-30",

    # November 2026
    "2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05",
    "2026-11-06", "2026-11-16",

    # Sessional examination days
    # First Sessional Exam: Aug 31 - Sep 3
    "2026-08-31", "2026-09-01", "2026-09-02", "2026-09-03",

    # Second Sessional Exam: Oct 12 - Oct 15
    "2026-10-12", "2026-10-13", "2026-10-14", "2026-10-15",

    # Third Sessional Exam: Nov 17 - Nov 20
    "2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20",
}


def is_teaching_day(date_string):
    return date_string in TEACHING_DAYS
