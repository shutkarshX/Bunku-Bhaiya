# TEIN Planner — Unified Scenario Spec

## Goal

TEIN uses one planner model for two scopes:

- **Today** — “What if I bunk today?”
- **Checkpoint** — “How much can I bunk overall?”

These are not two separate planners. They are two views of the same scenario calculation model.

## Shared model

A scenario contains:

- `scope`: `today` or `checkpoint`
- `classes_missed`: non-negative integer

The scenario is a simulation only. It must not modify `selected_leaves` or `planner_step` unless the user explicitly commits a leave through the existing planner flow.

## Today scope

Available classes are the backend's `_bunkmaster_remaining_today` value.

The system must not require or invent a timetable. It does not know the subject or exact time of remaining classes.

Interpretation:

> Miss X of today's remaining classes and attend the rest.

The result should include:

- attendance after today's scenario
- projected attendance at the active checkpoint
- safe / recovery / impossible status as appropriate
- remaining safe leave context where useful

## Checkpoint scope

Available classes are the future classes already calculated for the active checkpoint, including today's remaining classes.

Interpretation:

> Miss X classes before the checkpoint and attend the rest.

The existing checkpoint planner remains the source of truth for its established leave calculations and progression.

## Shared UI

The UI should expose a compact scope switch:

`TODAY | CHECKPOINT`

Both modes use the same controls and result area. Switching scope changes only the calculation context.

Suggested wording:

- Today: **What if I bunk today?**
- Checkpoint: **How much can I bunk?**

## Data rules

- Today's remaining classes are future classes.
- Unmarked classes are already happened/attended classes and must not be counted as future classes.
- No timetable is required.
- Do not allow a scenario to miss more classes than are available in its selected scope.
- Scenario state is separate from persisted planner leave state.

## Backend architecture

Preferred structure:

```text
Attendance data
      ↓
Scenario adapter
      ↓
Unified scenario calculation
      ↓
TODAY / CHECKPOINT result
```

The implementation should reuse the existing attendance and calculator functions wherever possible rather than creating a second independent attendance formula.

## Future extension

If timetable data becomes available later, subject-specific choices can be added as an optional input without changing the basic scenario model.

## Acceptance criteria

1. User can switch between Today and Checkpoint without leaving the planner.
2. Both modes use the same core scenario controls.
3. Today mode works using only data TEIN already receives.
4. Checkpoint mode preserves the existing planner behavior.
5. Simulation does not mutate saved planner state.
6. Unmarked classes are never double-counted.
7. No timetable dependency is introduced.
