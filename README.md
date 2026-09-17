# Bunku-Bhaiya

> A smart college attendance dashboard and safe-bunk calculator built for students.

Bunku-Bhaiya retrieves college attendance, normalizes it into portal/site/effective attendance, uses the academic calendar for teaching-day calculations, and projects safe leave around sessional checkpoints.

## ✦ What it does

- Retrieves attendance from the college portal
- Shows overall and subject-wise attendance
- Separates portal attendance from site attendance and effective attendance
- Treats already-held, unmarked/frozen classes as present for effective attendance
- Keeps future classes separate from current attendance
- Uses the academic calendar to identify actual teaching days
- Calculates safe leave at the 75% attendance threshold
- Handles sessional checkpoint calculations
- Preserves portal subject-wise attendance details for the dashboard
- Provides a student-focused web dashboard

## → Attendance model

```text
P = portal-posted present classes
A = portal-posted absent classes
U = already-held, unmarked/frozen classes

TOTAL = P + A + U

Portal attendance    = P / (P + A)
Site attendance      = P / TOTAL
Effective attendance = (P + U) / TOTAL
```

Future classes are planning inputs only and are not included in current, site, or effective attendance totals.

## → How it works

```text
College portal
      ↓
portal.py
      ↓
Raw attendance + subject details
      ↓
attendance_state.py
      ↓
P / A / U normalized state
      ↓
bunk_calculator.py
      ↓
Safe-bunk + checkpoint projections
      ↓
Flask dashboard
```

1. The student enters their college portal credentials.
2. Bunku-Bhaiya retrieves aggregate attendance and subject-wise portal data.
3. The attendance state is normalized into present, absent, and unmarked classes.
4. The academic calendar determines actual teaching days.
5. The calculator uses effective attendance as the planning starting point.
6. The calculator projects safe leave while maintaining at least 75% attendance.
7. The dashboard displays the resulting attendance and checkpoint information.

## 🧩 Tech

`Python` · `Flask` · `Playwright` · `JavaScript` · `HTML/CSS`

## 📁 Project structure

```text
Bunku-Bhaiya/
├── app.py                    # Flask routes and session flow
├── portal.py                 # NIET portal retrieval
├── attendance_state.py       # P/A/U attendance normalization
├── bunk_calculator.py        # Attendance planning and projections
├── academic_calendar.py      # Teaching-day calendar
├── test_portal.py            # Manual portal diagnostic
├── .gitignore
├── static/
│   ├── style.css
│   └── loading.mp4
└── templates/
    ├── dashboard.html
    └── _subject_attendance_details.html
```

## ⚙️ Configuration

Bunku-Bhaiya uses a Flask session with a secret key provided through the `SECRET_KEY` environment variable.

The secret key is intentionally not stored in the repository.

### Windows PowerShell

```powershell
[Environment]::SetEnvironmentVariable("SECRET_KEY","your-random-secret-here","User")
```

Restart the terminal after setting the variable, then run the application normally.

## 🔐 Privacy & safety

Credentials are used for the college-portal retrieval flow and should never be committed to Git. Keep secrets in environment variables and do not share `.env` files or personal portal data.

## 📌 Project status

Bunku-Bhaiya is actively evolving. `version-D` is the working branch for the current attendance-model and calculator work; `main` is kept as the stable baseline.

## 🔗 Links

[GitHub repository](https://github.com/shutkarshX/Bunku-Bhaiya)
