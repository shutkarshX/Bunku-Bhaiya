

def get_planner_token(attendance_data):
    subjects = attendance_data.get("subjects") or []
    if not subjects:
        return None
    return subjects[0].get("_bunkmaster_subject_details_token")


def get_dashboard_step(phase_1_result):
    # The active checkpoint determines the initial screen. Once the user
    # submits a checkpoint choice, sessional_step controls the next screen
    # so a valid "0 classes" choice still advances the flow.
    saved_step = session.get("sessional_step")
    if isinstance(saved_step, int) and 1 <= saved_step <= 4:
        return saved_step

    active_index = phase_1_result.get("active_checkpoint_index")
    if active_index is None:
        return 4
    return active_index + 1


def get_requested_leave_classes(form, step):
    try:
        days = int(form.get(f"leave_{step}_days", 0))
    except (TypeError, ValueError):
        days = 0
    try:
        classes = int(form.get(f"leave_{step}_classes", 0))
    except (TypeError, ValueError):
        classes = 0
    return days_and_classes_to_classes(days, classes)


def build_checkpoint_tracker_data(phase_1_result=None, choice_made=False):
    current_date = date.today()

    if phase_1_result:
        source = phase_1_result.get("checkpoints", [])
        active_index = phase_1_result.get("active_checkpoint_index")
        return [
            {
                "checkpoint": item.get("checkpoint", ""),
                "state_class": (
                    "passed"
                    if item.get("is_completed")
                    else "current"
                    if index == active_index
                    else "upcoming"
                ),
                "icon": (
                    "✓"
                    if item.get("is_completed")
                    else "●"
                    if index == active_index
                    else "○"
                ),
                "label": (
                    "Passed"
                    if item.get("is_completed")
                    else "Current"
                    if index == active_index
                    else "Upcoming"
                ),
                "show_projection": (
                    choice_made
                    and index == active_index
                    and not item.get("is_completed")
                ),
                "starting_percentage": item.get("starting_percentage", 0),
                "projected_percentage": item.get("requested_projected_percentage", 0),
                "projected_attended": item.get("requested_projected_attended", 0),
                "projected_total": item.get("requested_projected_total", 0),
            }
            for index, item in enumerate(source)
        ]