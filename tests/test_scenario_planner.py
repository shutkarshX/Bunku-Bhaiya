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
