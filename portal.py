from datetime import date, datetime
import time
import uuid

from playwright.sync_api import sync_playwright

from academic_calendar import is_teaching_day


class PortalUnavailableError(Exception):
    """The NIET portal could not be reached or loaded."""
    pass


class PortalLoginError(Exception):
    """The NIET portal was reachable but login failed."""
    pass


# Raw subject-wise attendance responses are kept server-side so the Flask
# cookie session does not have to carry hundreds of attendance records.
_SUBJECT_DETAILS_CACHE = {}


def get_subject_details(details_token):
    """Return cached raw subject-wise attendance details for a token."""
    if not details_token:
        return []
    return _SUBJECT_DETAILS_CACHE.get(details_token, [])


def _parse_portal_date(value):
    """Convert the portal's attendance date string into a date."""
    if not value:
        return None

    value = str(value).strip()

    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass

    return None


def _today_logged_classes(page, course_data):
    """Count today's classes while retaining the exact portal responses."""
    subject_ids = []

    for course in course_data:
        encrypted_id = course.get("encoSubjectwiseStudentId")
        if encrypted_id and encrypted_id not in subject_ids:
            subject_ids.append(encrypted_id)

    if not subject_ids:
        raise PortalUnavailableError(
            "The course data did not contain subject attendance IDs."
        )

    today = date.today()
    today_logged = 0
    subject_details = []

    print(
        "Checking today's logged classes across",
        len(subject_ids),
        "subjects..."
    )

    for index, encrypted_id in enumerate(subject_ids, start=1):
        try:
            response = page.request.get(
                "https://nietcloud.niet.co.in/"
                "stu_getSubjectWiseStudentAttendance.json",
                params={"encoSubjectwiseStudentId": encrypted_id},
                timeout=15000,
            )

            # Playwright APIResponse exposes ok/status rather than
            # requests.Response.raise_for_status().
            if not response.ok:
                raise RuntimeError(
                    f"HTTP {response.status} while retrieving subject attendance"
                )

            records = response.json()

            if not isinstance(records, list):
                raise ValueError("Subject attendance response was not a list")

            # Keep the response exactly as returned by the portal. Only the
            # subject label is added outside the raw records for display.
            subject_name = f"Subject {index}"
            for course in course_data:
                if course.get("encoSubjectwiseStudentId") == encrypted_id:
                    subject_name = (
                        course.get("subjectName")
                        or course.get("courseName")
                        or course.get("subjectCode")
                        or subject_name
                    )
                    break

            columns = []
            for record in records:
                if isinstance(record, dict):
                    for key in record.keys():
                        if key not in columns:
                            columns.append(key)

            subject_details.append({
                "subject_name": subject_name,
                "subject_id": encrypted_id,
                "records": records,
                "columns": columns,
            })

            subject_today = 0

            for record in records:
                if not isinstance(record, dict):
                    continue

                if _parse_portal_date(record.get("Date")) != today:
                    continue

                # A record normally represents one lecture. If the portal
                # reports consecutive lectures, count all of them.
                try:
                    count = int(
                        record.get("noOfConsicativeLectur") or 1
                    )
                except (TypeError, ValueError):
                    count = 1

                subject_today += max(1, count)

            today_logged += subject_today
            print(
                f"  Subject {index}/{len(subject_ids)}: "
                f"{subject_today} logged today"
            )

        except Exception as e:
            print(
                f"Could not retrieve today's sessions for subject "
                f"{index}: {e}"
            )
            # Accuracy matters here: do not silently return a partial count.
            raise PortalUnavailableError(
                "The portal did not return today's class data for all subjects."
            )

    # Today only contributes classes if the academic calendar says it is a
    # teaching day. Off days must never be treated as eight remaining classes.
    if is_teaching_day(today.isoformat()):
        remaining_today = max(0, 8 - today_logged)
    else:
        remaining_today = 0
        print("Today is not a teaching day; remaining classes: 0")

    return today_logged, remaining_today, subject_details


