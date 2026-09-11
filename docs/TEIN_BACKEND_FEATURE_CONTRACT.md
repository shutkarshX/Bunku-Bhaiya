# TEIN — Backend & Feature Contract v1

**Project:** Bunku-Bhaiya / TEIN  
**Purpose:** Preserve backend behavior and application features while the UI is redesigned.

## Core Architecture Rule

> **Backend = source of truth. UI = presentation, interaction, and navigation.**

The UI redesign must not silently change attendance calculations, planner logic, portal behavior, session state, or feature availability.

## 1. Authentication / Login

- Manual NIET Cloud email/username entry.
- Generated NIET email/username using admission year, branch, and student number.
- Format: `{yearCode}{branch}{studentNumber}@niet.co.in`
- `yearCode = 0 + last two digits of year + 1` (e.g. 2026 → 0261).
- Credentials are submitted to Flask and used for portal authentication; they are not persistent attendance data.

## 2. Attendance Retrieval

**Route:** `POST /get-attendance`

Inputs: `username`, `password`.

The backend authenticates against NIET Cloud, retrieves courses and subject-wise attendance, calculates aggregate attendance, today's logged/remaining classes and unmarked classes, stores attendance in the Flask session, resets leave/planner state, and runs the planning phase.

Errors must distinguish portal unavailability, portal login failure, and unexpected retrieval failures. Loading state must be supported.

## 3. Core Attendance Data

The backend is authoritative for:

- Total attended classes
- Total absent classes
- Total classes
- Overall attendance percentage
- Subject-wise attendance
- Today's logged classes
- Today's remaining classes
- Unmarked classes
- Checkpoint/planner information

The frontend must display these values rather than implementing competing calculations.

## 4. Today's Attendance

Attendance records dated for the current day are inspected. Consecutive lectures are accounted for using portal data.

Metadata:

- `_bunkmaster_today_logged`
- `_bunkmaster_remaining_today`

On a teaching day: `remaining_today = max(0, 8 - today_logged)`. On a non-teaching day: `remaining_today = 0`.

Today's remaining classes are future classes and must not be treated as already attended.

## 5. Unmarked Classes

Metadata: `_bunkmaster_unmarked_classes`.

Unmarked classes are treated as already happened/attended:

```text
effective_attended = aggregate_attended + unmarked_classes
effective_total = aggregate_total + unmarked_classes
```

They are **not future classes** and must never be double-counted.

## 6. Attendance Planner

The planner answers:

- How many classes can be safely missed?
- What happens if leave is taken?
- What will projected attendance become?
- Can attendance remain at/above the required threshold?
- What is the next important checkpoint?

The existing backend calculator remains authoritative.

## 7. Checkpoints

Current configured checkpoints:

- `2026-08-29`
- `2026-10-10`
- `2026-11-16`

The backend determines the active checkpoint and future-class information. UI hierarchy: past = history, current = action, future = preview.

## 8. Planner Progression

Routes:

- `POST /sessional-1`
- `POST /sessional-2`
- `POST /sessional-3`

Progression:

```text
Initial → Step 1
Sessional 1 → Step 2
Sessional 2 → Step 3
Sessional 3 → Complete / Step 4
```

Stored in session as `planner_step`. Client-side state must not replace server-side progression.

## 9. Leave Selection

Leave information is stored in `selected_leaves`. Fresh attendance retrieval resets leave selections and planner progression.

Leave calculations continue to use the existing calculator logic.

## 10. 75% Attendance Logic

The existing attendance threshold and formulas must remain unchanged. UI should clearly communicate safe, at-risk, below-threshold, maximum possible attendance, and safe/usable leave where applicable.

## 11. Leave Calculator

The calculator considers effective current attendance, future classes, today's remaining classes, selected leaves, checkpoint boundaries, threshold, and maximum possible attendance.

Today's remaining classes are added to the active checkpoint's future-class pool before projections are calculated.

## 12. Subjects

Subjects are the source/details view. At minimum show subject name, attendance percentage, attended classes, total classes, and relevant status/indicator.

> Home tells the user where they stand. Subjects explain where the numbers came from.

## 13. Subject Details

Raw subject-wise attendance details are cached server-side using `_bunkmaster_subject_details_token`.

Details can include date, lecture time, session, attendance status, and other raw record information. Current desktop table fields are:

`Sr. No. | Date | Lecture Time | Session | Status`

The details cache is currently in-memory and may be lost after Flask restart/reload. UI must handle missing details gracefully.

## 14. Home

**Purpose: Status — “Where am I right now?”**

