import time
import random
from playwright.sync_api import sync_playwright
from playwright_stealth.stealth import Stealth  # CRITICAL: Anti-bot detection

def random_delay(min_ms=100, max_ms=500):
    """Add random delay to mimic human behavior."""
    time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

def human_type(page, text: str):
    """Type like a human with random delays and occasional typos."""
    for i, char in enumerate(text):
        # 5% chance to make a typo
        if random.random() < 0.05 and i < len(text) - 1:
            wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
            page.keyboard.type(wrong_char)
            random_delay(150, 400)
            page.keyboard.press("Backspace")
            random_delay(200, 500)
        
        page.keyboard.type(char)
        if char == " ":
            random_delay(150, 400)
        else:
            random_delay(40, 200)

def move_mouse_randomly(page):
    """Move mouse to random positions like a human."""
    for _ in range(3):
        x = random.randint(100, 800)
        y = random.randint(100, 500)
        page.mouse.move(x, y)
        random_delay(100, 300)

def main():
    with sync_playwright() as p:
        # Launch with anti-detection settings
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-infobars',
                '--disable-extensions',
                '--disable-gpu',
                '--window-size=1920,1080',
            ]
        )
        
        # Create context with realistic settings
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US", # Google is global, US is a good default
            timezone_id="America/New_York",
            geolocation={"latitude": 40.7128, "longitude": -74.0060},  # New York City
            permissions=["geolocation"],
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            }
        )
        
        page = context.new_page()
        
        # CRITICAL: Apply stealth mode to hide automation signatures
        stealth = Stealth()
        stealth.apply_stealth_sync(page)
        print("Stealth mode activated!")
        
        try:
            # Step 1: Navigate to Google.com
            print("Step 1: Navigating to google.com...")
            random_delay(500, 1000)
            page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=60000)
            random_delay(2000, 3000)
            move_mouse_randomly(page)
            page.screenshot(path="step1_google_homepage.png")
            print("Screenshot saved: step1_google_homepage.png")
            
            # Step 2: Find the search input field
            print("Step 2: Finding search input field...")
            search_input = None
            search_selectors = [
                "textarea[name='q']", # Google's primary search input
                "input[name='q']",
                "input[placeholder*='Search']",
                "input[type='search']",
                "input[type='text']",
            ]

            for selector in search_selectors:
                try:
                    loc = page.locator(selector).first
                    if loc.is_visible(timeout=2000):
                        search_input = loc
                        print(f"Found search input with selector: {selector}")
                        break
                except:
                    continue

            if not search_input:
                # Google usually has a textarea or input directly visible. This fallback is more generic.
                try:
                    # Attempt to click on a general search icon/text if present (less common on Google homepage)
                    page.locator("text=Search").first.click(timeout=2000)
                    random_delay(500, 1000)
                    search_input = page.locator("input:visible, textarea:visible").first
                    print("Found search input via fallback click.")
                except Exception as e:
                    print(f"Could not find search input even with fallback: {e}")
                    raise Exception("Failed to find search input field.")

            # Step 3: Type "weather" into the search field
            print("Step 3: Typing 'weather' into search field...")
            search_input.hover()
            random_delay(200, 400)
            search_input.click()
            random_delay(300, 600)
            
            # Google's search input often clears itself on click if it's pre-filled
            # For a fresh search, clearing explicitly might be redundant but safe.
            # search_input.fill("") 
            # random_delay(200, 400)
            
            human_type(page, "weather")
            random_delay(500, 1000) # Short delay before pressing Enter

            # Step 4: Submit the search query
            print("Step 4: Submitting search query by pressing Enter...")
            page.keyboard.press("Enter")
            
            # Step 5: Wait for search results to load, specifically for the weather card
            print("Step 5: Waiting for weather results to appear...")
            # Wait for either the temperature element or the main weather card container
            page.wait_for_selector("#wob_tm, div[aria-label='Weather']", timeout=15000)
            random_delay(3000, 5000) # Give it a bit more time after selector appears
            move_mouse_randomly(page)

            # Step 6: Take a screenshot of the weather results
            page.screenshot(path="step6_weather_results.png")
            print("Screenshot saved: step6_weather_results.png")
            
            print("Automation completed successfully: Searched for 'weather' on Google and found results.")
            
        except Exception as e:
            print(f"Error during automation: {e}")
            page.screenshot(path="error.png")
            print("Screenshot saved: error.1.png")
        finally:
            random_delay(1000, 2000)
            browser.close()
            print("Browser closed.")

if __name__ == "__main__":
    main()