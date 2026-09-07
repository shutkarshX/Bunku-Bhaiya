# Bunku-Bhaiya

A student attendance dashboard for NIET with subject history and a 75% safe-leave planner.

## What it does

- Retrieves live attendance from the NIET college portal.
- Calculates overall and subject-wise attendance.
- Uses the academic calendar instead of assuming every weekday is a teaching day.
- Plans leave around three sessional checkpoints.
- Carries a user's **planned projection** forward only while a checkpoint is still upcoming.
- Uses current portal attendance after a checkpoint has passed instead of inventing historical attendance.
- Shows subject attendance history in a focused detail view.
- Supports Auto, Light and Dark appearance modes.
- Provides a cinematic loading/login experience while keeping the core dashboard simple.

## Checkpoints

| Checkpoint | Date |
| --- | --- |
| First Sessional | 29 August 2026 |
| Second Sessional | 10 October 2026 |
| Third Sessional | 16 November 2026 |

The calculator treats **75% as safe** (`>= 75%`).

## Architecture

```text
NIET Portal
    ↓
portal.py
    ↓
app.py session data
    ↓
bunk_calculator.py
    ↓
TEIN dashboard
```

### Backend

- `app.py` — Flask routes, session state and dashboard rendering.
- `portal.py` — Playwright-based NIET retrieval and subject-detail capture.
- `bunk_calculator.py` — current calculator wrapper and today's remaining-class adjustment.
- `legacy_bunk_calculator.py` — established checkpoint/calculation engine.
- `academic_calendar.py` — authoritative teaching dates and classes-per-day configuration.

### Frontend

- `templates/dashboard.html` — TEIN page structure and data presentation.
- `templates/tein_checkpoint_body.html` — First Sessional plan body.
- `templates/_subject_attendance_details.html` — legacy subject-detail partial retained for compatibility.
- `static/style.css` — base document styling and shared controls.
- `static/tein-app.css` — single source for the current TEIN application visual system.
- `static/tein.js` — theme, sound and lightweight interaction layer.
- `static/tein-shell.js` — login flow, navigation, subject interactions and leave controls.
- `static/tein-login.css` / `static/tein-login-spider.css` — login scene.
- `static/loading.mp4` — loading media.

The old duplicate TEIN overhaul/dynamic stylesheet layers have been removed so the cascade has one clear application layer.

## NIET email generator

The generated address follows:

```text
2023 → 0231 + branch + student number @niet.co.in
2024 → 0241 + branch + student number @niet.co.in
2025 → 0251 + branch + student number @niet.co.in
2026 → 0261 + branch + student number @niet.co.in
```

## Local setup

Bunk-Bhaiya requires a Flask session secret. Do not commit it.

### Windows PowerShell

```powershell
[Environment]::SetEnvironmentVariable("SECRET_KEY","your-random-secret-here","User")
```

Then install the project's Python dependencies and Playwright browser, and run:

```powershell
python app.py
```

The application listens on port `5000` in the development configuration.

## Useful checks

```powershell
python -m py_compile app.py
python -m py_compile bunk_calculator.py
python -m py_compile portal.py
```

Git:

```powershell
git status
git pull origin ui-changes
```

## Security

- `SECRET_KEY` stays outside the repository.
- College credentials are submitted to the NIET portal for retrieval and are not intentionally persisted as application data.
- Subject-detail responses are held server-side in the current Flask process rather than copied into the cookie session.
