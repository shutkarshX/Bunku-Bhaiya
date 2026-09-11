import json
from pathlib import Path

from scenario_planner import calculate_scenario


def sample_attendance():
    return {
        "subjects": [
            {
                "_bunkmaster_remaining_today": 4,
                "_bunkmaster_unmarked_classes": 1,
            }
        ],
        "total_attended": 40,
        "total_classes": 50,
    }


def sample_phase():
    return {
        "active_checkpoint_index": 0,
        "checkpoints": [
            {
                "name": "Second Sessional",
                "date": "10 October 2026",
                "future_classes": 20,
            }
        ],
    }


def test_today_scenario_uses_only_remaining_today():
    result = calculate_scenario(sample_attendance(), sample_phase(), "today", 1)
    assert result["available_classes"] == 4
    assert result["classes_missed"] == 1
    assert result["today"]["missed"] == 1
    assert result["checkpoint"]["missed"] == 1


def test_today_scenario_clamps_to_available_classes():
    result = calculate_scenario(sample_attendance(), sample_phase(), "today", 99)
    assert result["classes_missed"] == 4
    assert result["today"]["missed"] == 4


def test_checkpoint_scenario_uses_checkpoint_future_classes():
    result = calculate_scenario(sample_attendance(), sample_phase(), "checkpoint", 3)
    assert result["available_classes"] == 20
    assert result["classes_missed"] == 3
    assert result["checkpoint"]["missed"] == 3
    assert result["today"] is None


def test_scenario_does_not_mutate_attendance():
    attendance = sample_attendance()
    calculate_scenario(attendance, sample_phase(), "today", 2)
    assert attendance["total_attended"] == 40
    assert attendance["total_classes"] == 50


def test_sep11_auditorium_fixture_can_simulate_no_more_classes_today():
    fixture_path = Path(__file__).parent / "fixtures" / "sep11_2026_auditorium.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    attendance = fixture["attendance"]
    phase = fixture["phase"]

    automatic = calculate_scenario(attendance, phase, "today", 0)
    assert automatic["today_remaining"] == 3
    assert automatic["portal_today_remaining"] == 3
    assert automatic["today_override_active"] is False

    simulated = calculate_scenario(
        attendance,
        phase,
        "today",
        0,
        today_remaining_override=0,
    )

    assert simulated["today_remaining"] == 0
    assert simulated["portal_today_remaining"] == 3
    assert simulated["today_override_active"] is True
    assert simulated["available_classes"] == 0
    assert simulated["today"]["total"] == automatic["today"]["total"] - 3
    assert simulated["checkpoint"]["total"] == automatic["checkpoint"]["total"] - 3
    assert attendance["total_attended"] == 40
    assert attendance["total_classes"] == 50


def test_sep11_fixture_can_simulate_partial_remaining_classes():
    fixture_path = Path(__file__).parent / "fixtures" / "sep11_2026_auditorium.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    result = calculate_scenario(
        fixture["attendance"],
        fixture["phase"],
        "today",
        1,
        today_remaining_override=2,
    )

    assert result["portal_today_remaining"] == 3
    assert result["today_remaining"] == 2
    assert result["available_classes"] == 2
    assert result["classes_missed"] == 1
    assert result["today"]["missed"] == 1
