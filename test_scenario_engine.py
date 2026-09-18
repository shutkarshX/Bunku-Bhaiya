import unittest
from unittest.mock import patch

from scenario_engine import (
    calculate_today_scenario,
    calculate_date_range_scenario,
    calculate_date_selection_scenario,
    calculate_until_date_scenario,
    get_effective_starting_state,
)


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
        self.assertFalse(result["valid"])
        self.assertEqual(result["starting"]["today_remaining"], 5)


class UntilDateScenarioTests(unittest.TestCase):
    def test_today_uses_event_adjusted_remaining_classes(self):
        event = {"date": "2026-09-18", "classes": 3, "attended": True}
        result = calculate_until_date_scenario(attendance(8), event, "2026-09-18", attended=2, leave=3)
        self.assertTrue(result["valid"])
        self.assertEqual(result["future_classes"], 5)
        self.assertEqual(result["planned_classes"], 5)
        self.assertEqual(result["projected_attended"], 248)
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


class DateRangeScenarioTests(unittest.TestCase):
    def test_today_to_future_range_counts_today_and_later_teaching_days(self):
        result = calculate_date_range_scenario(attendance(8), None, "2026-09-18", "2026-09-21", attended=8, leave=8)
        self.assertTrue(result["valid"])
        self.assertEqual(result["future_classes"], 16)
        self.assertEqual(result["remaining_after_plan"], 0)

    def test_future_to_future_range_counts_only_selected_range(self):
        result = calculate_date_range_scenario(attendance(8), None, "2026-09-21", "2026-09-22", attended=8, leave=8)
        self.assertTrue(result["valid"])
        self.assertEqual(result["future_classes"], 16)
        self.assertEqual(result["planned_classes"], 16)

    def test_range_rejects_end_before_start(self):
        result = calculate_date_range_scenario(attendance(8), None, "2026-09-22", "2026-09-21", attended=0, leave=0)
        self.assertFalse(result["valid"])

    def test_range_rejects_past_start(self):
        result = calculate_date_range_scenario(attendance(8), None, "2026-09-17", "2026-09-21", attended=0, leave=0)
        self.assertFalse(result["valid"])

    def test_future_to_future_range_does_not_apply_today_event(self):
        event = {"date": "2026-09-18", "classes": 3, "attended": True}
        result = calculate_date_range_scenario(attendance(8), event, "2026-09-21", "2026-09-21", attended=8, leave=0)
        self.assertTrue(result["valid"])
        self.assertEqual(result["future_classes"], 8)




class DateSelectionScenarioTests(unittest.TestCase):
    def test_selected_days_convert_to_attend_and_bunk_classes(self):
        plan = {
            "2026-09-21": {"action": "attend"},
            "2026-09-23": {"action": "bunk"},
        }
        result = calculate_date_selection_scenario(attendance(8), None, plan)
        self.assertTrue(result["valid"])
        self.assertEqual(result["attended_days"], 1)
        self.assertEqual(result["bunk_days"], 1)
        self.assertEqual(result["attended"], 8)
        self.assertEqual(result["leave"], 8)
        self.assertEqual(result["planned_classes"], 16)

    def test_today_selected_day_uses_remaining_classes(self):
        plan = {"2026-09-18": {"action": "attend"}}
        result = calculate_date_selection_scenario(attendance(5), None, plan)
        self.assertTrue(result["valid"])
        self.assertEqual(result["attended"], 5)
        self.assertEqual(result["planned_classes"], 5)

    def test_selected_day_can_use_custom_class_count(self):
        plan = {"2026-09-21": {"action": "bunk", "classes": 3}}
        result = calculate_date_selection_scenario(attendance(8), None, plan)
        self.assertTrue(result["valid"])
        self.assertEqual(result["bunk_days"], 1)
        self.assertEqual(result["leave"], 3)
        self.assertEqual(result["planned_classes"], 3)

    def test_non_teaching_selected_date_is_rejected(self):
        plan = {"2026-09-19": {"action": "bunk"}}
        result = calculate_date_selection_scenario(attendance(8), None, plan)
        self.assertFalse(result["valid"])


if __name__ == "__main__":
    unittest.main()
