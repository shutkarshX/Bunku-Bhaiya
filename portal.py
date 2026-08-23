from playwright.sync_api import sync_playwright
import time


def get_attendance(username, password):

    total_start = time.perf_counter()

    attendance_data = []

    with sync_playwright() as p:

        # ---------------------------------
        # 1. Launch browser
        # ---------------------------------

        t0 = time.perf_counter()

        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        t1 = time.perf_counter()

        print(f"[TIME] Browser launch: {t1 - t0:.2f}s")


        # ---------------------------------
        # 2. Open login page
        # ---------------------------------

        t0 = time.perf_counter()

        page.goto(
            "https://nietcloud.niet.co.in/login.htm",
            wait_until="domcontentloaded"
        )

        t1 = time.perf_counter()

        print(f"[TIME] Login page: {t1 - t0:.2f}s")


        # ---------------------------------
        # 3. Login
        # ---------------------------------

        t0 = time.perf_counter()

        page.locator("#j_username").fill(username)
        page.locator("#password-1").fill(password)

        page.locator("button[type='submit']").click()

        try:

            page.wait_for_url(
                "**/home.htm",
                timeout=15000
            )

        except Exception:

            print("Login failed.")
            print("Current URL:", page.url)

            browser.close()
            return []

        t1 = time.perf_counter()

        print(f"[TIME] Login: {t1 - t0:.2f}s")
        print("Logged in:", page.url)


        # ---------------------------------
        # 4. Attendance API listener
        # ---------------------------------

        def handle_response(response):

            if "stu_getStudentBatchCourseAttendanceList.json" in response.url:

                print("Subject-wise attendance request found.")

                try:

                    data = response.json()

                    if isinstance(data, list):

                        attendance_data.clear()
                        attendance_data.extend(data)

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


        page.on("response", handle_response)


        # ---------------------------------
        # 5. Academic Functions
        # ---------------------------------

        t0 = time.perf_counter()

        academic = page.locator(
            'a[pid="20009"]'
        )

        academic.wait_for(
            state="visible",
            timeout=10000
        )

        academic.click()

        t1 = time.perf_counter()

        print(
            f"[TIME] Academic Functions: {t1 - t0:.2f}s"
        )


        # ---------------------------------
        # 6. Courses
        # ---------------------------------

        t0 = time.perf_counter()

        courses = page.locator(
            'a[pid="24732"]'
        )

        courses.wait_for(
            state="visible",
            timeout=10000
        )

        courses.click()

        t1 = time.perf_counter()

        print(
            f"[TIME] Courses: {t1 - t0:.2f}s"
        )


        # ---------------------------------
        # 7. Attendance + API
        # ---------------------------------

        t0 = time.perf_counter()

        attendance_button = page.locator(
            'button[data-tab="attendanceTab"]'
        )

        attendance_button.wait_for(
            state="visible",
            timeout=10000
        )

        attendance_button.click()

        print("Attendance clicked.")

        # Wait for the API response to arrive
        deadline = time.perf_counter() + 10

        while (
            not attendance_data
            and time.perf_counter() < deadline
        ):
            page.wait_for_timeout(50)

        t1 = time.perf_counter()

        print(
            f"[TIME] Attendance + API: {t1 - t0:.2f}s"
        )

        print(
            "Subjects received:",
            len(attendance_data)
        )


        # ---------------------------------
        # 8. Total processing time
        # ---------------------------------

        total_end = time.perf_counter()

        print()
        print("======================================")
        print(
            f"[TIME] TOTAL: {total_end - total_start:.2f}s"
        )
        print("======================================")
        print()


        browser.close()


    return attendance_data