# Bunku-Bhaiya

> A smart college attendance dashboard and safe-bunk calculator built for students.

Bunku-Bhaiya retrieves college attendance, turns it into subject-level insights, and calculates how many teaching days can be missed while maintaining the required attendance target.

## ✦ What it does

- Retrieves attendance from the college portal
- Shows overall and subject-wise attendance
- Uses the academic calendar to identify actual teaching days
- Calculates safe leave at the 75% attendance threshold
- Handles sessional checkpoint calculations
- Lets the student choose whether a teaching-day checkpoint should count
- Provides a simple student-focused web dashboard
- Shows a loading state while attendance is being retrieved

## → How it works

```text
College portal
      ↓
Attendance retrieval
      ↓
Subject-wise data
      ↓
Academic calendar
      ↓
Attendance + teaching-day calculations
      ↓
Safe-bunk projection
      ↓
Student dashboard
```

1. The student enters their college portal credentials.
2. Bunku-Bhaiya retrieves the current subject-wise attendance.
3. The application calculates the overall attendance.
4. The academic calendar determines which dates are actual teaching days.
5. The student can choose whether a teaching-day checkpoint should be included.
6. The calculator determines the maximum number of teaching days that can be missed while maintaining at least 75% attendance.
7. The projected attendance is displayed on the dashboard.

## 🧩 Tech

`Python` · `Flask` · `Playwright` · `JavaScript` · `HTML/CSS`

## 📁 Project structure

```text
Bunku-Bhaiya/
├── app.py
├── portal.py
├── bunk_calculator.py
├── academic_calendar.py
├── test_portal.py
├── .gitignore
├── static/
│   ├── style.css
│   └── loading.mp4
└── templates/
    └── dashboard.html
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

Bunku-Bhaiya is an actively evolving student-focused project. The calculation logic and UI are being refined as the college workflow changes.

## 🔗 Links

[GitHub repository](https://github.com/shutkarshX/Bunku-Bhaiya)
