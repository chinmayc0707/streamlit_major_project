from playwright.sync_api import sync_playwright, expect
import time

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the app
        page.goto("http://localhost:8501")
        time.sleep(10) # Wait for the app to load

        # Go to settings and enter API keys
        settings_button = page.get_by_role("radio", name="Settings")
        expect(settings_button).to_be_visible()
        settings_button.click()
        time.sleep(5)

        page.get_by_label("AssemblyAI API Key:").fill("dummy-key")
        page.get_by_label("OpenRouter API Key:").fill("dummy-key")
        page.get_by_role("button", name="Save Settings").click()
        time.sleep(5)

        # Go to the input page
        input_button = page.get_by_role("radio", name="Input Content")
        expect(input_button).to_be_visible()
        input_button.click()
        time.sleep(5)

        # Select plain text input
        plain_text_button = page.get_by_role("radio", name="Plain Text")
        expect(plain_text_button).to_be_visible()
        plain_text_button.click()
        time.sleep(5)

        # Enter text and process
        page.get_by_label("Paste or type English text:").fill("This is a test of the translation feature.")
        page.get_by_role("button", name="Process Text Content").click()

        # Check for the Kanglish output
        expect(page.get_by_text("Kanglish Translation")).to_be_visible(timeout=60000)

        # Take a screenshot
        page.screenshot(path="jules-scratch/verification/verification.png")

        browser.close()

if __name__ == "__main__":
    run_verification()