Prioritize overall attendance, current status, total/attended/absent counts, today's useful attendance context, next checkpoint, and relevant history. Do not duplicate the full planner.

## 15. Plan

**Purpose: Action — “What can I do?”**

Prioritize active checkpoint, leave controls, safe leave, projected attendance, threshold/status, sessional progression, and next action.

## 16. Subjects

**Purpose: Source/details — “Where did these numbers come from?”**

Prioritize subject attendance and drill-down into detailed attendance records. Desktop tables may become mobile cards/expandable details without losing data.

## 17. More

Secondary utilities/settings such as theme, sound, app information, reset/logout, PWA-related utilities, and other non-primary settings. Core attendance actions should remain in the primary views.

## 18. Navigation

Primary navigation:

`Home | Plan | Subjects | More`

The active destination must be visually obvious and routing must remain compatible with existing Flask view selection.

## 19. Theme

Preserve system/light/dark behavior and stored preference. Theme is presentation-only and must not affect attendance state.

## 20. Sound & Motion

Preserve optional interaction sounds, animated numbers, attendance visuals, button/card effects, and loading/login sequences. These are enhancements only; core functionality must work without them.

## 21. Android-First Requirement

Primary target: **Android phones**, with **Pixel 7** as the main development profile. Also check **Samsung Galaxy S20 Ultra** and **Samsung Galaxy S8+**.

Requirements:

- Touch targets generally ≥48px.
- No accidental page overflow.
- Readable text without zooming.
- Comfortable narrow-screen cards and controls.
- Mobile-native subject details where appropriate.
- Desktop remains usable.

## 22. PWA

Preserve:

- `/static/manifest.webmanifest`
- `/static/tein-icon.svg`
- `/static/tein-sw.js`
- `/sw.js`

Do not remove installability-related behavior.

## 23. Loading & Errors

Attendance retrieval may take time because it communicates with the academic portal. Provide clear loading feedback, prevent accidental duplicate submissions, and recover cleanly from errors.

## 24. Reset

**Route:** `GET /reset`

Reset clears attendance/planner session state. Keep reset/logout secondary rather than a primary action.

## 25. Session State

Important server-side session values:

```text
attendance_data
selected_leaves
planner_step
```

Client-side state may control visual behavior but must not become authoritative for attendance or planner progression.

## 26. Backend Responsibilities

### `app.py`
Flask app, routes, session state, attendance endpoint, planner progression, dashboard view selection, error handling, and `/sw.js`.

### `portal.py`
NIET Cloud automation, authentication, course/subject retrieval, subject attendance retrieval, today's attendance, unmarked classes, and subject-detail caching.

### `bunk_calculator.py`
Effective attendance, future classes, today's remaining classes, checkpoints, projections, leave calculations, and status.

### Templates/static frontend
Presentation, interaction, navigation, responsive layout, theme/sound/motion, and PWA frontend behavior.

## 27. Non-Negotiable Regression Checklist

Before/after UI changes verify:

- Manual login
- Generated email
- Attendance retrieval
- Portal login/unavailable errors
- Aggregate attendance
- Today's logged/remaining classes
- Unmarked classes and no double counting
- Planner calculations
- 75% logic
- Leave calculations
- Sessional 1/2/3 progression
- Subject list
- Subject details
- Home / Plan / Subjects / More
- Theme / sound / reset
- PWA manifest / service worker
- Android layouts
- Desktop usability

## 28. UI Redesign Boundary

UI may change layout, typography, spacing, cards, navigation appearance, mobile hierarchy, table presentation, animation style, and interaction patterns.

Without an explicit backend reason, do **not** change attendance formulas, portal scraping, checkpoint logic, sessional progression, leave calculations, authentication rules, or server-side source-of-truth behavior.

## 29. Product Model

```text
Home     → Status   → Where am I?
Plan     → Action   → What can I do?
Subjects → Source   → Where did these numbers come from?
More     → Utilities → What else do I need?
```

TEIN should feel like a focused attendance utility, not a generic dashboard.

## 30. Definition of Done — UI vNext

1. All existing backend features still work.
2. Attendance calculations remain unchanged.
3. Android is the primary polished experience.
4. Home, Plan, Subjects, and More have distinct purposes.
5. Planner is comfortable with touch.
6. Subject details are readable on mobile.
7. Loading/error states are clear.
8. Theme, sound, and PWA remain functional.
9. No important backend data is removed or hidden.
10. The safe `ui-changes` baseline remains recoverable throughout development.

---

**Version:** v1  
**Role:** Backend/feature contract for the TEIN UI redesign  
**Principle:** Preserve behavior first. Redesign presentation second.