def get_attendance(username, password):
    total_start = time.perf_counter()
    attendance_data = []
    course_data = []

    with sync_playwright() as p:
        browser = None
        page = None

        try:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as e:
                print("Could not launch Chromium:", e)
                raise PortalUnavailableError("Unable to start the browser.")

            try:
                page = browser.new_page()
            except Exception as e:
                print("Could not create browser page:", e)
                raise PortalUnavailableError("Unable to create a browser session.")

            # Open login page.
            try:
                page.goto(
                    "https://nietcloud.niet.co.in/login.htm",
                    wait_until="domcontentloaded",
                    timeout=15000,
                )
            except Exception as e:
                print("Could not reach the college portal:", e)
                raise PortalUnavailableError(
                    "The NIET college portal is currently unreachable."
                )

            # Login.
            try:
                page.locator("#j_username").fill(username)
                page.locator("#password-1").fill(password)
                page.locator("button[type='submit']").click()
            except Exception as e:
                print("Could not submit login:", e)
                raise PortalUnavailableError("The NIET login page could not be used.")

            try:
                page.wait_for_url("**/home.htm", timeout=15000)
            except Exception:
                print("NIET login failed. Current URL:", page.url)
                if "nietcloud.niet.co.in" not in page.url:
                    raise PortalUnavailableError(
                        "The NIET portal became unreachable."
                    )
                raise PortalLoginError(
                    "The NIET portal was reached, but login was not successful."
                )

            # Capture both existing aggregate attendance and the course list.
            def handle_response(response):
                try:
                    if "stu_getStudentBatchCourseAttendanceList.json" in response.url:
                        data = response.json()
                        if isinstance(data, list):
                            attendance_data.clear()
                            attendance_data.extend(data)
                            print("Captured", len(attendance_data), "subjects")

                    elif "stu_getStudentBatchCourseList.json" in response.url:
                        data = response.json()
                        if isinstance(data, list):
                            course_data.clear()
                            course_data.extend(data)
                            print("Captured", len(course_data), "course records")
                except Exception as e:
                    print("Could not read portal response:", e)

            page.on("response", handle_response)

            # Open Academic Functions.
            try:
                academic = page.locator('a[pid="20009"]')
                academic.wait_for(state="visible", timeout=10000)
                academic.click()
            except Exception as e:
                print("Academic Functions could not be opened:", e)
                raise PortalUnavailableError(
                    "The NIET portal did not respond correctly after login."
                )

            # Open Courses. This also triggers the course-list request.
            try:
                courses = page.locator('a[pid="24732"]')
                courses.wait_for(state="visible", timeout=10000)
                courses.click()
            except Exception as e:
                print("Courses could not be opened:", e)
                raise PortalUnavailableError(
                    "The NIET portal did not respond correctly while opening courses."
                )

            # Open Attendance. This triggers the aggregate attendance request.
            try:
                attendance_button = page.locator(
                    'button[data-tab="attendanceTab"]'
                )
                attendance_button.wait_for(state="visible", timeout=10000)
                attendance_button.click()
            except Exception as e:
                print("Attendance section could not be opened:", e)
                raise PortalUnavailableError(
                    "The NIET attendance page could not be opened."
                )

            # Wait for both existing API responses.
            deadline = time.perf_counter() + 10
            while (
                (not attendance_data or not course_data)
                and time.perf_counter() < deadline
            ):
                page.wait_for_timeout(50)

            if not attendance_data:
                raise PortalUnavailableError(
                    "The attendance data could not be retrieved from the NIET portal."
                )

            if not course_data:
                raise PortalUnavailableError(
                    "The course data could not be retrieved from the NIET portal."
                )

            # Use the authenticated portal session to inspect every subject.
            # These are the same 13 calls already needed for today's count;
            # their raw responses are retained for the dashboard details.
            (
                today_logged,
                remaining_today,
                subject_details,
            ) = _today_logged_classes(
                page,
                course_data
            )

            # Keep the raw subject-wise responses server-side. The token is
            # small enough to safely carry in the Flask cookie session.
            details_token = uuid.uuid4().hex
            _SUBJECT_DETAILS_CACHE[details_token] = subject_details

            # Problem 2 is already available from the aggregate endpoint.
            # Keep it informational; these classes have occurred and must NOT
            # be added to future_classes.
            unmarked_classes = 0
            for subject in attendance_data:
                try:
                    unmarked_classes += int(
                        subject.get("totalUnFreezedAttendance") or 0
                    )
                except (TypeError, ValueError):
                    pass

            # Preserve the new values inside the existing subject-list shape.
            # This keeps app.py backwards compatible while allowing the
            # calculator/session to carry today's state across requests.
            attendance_data[0][
                "_bunkmaster_today_logged"
            ] = today_logged

            attendance_data[0][
                "_bunkmaster_remaining_today"
            ] = remaining_today

            attendance_data[0][
                "_bunkmaster_unmarked_classes"
            ] = unmarked_classes

            attendance_data[0][
                "_bunkmaster_subject_details_token"
            ] = details_token

            print("Today's logged classes:", today_logged)
            print("Today's remaining classes:", remaining_today)
            print("Unmarked classes:", unmarked_classes)
            print(
                f"[TIME] TOTAL: {time.perf_counter() - total_start:.2f}s"
            )

            return attendance_data

        except (PortalUnavailableError, PortalLoginError):
            raise
        except Exception as e:
            print("Unexpected portal error:", e)
            raise PortalUnavailableError(
                "The NIET portal is currently unavailable."
            )
        finally:
            if browser is not None:
                try:
                    browser.close()
                except Exception as e:
                    print("Browser cleanup warning:", e)
                except Exception:
                    pass
