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
        
        # Create context with realistic settings (Indian locale for BookMyShow)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            geolocation={"latitude": 19.0760, "longitude": 72.8777},  # Mumbai
            permissions=["geolocation"],
            extra_http_headers={
                "Accept-Language": "en-IN,en;q=0.9",
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
            print("Step 1: Navigate to BookMyShow homepage.")
            random_delay(500, 1000)
            page.goto("https://in.bookmyshow.com/", wait_until="domcontentloaded", timeout=60000)
            random_delay(2000, 3000)
            move_mouse_randomly(page)
            page.screenshot(path="bms_step1_homepage.png")
            print("Screenshot saved: bms_step1_homepage.png")
            
            print("Step 2: Handling city selection (Mumbai).")
            # Attempt to click 'Mumbai' city button/link
            try:
                # Look for a common city selection pattern (e.g., text, data-test-id)
                city_selectors = [
                    page.locator("text=Mumbai").first,
                    page.locator("div[data-test-id='city-modal-overlay'] button:has-text('Mumbai')").first,
                    page.locator("li[data-value='Mumbai']").first
                ]
                
                clicked_city = False
                for selector in city_selectors:
                    if selector.is_visible(timeout=5000):
                        selector.hover()
                        random_delay(300, 800)
                        selector.click()
                        print("City selected: Mumbai")
                        clicked_city = True
                        random_delay(3000, 4000) # Wait for page to settle after city selection
                        break
                
                if not clicked_city:
                    print("Mumbai city selection not found or already selected.")

            except Exception as e:
                print(f"City selection skipped or failed: {e}")
                
            page.screenshot(path="bms_step2_city_selected.png")
            print("Screenshot saved: bms_step2_city_selected.png")

            print("Step 3: Locate and click the search icon/button.")
            # BookMyShow usually has a magnifying glass icon for search
            search_icon_selectors = [
                "a[href='/explore/search/movies']", # Common search link
                "div[class*='search-button']", # Search button div
                "svg[data-icon='search']" # SVG search icon
            ]

            search_button = None
            for selector_str in search_icon_selectors:
                try:
                    loc = page.locator(selector_str).first
                    if loc.is_visible(timeout=5000):
                        search_button = loc
                        break
                except:
                    continue
            
            if search_button:
                search_button.hover()
                random_delay(300, 700)
                search_button.click()
                print("Clicked search icon.")
                random_delay(2000, 3000)
            else:
                print("Search icon not found. Proceeding without clicking.")
            
            page.screenshot(path="bms_step3_search_clicked.png")
            print("Screenshot saved: bms_step3_search_clicked.png")

            print("Step 4: Type 'Border 2' into the search input.")
            search_input = None
            # Try multiple selectors for the actual search input field
            search_input_selectors = [
                "input[placeholder*='Search']",
                "input#inp_Search",
                "input[type='text'][class*='search-input']"
            ]

            for selector in search_input_selectors:
                try:
                    loc = page.locator(selector).first
                    if loc.is_visible(timeout=5000):
                        search_input = loc
                        break
                except:
                    continue
            
            if search_input:
                search_input.hover()
                random_delay(200, 400)
                search_input.click()
                random_delay(300, 600)
                search_input.fill("")  # Clear first
                random_delay(200, 400)
                human_type(page, "Border 2")
                print("Typed 'Border 2' into search.")
                random_delay(3000, 4000)  # Wait for dropdown suggestions
            else:
                raise Exception("Search input field not found.")
            
            page.screenshot(path="bms_step4_typed_search.png")
            print("Screenshot saved: bms_step4_typed_search.png")

            print("Step 5: Select 'Border 2' from the search results/suggestions.")
            # Look for suggestions in a common structure
            # BookMyShow often uses a specific structure for search results like a list or div containing a-tags
            movie_result_selectors = [
                "a[href*='border-2']", # Direct link if available
                "div[class*='sc-g'] > div:has-text('Border 2')", # Common structure for movie results
                "li:has-text('Border 2')",
                "div[role='option']:has-text('Border 2')"
            ]
            
            movie_found = False
            for selector_str in movie_result_selectors:
                try:
                    movie_link = page.locator(selector_str).first
                    if movie_link.is_visible(timeout=5000):
                        movie_link.scroll_into_view_if_needed()
                        movie_link.hover(timeout=2000)
                        random_delay(300, 800)
                        movie_link.click(force=True)
                        print(f"Clicked search result for: {movie_link.inner_text()}")
                        movie_found = True
                        random_delay(4000, 6000) # Wait for movie page to load
                        break
                except Exception as e:
                    print(f"Trying next movie result selector: {e}")
                    continue
            
            if not movie_found:
                raise Exception("Movie 'Border 2' not found in search results.")
            
            page.screenshot(path="bms_step5_movie_page.png")
            print("Screenshot saved: bms_step5_movie_page.png")

            print("Step 6: Verify if showtimes are displayed for 'Border 2'.")
            # Check for elements indicating showtimes or ability to book tickets
            try:
                book_tickets_button = page.locator("text=Book Tickets").first
                show_date_picker = page.locator("div[data-entity-type='Date']").first
                
                if book_tickets_button.is_visible(timeout=10000):
                    print(" 'Book Tickets' button is visible. Shows are likely available.")
                elif show_date_picker.is_visible(timeout=10000):
                    print(" Date picker for shows is visible. Shows are likely available.")
                else:
                    print(" No immediate 'Book Tickets' or date picker visible. Shows might not be available or page structure changed.")
                
            except Exception as e:
                print(f"Could not verify showtime availability: {e}")
                print("This could mean no shows are currently available or selectors need adjustment.")

            page.screenshot(path="bms_step6_showtime_check.png")
            print("Screenshot saved: bms_step6_showtime_check.png")

            print("Automation completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="bms_error.png")
            print("Screenshot saved: bms_error.png")
        finally:
            random_delay(1000, 2000)
            browser.close()
            print("Browser closed.")

if __name__ == "__main__":
    main()