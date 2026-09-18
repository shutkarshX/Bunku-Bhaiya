import unittest
from unittest.mock import patch

from scenario_engine import (calculate_today_scenario, calculate_until_date_scenario, get_effective_starting_state)


def attendance(remaining=8):
    return {
        "subjects": [{
            "attendedLecture": 243,
            "absentLecture": 20,
            "totalUnFreezedAttendance": 0,
            "_bunkmaster_remaining_today": remaining,
        }],
        "total_attended": 243,
        "total_absent": 20,
        "total_classes": 263,
    }


class TodayScenarioTests(unittest.TestCase):
    def test_no_event_keeps_all_remaining_classes(self):
        state = get_effective_starting_state(attendance(8), None)
        self.assertEqual(state["today_remaining"], 8)
        self.assertEqual(state["attended"], 243)
        self.assertEqual(state["total"], 263)

    def test_attended_event_moves_event_classes_into_starting_state(self):
        event = {"date": "2026-09-18", "classes": 3, "attended": True}
        with patch("scenario_engine.date") as today:
            today.today.return_value.isoformat.return_value = "2026-09-18"
            state = get_effective_starting_state(attendance(8), event)
        self.assertEqual(state["event_classes"], 3)
        self.assertEqual(state["event_attended"], 3)
        self.assertEqual(state["today_remaining"], 5)
        self.assertEqual(state["attended"], 246)
        self.assertEqual(state["total"], 266)

    def test_unattended_event_is_counted_as_classes_but_not_attended(self):
        event = {"date": "2026-09-18", "classes": 3, "attended": False}
        with patch("scenario_engine.date") as today:
            today.today.return_value.isoformat.return_value = "2026-09-18"
            state = get_effective_starting_state(attendance(8), event)
        self.assertEqual(state["today_remaining"], 5)
        self.assertEqual(state["attended"], 243)
        self.assertEqual(state["total"], 266)

    def test_stale_event_is_ignored(self):
        event = {"date": "2026-09-17", "classes": 3, "attended": True}
        with patch("scenario_engine.date") as today:
            today.today.return_value.isoformat.return_value = "2026-09-18"
            state = get_effective_starting_state(attendance(8), event)
        self.assertEqual(state["today_remaining"], 8)
        self.assertEqual(state["attended"], 243)
        self.assertEqual(state["total"], 263)

    def test_today_plan_cannot_exceed_effective_remaining_pool(self):
        event = {"date": "2026-09-18", "classes": 3, "attended": True}
        with patch("scenario_engine.date") as today:
            today.today.return_value.isoformat.return_value = "2026-09-18"
            result = calculate_today_scenario(attendance(8), event, attended=3, leave=3)
        self.assertTrue(result["valid"])
        self.assertEqual(result["planned_classes"], 6)
        self.assertEqual(result["remaining_after_plan"], 0)


class UntilDateScenarioTests(unittest.TestCase):
    def test_today_uses_event_adjusted_remaining_classes(self):
        event = {"date": "2026-09-18", "classes": 3, "attended": True}
        result = calculate_until_date_scenario(attendance(8), event, "2026-09-18", attended=2, leave=3)
        self.assertTrue(result["valid"])
        self.assertEqual(result["future_classes"], 5)
        self.assertEqual(result["planned_classes"], 5)
        self.assertEqual(result["projected_attended"], 251)
        self.assertEqual(result["projected_total"], 271)

    def test_until_date_rejects_plan_above_available_classes(self):
        result = calculate_until_date_scenario(attendance(2), None, "2026-09-18", attended=2, leave=1)
        self.assertFalse(result["valid"])
        self.assertEqual(result["future_classes"], 2)

    def test_until_date_rejects_past_date(self):
        result = calculate_until_date_scenario(attendance(8), None, "2026-09-17", attended=0, leave=0)
        self.assertFalse(result["valid"])

    def test_until_date_counts_only_listed_teaching_days(self):
        result = calculate_until_date_scenario(attendance(8), None, "2026-09-21", attended=8, leave=8)
        self.assertTrue(result["valid"])
        self.assertEqual(result["future_classes"], 16)
        self.assertEqual(result["remaining_after_plan"], 0)


if __name__ == "__main__":
    unittest.main()
