\# Bunku-Bhaiya



A smart college attendance dashboard and safe-bunk calculator built for students.



\## Features



\- College portal attendance retrieval

\- Overall attendance calculation

\- Subject-wise attendance dashboard

\- Academic-calendar-based teaching-day calculation

\- Safe leave calculation based on 75% attendance

\- Sessional checkpoint calculations

\- User choice for whether a teaching-day checkpoint should be included

\- Simple web-based interface

\- Loading screen while attendance is being retrieved



\## How It Works



1\. The student enters their college portal credentials.

2\. Bunku-Bhaiya retrieves the current subject-wise attendance.

3\. The application calculates the overall attendance.

4\. The academic calendar determines which dates are actual teaching days.

5\. The student can choose whether a teaching-day checkpoint should be included.

6\. The calculator determines the maximum number of teaching days that can be missed while maintaining at least 75% attendance.

7\. The projected attendance is displayed on the dashboard.



\## Project Structure



```text

Bunku-Bhaiya/

│

├── app.py

├── portal.py

├── bunk\_calculator.py

├── academic\_calendar.py

├── test\_portal.py

├── .gitignore

│

├── static/

│   ├── style.css

│   └── loading.mp4

│

└── templates/

&#x20;   └── dashboard.html

## Configuration

BunkMaster uses a Flask session with a secret key provided through the
`SECRET_KEY` environment variable.

For local development, set the environment variable before running the app.

The secret key is intentionally not stored in the repository.

### Windows PowerShell

```powershell
[Environment]::SetEnvironmentVariable("SECRET_KEY","your-random-secret-here","User")