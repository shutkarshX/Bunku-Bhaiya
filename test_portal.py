from playwright.sync_api import sync_playwright
from getpass import getpass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # Open college login page
    page.goto("https://nietcloud.niet.co.in/login.htm")

    username = input("College username: ")
    password = getpass("College password: ")

    # Login
    page.locator("#j_username").fill(username)
    page.locator("#password-1").fill(password)
    page.locator("button[type='submit']").click()

    page.wait_for_timeout(5000)

    print("Current URL:", page.url)

    if "/login.htm" in page.url:
        print("LOGIN FAILED")
        input("Press Enter to close...")
        browser.close()
        raise SystemExit

    print("Logged in successfully.")

    # Capture the full attendance response
    def handle_response(response):

        if "stu_getStudentBatchCourseAttendanceList.json" in response.url:

            print("\nSUBJECT-WISE ATTENDANCE FOUND")
            print("Status:", response.status)

            try:
                data = response.json()

                print("\n========== FULL ATTENDANCE RESPONSE ==========")
                print(data)
                print("==============================================")

            except Exception as e:
                print("Could not parse JSON:", e)

    page.on("response", handle_response)

    # Navigate manually for this test
    input(
        "\nClick Attendance in the college browser, "
        "wait for the attendance to appear, "
        "then press Enter here..."
    )

    page.wait_for_timeout(2000)

    browser.close()