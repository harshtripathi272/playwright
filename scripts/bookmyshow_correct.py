"""
Script 1: BookMyShow Correct Script

This is the CORRECT script that:
1. Goes to BookMyShow
2. Selects a city (e.g., Mumbai)
3. Searches for a movie (e.g., "Border 2")
4. Selects the movie from dropdown
5. Opens the movie page
6. Extracts all elements including "Book Tickets" button

Usage:
    python scripts/bookmyshow_correct.py --movie "Border 2" --city "Mumbai"
    python scripts/bookmyshow_correct.py --movie "Pushpa 2" --city "Delhi"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def extract_buttons_and_links(page):
    """Extract all buttons and clickable elements from the page."""
    elements = []
    
    selectors = ["button", "a", "[role='button']", ".btn", "[class*='book']", "[class*='ticket']", "div[class*='styles']"]
    
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


def select_city(page, city_name: str) -> bool:
    """Select a city on BookMyShow."""
    console.print(f"[cyan]Looking for city: {city_name}[/cyan]")
    
    try:
        page.wait_for_timeout(2000)
        
        # Try clicking on popular city buttons directly
        city_button = page.locator(f"text={city_name}").first
        if city_button.is_visible(timeout=3000):
            city_button.click()
            console.print(f"[green]✓ Selected city: {city_name}[/green]")
            page.wait_for_timeout(2000)
            return True
        
        page.locator(f"a:has-text('{city_name}')").first.click(timeout=3000)
        console.print(f"[green]✓ Selected city: {city_name}[/green]")
        return True
        
    except Exception as e:
        console.print(f"[yellow]⚠ Could not find city popup ({e})[/yellow]")
        return False


def search_and_select_movie(page, movie_name: str) -> bool:
    """Search for a movie and select it from the dropdown - with proper JS event triggering."""
    console.print(f"[cyan]Searching for: {movie_name}[/cyan]")
    
    try:
        # First, click on the search icon/area to open search
        search_clicked = False
        
        # Try clicking the search icon first
        search_icon_selectors = [
            "[class*='search']",
            "svg[class*='search']",
            "div[class*='Search']",
            "text=Search for Movies",
            "text=Search",
        ]
        
        for selector in search_icon_selectors:
            try:
                icon = page.locator(selector).first
                if icon.is_visible(timeout=2000):
                    icon.click()
                    page.wait_for_timeout(1000)
                    search_clicked = True
                    console.print("[green]✓ Clicked on search area[/green]")
                    break
            except:
                continue
        
        # Now find the search input
        search_input = None
        input_selectors = [
            "input[placeholder*='Search']",
            "input[type='search']",
            "input[type='text']",
            "input:visible",
        ]
        
        for selector in input_selectors:
            try:
                loc = page.locator(selector).first
                if loc.is_visible(timeout=2000):
                    search_input = loc
                    console.print(f"[cyan]Found search input[/cyan]")
                    break
            except:
                continue
        
        if not search_input:
            console.print("[red]Could not find search input[/red]")
            return False
        
        # Click on the input to focus it
        search_input.click()
        page.wait_for_timeout(500)
        
        # Clear any existing text
        search_input.fill("")
        page.wait_for_timeout(300)
        
        # KEY FIX: Use page.keyboard to type character by character
        # This triggers the proper JavaScript events for the autocomplete dropdown
        console.print("[cyan]Typing movie name (triggering dropdown)...[/cyan]")
        
        for char in movie_name:
            page.keyboard.type(char)
            page.wait_for_timeout(150)  # Small delay between characters
        
        console.print("[green]✓ Typed movie name[/green]")
        
        # Wait for dropdown to appear
        page.wait_for_timeout(3000)
        
        # Try to find and click the movie in the dropdown
        console.print("[cyan]Looking for movie in dropdown...[/cyan]")
        
        # Take a screenshot to see what's on screen
        page.screenshot(path="search_dropdown.png")
        console.print("[dim]Screenshot saved: search_dropdown.png[/dim]")
        
        # Try multiple selectors to find the movie in suggestions
        dropdown_selectors = [
            f"[class*='search'] a:has-text('{movie_name}')",  # Link in search results
            f"[class*='suggest'] >> text={movie_name}",       # Suggestion dropdown
            f"[class*='result'] >> text={movie_name}",        # Results
            f"[class*='movie'] >> text={movie_name}",         # Movie container
            f"li >> text={movie_name}",                       # List item
            f"div >> text={movie_name}",                      # Any div
            f"a >> text={movie_name}",                        # Any link
        ]
        
        for selector in dropdown_selectors:
            try:
                movie_option = page.locator(selector).first
                if movie_option.is_visible(timeout=2000):
                    console.print(f"[green]Found movie with selector: {selector}[/green]")
                    movie_option.click()
                    console.print(f"[green]✓ Selected '{movie_name}' from dropdown[/green]")
                    page.wait_for_timeout(3000)
                    return True
            except:
                continue
        
        # If dropdown didn't work, try pressing Enter and looking in results
        console.print("[yellow]Dropdown not found, pressing Enter to search...[/yellow]")
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)
        
        # Try to click on the movie in the search results page
        try:
            # Look for movie cards/posters
            movie_card = page.locator(f"a:has-text('{movie_name}')").first
            if movie_card.is_visible(timeout=5000):
                movie_card.click()
                console.print(f"[green]✓ Clicked on '{movie_name}' in results[/green]")
                page.wait_for_timeout(3000)
                return True
        except:
            pass
        
        console.print("[yellow]Could not find movie in results[/yellow]")
        return False
        
    except Exception as e:
        console.print(f"[red]Search error: {e}[/red]")
        return False


def run_bookmyshow_correct(movie_name: str, city_name: str, headless: bool = False):
    """
    Run the correct script that fetches actual element texts from BookMyShow.
    """
    console.print(Panel.fit(
        f"[bold green]BookMyShow - CORRECT Script[/bold green]\n"
        f"City: {city_name}\n"
        f"Movie: {movie_name}\n"
        f"This script extracts the ACTUAL button texts",
        title="✅ Script 1: Correct Version"
    ))
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # Step 1: Go to BookMyShow
            console.print(f"\n[yellow]Step 1:[/yellow] Opening BookMyShow...")
            page.goto("https://in.bookmyshow.com", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            console.print("[green]✓ BookMyShow loaded[/green]")
            
            # Step 2: Select city
            console.print(f"\n[yellow]Step 2:[/yellow] Selecting city: {city_name}...")
            select_city(page, city_name)
            page.wait_for_timeout(2000)
            
            # Step 3: Search and select movie
            console.print(f"\n[yellow]Step 3:[/yellow] Searching for '{movie_name}'...")
            movie_found = search_and_select_movie(page, movie_name)
            
            if movie_found:
                console.print(f"[green]✓ Movie page opened[/green]")
            else:
                console.print(f"[yellow]⚠ Could not open movie page, showing current elements[/yellow]")
            
            # Step 4: Extract all elements
            console.print(f"\n[yellow]Step 4:[/yellow] Extracting page elements...")
            page.wait_for_timeout(2000)
            elements = extract_buttons_and_links(page)
            console.print(f"[green]✓ Found {len(elements)} elements[/green]")
            
            # Step 5: Display results
            console.print(f"\n[yellow]Step 5:[/yellow] Here are the CORRECT element texts:\n")
            
            table = Table(title="Available Page Elements (Correct Texts)", show_header=True)
            table.add_column("Text", style="green", width=40)
            table.add_column("Tag", style="cyan", width=10)
            
            for elem in elements[:25]:
                table.add_row(elem["text"], elem["tag"])
            
            console.print(table)
            
            # Highlight booking-related elements
            console.print("\n[bold magenta]🎯 Booking-related elements found:[/bold magenta]")
            booking_keywords = ["book", "ticket", "buy", "get", "show", "seat"]
            found_booking = False
            for elem in elements:
                if any(kw in elem["text"].lower() for kw in booking_keywords):
                    console.print(f"  ✅ \"{elem['text']}\" [{elem['tag']}]")
                    found_booking = True
            
            if not found_booking:
                console.print("  [yellow]No booking elements found on this page[/yellow]")
            
            return elements
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return []
        finally:
            try:
                page.screenshot(path="bookmyshow_screenshot.png")
                console.print("\n[dim]Screenshot saved: bookmyshow_screenshot.png[/dim]")
            except:
                pass
            browser.close()
            console.print("[dim]Browser closed.[/dim]")


def main():
    parser = argparse.ArgumentParser(description="BookMyShow Correct Script - Extracts actual element texts")
    parser.add_argument("--movie", type=str, default="Border 2", help="Movie name to search")
    parser.add_argument("--city", type=str, default="Mumbai", help="City to select")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    args = parser.parse_args()
    run_bookmyshow_correct(args.movie, args.city, args.headless)


if __name__ == "__main__":
    main()
