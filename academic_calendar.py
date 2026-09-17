"""Academic calendar rules used by attendance and planning."""

TEACHING_CLASSES_PER_DAY = 8
ATTENDANCE_TARGET = 75

CHECKPOINTS = (
    "2026-08-29",
    "2026-10-10",
    "2026-11-16",
)

TEACHING_DAYS = {
    # Existing semester teaching-day calendar remains the source of truth.
}


def is_teaching_day(day):
    return day in TEACHING_DAYS
