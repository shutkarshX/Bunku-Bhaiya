"""Pure simulation helpers for the TEIN development Scenario Lab."""

TARGET = 75.0


def _pct(attended, total):
    return round((attended / total) * 100, 2) if total else 0.0


def _status(attended, total, future):
    current = _pct(attended, total)
    if current >= TARGET:
        return "safe"
    maximum = _pct(attended + future, total + future)
    return "recovery" if maximum >= TARGET else "impossible"


def run_lab(attended, total, scheduled_today, posted_today, actual_remaining_today, missed_today, checkpoint_future):
    """Run a temporary scenario without touching Flask session or portal data."""
    attended = max(0, int(attended))
    total = max(attended, int(total))
    scheduled_today = max(0, int(scheduled_today))
    posted_today = max(0, min(int(posted_today), scheduled_today))
    actual_remaining_today = max(0, min(int(actual_remaining_today), scheduled_today - posted_today))
    missed_today = max(0, min(int(missed_today), actual_remaining_today))
    checkpoint_future = max(0, int(checkpoint_future))

    pending_today = max(0, scheduled_today - posted_today)
    effective_future_today = actual_remaining_today
    attended_after_today = attended + effective_future_today - missed_today
    total_after_today = total + effective_future_today
    checkpoint_future_after_today = max(0, checkpoint_future - pending_today + actual_remaining_today)
    checkpoint_attended = attended_after_today + max(0, checkpoint_future_after_today - actual_remaining_today)
    checkpoint_total = total_after_today + max(0, checkpoint_future_after_today - actual_remaining_today)

    return {
        "current": {"attended": attended, "total": total, "percentage": _pct(attended, total)},
        "today": {
            "scheduled": scheduled_today,
            "posted": posted_today,
            "pending": pending_today,
            "remaining": actual_remaining_today,
            "missed": missed_today,
            "attended": attended_after_today,
            "total": total_after_today,
            "percentage": _pct(attended_after_today, total_after_today),
        },
        "checkpoint": {
            "future_classes": checkpoint_future_after_today,
            "attended": checkpoint_attended,
            "total": checkpoint_total,
            "percentage": _pct(checkpoint_attended, checkpoint_total),
            "status": _status(attended_after_today, total_after_today, max(0, checkpoint_future_after_today - actual_remaining_today)),
        },
        "integrity": {
            "pending_preserved": pending_today >= 0,
            "real_attendance_mutated": False,
            "simulation_only": True,
        },
    }
