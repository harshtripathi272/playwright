import time
import random
from playwright.sync_api import sync_playwright

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
                '--window-size=1920,1080',
            ]
        )
        
        # Create context with realistic settings
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        
        page = context.new_page()
        
        try:
            # Step 1: Navigate to BookMyShow homepage
            print("Step 1: Navigating to BookMyShow...")
            random_delay(500, 1000)
            page.goto("https://in.bookmyshow.com", wait_until="domcontentloaded", timeout=60000)
            random_delay(2000, 3000)
            move_mouse_randomly(page)
            page.screenshot(path="step1_homepage.png")
            print("Screenshot saved: step1_homepage.png")

            # Step 2: Handle city selection popup and select Mumbai
            print("Step 2: Attempting to select Mumbai as the city...")
            try:
                # Look for the city selection modal
                # BookMyShow often has a modal with city names or asks 'Detect your location'
                # We will try to find a 'Mumbai' button directly in the main view or within a likely modal.
                mumbai_button = page.locator("div.sc-fHSTwm.fXwSjB[alt='Mumbai'], text=Mumbai").first
                if mumbai_button.is_visible(timeout=10000):
                    mumbai_button.hover()
                    random_delay(500, 1000)
                    mumbai_button.click()
                    print("City selected: Mumbai")
                    random_delay(3000, 5000) # Wait for page to load after city selection
                else:
                    print("Mumbai city selection button not found or not visible, proceeding assuming city is already set or no popup.")
            except Exception as e:
                print(f"City selection skipped or failed: {e}")
                # Optionally, if a 'detect location' button exists, click it and try to deny/select manually
                try:
                    if page.locator("text=Detect my location").is_visible(timeout=3000):
                        print("Found 'Detect my location', attempting to close or skip.")
                        page.keyboard.press("Escape") # Try to close with escape
                        random_delay(1000, 2000)
                except:
                    pass
            
            page.screenshot(path="step2_mumbai_selected.png")
            print("Screenshot saved: step2_mumbai_selected.png")

            # Step 3: Find search input and type 'Border 2'
            print("Step 3: Locating search input and typing 'Border 2'...")
            search_input = None
            search_selectors = [
                "input[placeholder*='Search']",
                "input[type='search']",
                "a[href='/explore/search/movie']", # BookMyShow often has a search icon/link first
                "div.sc-jKJlQu.hJpSjU" # A common search bar div on BMS
            ]
            
            for selector in search_selectors:
                try:
                    loc = page.locator(selector).first
                    if loc.is_visible(timeout=3000):
                        loc.hover()
                        random_delay(200, 500)
                        loc.click()
                        random_delay(1000, 2000) # Wait for search input to appear/become active
                        
                        # After clicking a search icon/link, a visible input field should appear
                        # Try finding a generic visible input after the initial click
                        temp_input = page.locator("input[type='text']:visible, input[type='search']:visible, input[placeholder*='Search']:visible").first
                        if temp_input.is_visible(timeout=3000):
                            search_input = temp_input
                            print(f"Found search input using selector: {selector}")
                            break
                except Exception as e:
                    # print(f"Selector '{selector}' failed: {e}")
                    continue

            if search_input:
                search_input.hover()
                random_delay(200, 400)
                search_input.click()
                random_delay(300, 600)
                search_input.fill("")  # Clear first
                random_delay(200, 400)

                human_type(page, "Border 2")
                random_delay(3000, 4000)  # Wait for dropdown suggestions
                page.screenshot(path="step3_typed_border2.png")
                print("Screenshot saved: step3_typed_border2.png")
            else:
                raise Exception("Could not find or activate search input field.")

            # Step 4: Click 'Border 2' from the search results dropdown
            print("Step 4: Selecting 'Border 2' from search results...")
            movie_found = False
            
            # Look for elements in the search dropdown. Common selectors: a, li, div[role='option'], div.sc-kghIBV.eybMGE
            dropdown_items = page.locator("div.sc-kghIBV.eybMGE > a, a.sc-qQyGU.iKkGvX, div[role='option'], li").all()
            
            for item in dropdown_items:
                try:
                    if not item.is_visible(timeout=1000):
                        continue
                    text = item.text_content().strip()
                    if "Border 2" in text or "border 2" in text.lower():
                        print(f"Found movie in dropdown: {text}")
                        item.scroll_into_view_if_needed()
                        item.hover(timeout=2000)
                        random_delay(500, 1000)
                        item.click(force=True) # Use force click as it might be covered by other elements momentarily
                        print(f"Clicked: {text}")
                        movie_found = True
                        break
                except Exception as e:
                    # print(f"Error interacting with dropdown item: {e}")
                    continue
            
            if not movie_found:
                raise Exception("Movie 'Border 2' not found in search results dropdown.")

            random_delay(3000, 5000) # Wait for navigation to movie page
            page.screenshot(path="step4_movie_page.png")
            print("Screenshot saved: step4_movie_page.png")
            
            # Step 5: Verify shows availability (by reaching the page and taking screenshot)
            print("Step 5: Successfully navigated to 'Border 2' movie page. Shows should be visible.")
            # You can add further checks here to scrape show times if needed
            # For this task, reaching the page where showtimes are displayed is sufficient.

            print("Automation completed successfully!")
            
        except Exception as e:
            print(f"Error during automation: {e}")
            page.screenshot(path="error.png")
            print("Screenshot saved: error.png")
        finally:
            random_delay(1000, 2000)
            browser.close()
            print("Browser closed.")

if __name__ == "__main__":
    main()
