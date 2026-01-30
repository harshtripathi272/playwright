"""
BookMyShow Stealth Script - Anti-Bot Detection Bypass

This script uses various techniques to bypass bot detection:
1. Playwright Stealth Plugin - Hides automation signatures
2. Advanced Human-like typing - Random delays, typos, and corrections
3. Mouse movements - Simulates real mouse behavior
4. Realistic browser fingerprint - Proper headers and user agent
5. Random delays - Mimics human reaction times
6. Smart Fuzzy Selection - Intelligent dropdown choice

Usage:
    python scripts/bookmyshow_stealth.py --movie "Border 2" --city "Mumbai"
"""

import argparse
import sys
import random
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
from playwright_stealth.stealth import Stealth
from rapidfuzz import fuzz
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Import matchers
from scripts.ai_matcher import setup_gemini, ai_find_element, fallback_fuzzy_match

console = Console()


def random_delay(min_ms=100, max_ms=500):
    """Add a random delay to mimic human behavior."""
    time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))


def human_type(page, text: str):
    """
    Type text like a human:
    - Random delays between keystrokes
    - Occasional typos and backspaces (5% chance)
    """
    chars = list(text)
    
    for i, char in enumerate(chars):
        # 5% chance to make a typo (if not the last character)
        if random.random() < 0.05 and i < len(chars) - 1:
            # Type a wrong character (neighbor on keyboard roughly)
            wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz') 
            page.keyboard.type(wrong_char)
            random_delay(150, 400)
            
            # Realize mistake, backspace
            page.keyboard.press("Backspace")
            random_delay(200, 500)
            
        page.keyboard.type(char)
        # Random delay between 50ms and 250ms per character
        # Faster for some sequences, slower for others
        if char == " ":
            random_delay(150, 400)
        else:
            random_delay(40, 200)


def move_mouse_randomly(page):
    """Move mouse to random positions to simulate human behavior."""
    for _ in range(3):
        x = random.randint(100, 800)
        y = random.randint(100, 500)
        page.mouse.move(x, y)
        random_delay(100, 300)


def find_best_dropdown_match(page, search_text: str):
    """Find the best matching option in the dropdown using fuzzy matching."""
    console.print(f"[cyan]Analyzing dropdown options for: '{search_text}'...[/cyan]")
    
    # Selectors for dropdown items - broadened to include all likely containers
    item_selectors = [
        "li",
        "a",
        "div[role='option']",
        ".search-result",
        "div[class*='suggestion']",
        "div[class*='styles__']" # Common in React apps like BMS
    ]
    
    potential_matches = []
    
    # Gather all text from potential dropdown items
    for selector in item_selectors:
        try:
            items = page.locator(selector).all()
            for item in items:
                if not item.is_visible():
                    continue
                    
                text = item.inner_text().strip()
                if not text:
                    continue
                
                # Clean text (remove newlines usually found in movie cards like "Border 2\nAction")
                clean_text = text.replace('\n', ' ').strip()
                
                # Calculate similarity score
                score = fuzz.token_sort_ratio(search_text.lower(), clean_text.lower())
                
                # Bonus for starting with the search term
                if clean_text.lower().startswith(search_text.lower()):
                    score += 10
                
                potential_matches.append({
                    "text": clean_text,
                    "score": score,
                    "element": item
                })
        except:
            continue

    if not potential_matches:
        console.print("[yellow]No dropdown items found to analyze.[/yellow]")
        return None

    # Sort by score descending
    potential_matches.sort(key=lambda x: x["score"], reverse=True)
    
    # Filter duplicates (by text)
    unique_matches = []
    seen_text = set()
    for m in potential_matches:
        if m["text"] not in seen_text:
            unique_matches.append(m)
            seen_text.add(m["text"])
            
    if not unique_matches:
         return None

    best_match = unique_matches[0]
    
    console.print("\n[dim]Top matches found:[/dim]")
    for match in unique_matches[:3]:
        console.print(f"  • \"{match['text'][:50]}...\" (Score: {match['score']})")
        
    if best_match["score"] > 50:  # Threshold for acceptance
        console.print(f"[green]✓ Best match selected: \"{best_match['text'][:50]}...\"[/green]")
        return best_match["element"]
    else:
        console.print(f"[yellow]⚠ Best match \"{best_match['text']}\" score too low ({best_match['score']})[/yellow]")
        return None


