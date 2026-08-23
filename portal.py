from playwright.sync_api import sync_playwright
import time


# =========================================
# PORTAL ERRORS
# =========================================

class PortalUnavailableError(Exception):
    """The NIET portal could not be reached or loaded."""
    pass


class PortalLoginError(Exception):
    """The NIET portal was reachable but login failed."""
    pass


# =========================================
# GET ATTENDANCE
# =========================================

def get_attendance(username, password):

    total_start = time.perf_counter()

    attendance_data = []
    browser = None

    try:

        with sync_playwright() as p:

            # ---------------------------------
            # 1. Launch browser
            # ---------------------------------

            t0 = time.perf_counter()

            try:

                browser = p.chromium.launch(
                    headless=False
                )

                page = browser.new_page()

            except Exception as e:

                print("Could not launch browser:")
                print(e)

                raise PortalUnavailableError(
                    "Unable to start the browser."
                )


            t1 = time.perf_counter()

            print(
                f"[TIME] Browser launch: "
                f"{t1 - t0:.2f}s"
            )


            # ---------------------------------
            # 2. Open login page
            # ---------------------------------

            t0 = time.perf_counter()

            try:

                page.goto(
                    "https://nietcloud.niet.co.in/login.htm",
                    wait_until="domcontentloaded",
                    timeout=15000
                )

            except Exception as e:

                print()
                print("======================================")
                print("NIET PORTAL UNAVAILABLE")
                print("======================================")
                print(
                    "Could not reach the college portal."
                )
                print(e)
                print()

                raise PortalUnavailableError(
                    "The NIET college portal is currently "
                    "unreachable."
                )


            t1 = time.perf_counter()

            print(
                f"[TIME] Login page: "
                f"{t1 - t0:.2f}s"
            )


            # ---------------------------------
            # 3. Login
            # ---------------------------------

            t0 = time.perf_counter()

            try:

                page.locator(
                    "#j_username"
                ).fill(username)

                page.locator(
                    "#password-1"
                ).fill(password)

                page.locator(
                    "button[type='submit']"
                ).click()

            except Exception as e:

                print("Could not submit login:")
                print(e)

                raise PortalUnavailableError(
                    "The NIET login page could not "
                    "be used."
                )


            try:

                page.wait_for_url(
                    "**/home.htm",
                    timeout=15000
                )

            except Exception:

                print()
                print("======================================")
                print("NIET LOGIN FAILED")
                print("======================================")

                print(
                    "Current URL:",
                    page.url
                )

                print()

                # ---------------------------------
                # If the portal itself disappeared
                # after login attempt, treat it as
                # unavailable.
                # ---------------------------------

                if (
                    "nietcloud.niet.co.in"
                    not in page.url
                ):

                    raise PortalUnavailableError(
                        "The NIET portal became "
                        "unreachable."
                    )

                raise PortalLoginError(
                    "The NIET portal was reached, "
                    "but login was not successful."
                )


            t1 = time.perf_counter()

            print(
                f"[TIME] Login: "
                f"{t1 - t0:.2f}s"
            )

            print(
                "Logged in:",
                page.url
            )


            # ---------------------------------
            # 4. Attendance API listener
            # ---------------------------------

            def handle_response(response):

                if (
                    "stu_getStudentBatchCourseAttendanceList.json"
                    in response.url
                ):

                    print(
                        "Subject-wise attendance "
                        "request found."
                    )

                    try:

                        data = response.json()

                        if isinstance(data, list):

                            attendance_data.clear()

                            attendance_data.extend(
                                data
                            )

                        print(
                            "Captured",
                            len(attendance_data),
                            "subjects"
                        )

                    except Exception as e:

                        print(
                            "Could not read attendance:",
                            e
                        )


            page.on(
                "response",
                handle_response
            )


            # ---------------------------------
            # 5. Academic Functions
            # ---------------------------------

            t0 = time.perf_counter()

            try:

                academic = page.locator(
                    'a[pid="20009"]'
                )

                academic.wait_for(
                    state="visible",
                    timeout=10000
                )

                academic.click()

            except Exception as e:

                print(
                    "Academic Functions page "
                    "could not be opened:"
                )

                print(e)

                raise PortalUnavailableError(
                    "The NIET portal did not respond "
                    "correctly after login."
                )


            t1 = time.perf_counter()

            print(
                f"[TIME] Academic Functions: "
                f"{t1 - t0:.2f}s"
            )


            # ---------------------------------
            # 6. Courses
            # ---------------------------------

            t0 = time.perf_counter()

            try:

                courses = page.locator(
                    'a[pid="24732"]'
                )

                courses.wait_for(
                    state="visible",
                    timeout=10000
                )

                courses.click()

            except Exception as e:

                print(
                    "Courses page "
                    "could not be opened:"
                )

                print(e)

                raise PortalUnavailableError(
                    "The NIET portal did not respond "
                    "correctly while opening courses."
                )


            t1 = time.perf_counter()

            print(
                f"[TIME] Courses: "
                f"{t1 - t0:.2f}s"
            )


            # ---------------------------------
            # 7. Attendance + API
            # ---------------------------------

            t0 = time.perf_counter()

            try:

                attendance_button = page.locator(
                    'button[data-tab="attendanceTab"]'
                )

                attendance_button.wait_for(
                    state="visible",
                    timeout=10000
                )

                attendance_button.click()

                print(
                    "Attendance clicked."
                )

            except Exception as e:

                print(
                    "Attendance section "
                    "could not be opened:"
                )

                print(e)

                raise PortalUnavailableError(
                    "The NIET attendance page "
                    "could not be opened."
                )


            # ---------------------------------
            # Wait for attendance API
            # ---------------------------------

            deadline = (
                time.perf_counter() + 10
            )

            while (
                not attendance_data
                and time.perf_counter() < deadline
            ):

                page.wait_for_timeout(50)


            t1 = time.perf_counter()

            print(
                f"[TIME] Attendance + API: "
                f"{t1 - t0:.2f}s"
            )

            print(
                "Subjects received:",
                len(attendance_data)
            )


            # ---------------------------------
            # Attendance request succeeded but
            # returned no subjects.
            # ---------------------------------

            if not attendance_data:

                raise PortalUnavailableError(
                    "The attendance data could not "
                    "be retrieved from the NIET portal."
                )


            # ---------------------------------
            # Total processing time
            # ---------------------------------

            total_end = time.perf_counter()

            print()
            print(
                "======================================"
            )

            print(
                f"[TIME] TOTAL: "
                f"{total_end - total_start:.2f}s"
            )

            print(
                "======================================"
            )

            print()


            return attendance_data


    except (
        PortalUnavailableError,
        PortalLoginError
    ):

        raise


    except Exception as e:

        print()
        print(
            "======================================"
        )
        print(
            "UNEXPECTED PORTAL ERROR"
        )
        print(
            "======================================"
        )
        print(e)
        print()

        raise PortalUnavailableError(
            "The NIET portal is currently unavailable."
        )


    finally:

        # -------------------------------------
        # Always close browser
        # -------------------------------------

        if browser:

            try:

                browser.close()

            except Exception:

                pass