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

        page.get_by_label("AssemblyAI API Key:").fill("dummy-key") # Replace with a valid key for real testing
        page.get_by_label("OpenRouter API Key:").fill("dummy-key") # Replace with a valid key for real testing
        page.get_by_role("button", name="Save Settings").click()
        time.sleep(5)

        # Go to the input page
        input_button = page.get_by_role("radio", name="Input Content")
        expect(input_button).to_be_visible()
        input_button.click()
        time.sleep(5)

        # Select youtube url input
        youtube_url_button = page.get_by_role("radio", name="YouTube URL")
        expect(youtube_url_button).to_be_visible()
        youtube_url_button.click()
        time.sleep(5)

        # Enter youtube url and process
        page.get_by_label("Enter YouTube URL:").fill("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        page.get_by_role("button", name="Process YouTube Video").click()

        # Check for the transcription output
        expect(page.get_by_text("Transcription")).to_be_visible(timeout=120000)

        # Take a screenshot
        page.screenshot(path="jules-scratch/verification/verification.png")

        browser.close()

if __name__ == "__main__":
    run_verification()