def extract_buttons_and_links(page):
    """Extract all buttons and clickable elements from the page."""
    elements = []
    
    selectors = ["button", "a", "[role='button']", ".btn", "[class*='book']", "[class*='ticket']"]
    
    for selector in selectors:
        try:
            locators = page.locator(selector).all()
            for loc in locators:
                try:
                    text = loc.inner_text(timeout=1000).strip()
                    if text and len(text) > 1 and len(text) < 50:
                        tag = loc.evaluate("el => el.tagName.toLowerCase()")
                        elements.append({
                            "text": text,
                            "tag": tag,
                            "selector": selector
                        })
                except:
                    continue
        except:
            continue
    
    # Remove duplicates
    seen = set()
    unique_elements = []
    for elem in elements:
        if elem["text"] not in seen:
            seen.add(elem["text"])
            unique_elements.append(elem)
    
    return unique_elements


def run_stealth_script(movie_name: str, city_name: str, find_text: str = None, api_key: str = None, headless: bool = False):
    """
    Run the stealth script with anti-detection techniques.
    """
    console.print(Panel.fit(
        f"[bold cyan]BookMyShow - STEALTH Mode[/bold cyan]\n"
        f"City: {city_name}\n"
        f"Movie: {movie_name}\n"
        f"Intent: {find_text or 'Just browsing'}\n\n"
        f"[dim]Anti-detection features enabled:[/dim]\n"
        f"  ✓ Playwright Stealth Plugin\n"
        f"  ✓ Human-like typing (with typos)\n"
        f"  ✓ Random mouse movements\n"
        f"  ✓ Realistic browser fingerprint\n"
        f"  ✓ Random delays\n"
        f"  ✓ Smart Fuzzy Selection\n"
        f"  ✓ AI/Fuzzy Element Matching",
        title="🕵️ Stealth Mode Activated"
    ))
    
    # Setup Gemini if API key provided
    use_ai = False
    if api_key:
        use_ai = setup_gemini(api_key)
        if use_ai:
             console.print("[green]🤖 AI Features Enabled (Gemini)[/green]")
    
    
    with sync_playwright() as p:
        # Launch browser with anti-detection settings
        browser = p.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',  # Hide automation
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
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            geolocation={"latitude": 19.0760, "longitude": 72.8777},  # Mumbai coordinates
            permissions=["geolocation"],
            extra_http_headers={
                "Accept-Language": "en-IN,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            }
        )
        
        page = context.new_page()
        
        # Apply stealth mode - this hides automation signatures
        console.print("\n[cyan]Applying stealth patches...[/cyan]")
        stealth_config = Stealth()
        stealth_config.apply_stealth_sync(page)
        console.print("[green]✓ Stealth mode activated[/green]")
        
        try:
            # Step 1: Go to BookMyShow with human-like behavior
            console.print(f"\n[yellow]Step 1:[/yellow] Opening BookMyShow...")
            random_delay(500, 1000)  # Wait before navigating
            
            page.goto("https://in.bookmyshow.com", wait_until="domcontentloaded", timeout=60000)
            random_delay(2000, 3000)  # Wait like a human would
            
            # Move mouse around like a human
            move_mouse_randomly(page)
            console.print("[green]✓ BookMyShow loaded[/green]")
            
            # Step 2: Select city
            console.print(f"\n[yellow]Step 2:[/yellow] Selecting city: {city_name}...")
            random_delay(500, 1000)
            
            try:
                city_button = page.locator(f"text={city_name}").first
                if city_button.is_visible(timeout=5000):
                    # Move to element before clicking (human-like)
                    city_button.hover()
                    random_delay(200, 500)
                    city_button.click()
                    console.print(f"[green]✓ Selected city: {city_name}[/green]")
                    random_delay(2000, 3000)
            except Exception as e:
                console.print(f"[yellow]⚠ City selection: {e}[/yellow]")
            
            # Step 3: Search for movie
            console.print(f"\n[yellow]Step 3:[/yellow] Searching for '{movie_name}'...")
            random_delay(1000, 2000)
            
            # Move mouse before clicking search
            move_mouse_randomly(page)
            
            # Try to find search input
            search_selectors = [
                "input[placeholder*='Search']",
                "input[type='search']",
                "input[type='text']",
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    loc = page.locator(selector).first
                    if loc.is_visible(timeout=2000):
                        search_input = loc
                        break
                except:
                    continue
            
            if not search_input:
                # Try clicking on search area first
                try:
                    page.locator("text=Search for Movies").first.click()
                    random_delay(500, 1000)
                    search_input = page.locator("input:visible").first
                except:
                    console.print("[red]Could not find search input[/red]")
            
            if search_input:
                # Click on search input
                search_input.hover()
                random_delay(200, 400)
                search_input.click()
                random_delay(300, 600)
                
                # Clear any existing text
                search_input.fill("")
                random_delay(200, 400)
                
                # Type movie name like a human
                console.print("[cyan]Typing movie name (simulating human typing with typos)...[/cyan]")
                human_type(page, movie_name)
                console.print("[green]✓ Typed movie name[/green]")
                
                # Wait for dropdown to appear
                console.print("[cyan]Waiting for search suggestions...[/cyan]")
                random_delay(3000, 4000)
                
                # Take screenshot
                page.screenshot(path="stealth_search.png")
                console.print("[dim]Screenshot saved: stealth_search.png[/dim]")
                
                # Use fuzzy matching to find and click result
                best_element = find_best_dropdown_match(page, movie_name)
                
                if best_element:
                    try:
                        # Try to scroll into view specifically
                        best_element.scroll_into_view_if_needed()
                        # specific timeout for hover so we don't get stuck
                        best_element.hover(timeout=2000)
                    except Exception as e:
                        console.print(f"[yellow]⚠ Hover failed (element might be covered), trying force click...[/yellow]")
                    
                    random_delay(300, 800)
                    try:
                        # Force click to ensure it registers
                        best_element.click(force=True)
                        console.print(f"[green]✓ Clicked best match[/green]")
                        random_delay(5000, 6000) # Increased wait for page load
                    except Exception as e:
                        console.print(f"[yellow]⚠ Click failed ({e}), attempting direct navigation...[/yellow]")
                        href = best_element.get_attribute("href")
                        if href:
                            target_url = href if href.startswith("http") else "https://in.bookmyshow.com" + href
                            page.goto(target_url, wait_until="domcontentloaded")
                            console.print(f"[green]✓ Navigated directly to {target_url}[/green]")
                            random_delay(3000, 4000)
                        else:
                            console.print("[red]❌ Could not navigate: No href found on element[/red]")
                else:
                    # Fallback if no fuzzy match found
                    console.print("[yellow]Fuzzy match failed, pressing Enter...[/yellow]")
                    random_delay(500, 800)
                    page.keyboard.press("Enter")
                    random_delay(4000, 5000)
            
            # Step 4: Extract elements
            console.print(f"\n[yellow]Step 4:[/yellow] Extracting page elements...")
            elements = extract_buttons_and_links(page)
            console.print(f"[green]✓ Found {len(elements)} elements[/green]")
            
            # Take final screenshot
            page.screenshot(path="stealth_result.png")
            console.print("[dim]Screenshot saved: stealth_result.png[/dim]")
            
            # Step 5: Analyze and Click (if requested)
            if find_text:
                console.print(f"\n[yellow]Step 5:[/yellow] Analyzing intent: '{find_text}'...")
                
                match_result = {}
                if use_ai:
                    console.print("[cyan]Asking Gemini AI to find the best element...[/cyan]")
                    match_result = ai_find_element(find_text, elements)
                else:
                    console.print("[cyan]Using Fuzzy Matching to find element...[/cyan]")
                    match_result = fallback_fuzzy_match(find_text, elements)
                
                if match_result.get("matched_index", -1) >= 0:
                    best_elem = match_result.get("element")
                    console.print(Panel.fit(
                        f"[bold green]✅ Target Identified![/bold green]\n\n"
                        f"[yellow]Your Intent:[/yellow] \"{find_text}\"\n"
                        f"[green]Matched Element:[/green] \"{best_elem.get('text')}\"\n"
                        f"[cyan]Confidence:[/cyan] {match_result.get('confidence')}%\n"
                        f"[magenta]Reasoning:[/magenta] {match_result.get('reasoning')}",
                        title="🎯 Smart Match"
                    ))
                    
                    # Try to interact with the found element
                    selector = best_elem.get("selector")
                    # We need to find the specific element handle again or use the selector
                    # However, best_elem from fallback_fuzzy_match might not have the playwright locator handle attached
                    # But extract_buttons_and_links returns dictionaries, not handles.
                    # We need to re-locate it.
                    
                    target_locator = None
                    if selector:
                        # Try to find it by text and selector to be precise
                        text_content = best_elem.get("text")
                        try:
                            # Try precise match first
                            target_locator = page.locator(f"{selector}:has-text('{text_content}')").first
                            if not target_locator.is_visible():
                                 target_locator = page.locator(selector).filter(has_text=text_content).first
                        except:
                            target_locator = page.locator(selector).first
                    
                    if target_locator:
                        console.print(f"\n[yellow]Step 6:[/yellow] interacting with target...")
                        target_locator.scroll_into_view_if_needed()
                        random_delay(500, 1000)
                        
                        try:
                            target_locator.hover(timeout=2000)
                            random_delay(200, 500)
                            target_locator.click(force=True)
                            console.print(f"[green]✓ Clicked on '{best_elem.get('text')}'[/green]")
                        except Exception as e:
                             console.print(f"[yellow]⚠ Click failed ({e}), trying to navigate via href...[/yellow]")
                             # Reuse the failsafe logic
                             try:
                                 href = target_locator.get_attribute("href")
                                 if href:
                                     target_url = href if href.startswith("http") else "https://in.bookmyshow.com" + href
                                     page.goto(target_url, wait_until="domcontentloaded")
                                     console.print(f"[green]✓ Navigated directly to {target_url}[/green]")
                                 else:
                                     console.print("[red]❌ No href found for fallback navigation[/red]")
                             except:
                                 console.print("[red]❌ Failed to retrieve href[/red]")
                        
                        random_delay(5000, 6000)
                    else:
                        console.print("[red]❌ Could not re-locate the element on page[/red]")

            return elements
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            page.screenshot(path="stealth_error.png")
            return []
        finally:
            random_delay(1000, 2000)  # Wait before closing like a human
            browser.close()
            console.print("\n[dim]Browser closed.[/dim]")


def main():
    parser = argparse.ArgumentParser(description="BookMyShow Stealth Script with Anti-Detection")
    parser.add_argument("--movie", type=str, default="Border 2", help="Movie name to search")
    parser.add_argument("--city", type=str, default="Mumbai", help="City to select")
    parser.add_argument("--find", type=str, help="Intent/Element to find (e.g., 'book tickets')")
    parser.add_argument("--api-key", type=str, help="Gemini API Key for AI matching")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    args = parser.parse_args()
    run_stealth_script(args.movie, args.city, args.find, args.api_key, args.headless)


if __name__ == "__main__":
    main()
