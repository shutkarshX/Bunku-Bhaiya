"""Single source of truth for portal attendance state.

P = portal-posted present classes
A = portal-posted absent classes
U = already-held, unmarked/frozen classes

Portal attendance    = P / (P + A)
Site attendance      = P / (P + A + U)
Effective attendance = (P + U) / (P + A + U)

Future classes are not part of this state. They belong to planning.
"""


def _safe_int(value, default=0):
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return default


def _percentage(attended, total):
    if total <= 0:
        return 0.0
    return (attended / total) * 100


def build_attendance_state(attendance_data):
    """Normalize raw portal subjects into one stable P/A/U state."""
    attendance_data = attendance_data or {}
    subjects = attendance_data.get("subjects") or []

    # Subjects are the authoritative raw portal records. The stored totals
    # are retained only as a compatibility fallback for older session data.
    if subjects:
        portal_present = sum(
            _safe_int(subject.get("attendedLecture"))
            for subject in subjects
            if isinstance(subject, dict)
        )
        portal_absent = sum(
            _safe_int(subject.get("absentLecture"))
            for subject in subjects
            if isinstance(subject, dict)
        )
    else:
        portal_present = _safe_int(attendance_data.get("total_attended"))
        portal_absent = _safe_int(attendance_data.get("total_absent"))

    unmarked = sum(
        _safe_int(subject.get("totalUnFreezedAttendance"))
        for subject in subjects
        if isinstance(subject, dict)
    )

    # Compatibility with sessions created before the normalized state layer.
    if unmarked == 0 and subjects and isinstance(subjects[0], dict):
        unmarked = _safe_int(subjects[0].get("_bunkmaster_unmarked_classes"))

    portal_total = portal_present + portal_absent
    site_total = portal_total + unmarked
    effective_present = portal_present + unmarked

    return {
        "present": portal_present,
        "absent": portal_absent,
        "unmarked": unmarked,
        "portal": {
            "present": portal_present,
            "absent": portal_absent,
            "total": portal_total,
            "percentage": round(_percentage(portal_present, portal_total), 2),
        },
        "site": {
            "present": portal_present,
            "total": site_total,
            "percentage": round(_percentage(portal_present, site_total), 2),
        },
        "effective": {
            "present": effective_present,
            "total": site_total,
            "percentage": round(_percentage(effective_present, site_total), 2),
        },
    }


def apply_effective_state(attendance_data, state=None):
    """Return a calculator-compatible copy using the normalized state."""
    if state is None:
        state = build_attendance_state(attendance_data)

    effective_attendance = dict(attendance_data or {})
    effective_attendance["total_attended"] = state["effective"]["present"]
    effective_attendance["total_classes"] = state["effective"]["total"]
    effective_attendance["overall_percentage"] = state["effective"]["percentage"]
    return effective_attendance
