"""
Script 2: BookMyShow Broken/Self-Correcting Script

This is the BROKEN script that:
1. Goes to BookMyShow
2. Selects a city (e.g., Mumbai)
3. Searches for a movie (e.g., "Border 2")
4. Selects the movie from dropdown
5. Opens the movie page
6. Tries to find an element with a WRONG name (e.g., "book home")
7. AUTOMATICALLY CORRECTS it to the right element (e.g., "Book Tickets")

Usage:
    python scripts/bookmyshow_broken.py --movie "Border 2" --city "Mumbai" --find "book home"
    python scripts/bookmyshow_broken.py --movie "Pushpa 2" --city "Delhi" --find "by tickts"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
from rapidfuzz import fuzz
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


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
                            "selector": selector,
                            "locator": loc
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
    """Search for a movie and select it from the dropdown."""
    console.print(f"[cyan]Searching for: {movie_name}[/cyan]")
    
    try:
        search_selectors = [
            "input[placeholder*='Search']",
            "input[type='search']",
            ".search-input",
            "#searchInput"
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
            try:
                page.locator("text=Search for Movies").first.click(timeout=3000)
                page.wait_for_timeout(500)
                search_input = page.locator("input:visible").first
            except:
                console.print("[red]Could not find search input[/red]")
                return False
        
        # Type the movie name slowly to trigger dropdown
        search_input.click()
        page.wait_for_timeout(500)
        search_input.fill("")
        
        for char in movie_name:
            search_input.type(char, delay=100)
        
        console.print("[green]✓ Typed movie name[/green]")
        page.wait_for_timeout(2000)
        
        # Look for the movie in the dropdown
        dropdown_selectors = [
            f"li:has-text('{movie_name}')",
            f"div:has-text('{movie_name}')",
            f"a:has-text('{movie_name}')",
        ]
        
        for selector in dropdown_selectors:
            try:
                movie_option = page.locator(selector).first
                if movie_option.is_visible(timeout=2000):
                    movie_option.click()
                    console.print(f"[green]✓ Selected '{movie_name}' from dropdown[/green]")
                    page.wait_for_timeout(3000)
                    return True
            except:
                continue
        
        # Fallback: press Enter
        search_input.press("Enter")
        page.wait_for_timeout(3000)
        
        try:
            movie_link = page.locator(f"a:has-text('{movie_name}')").first
            if movie_link.is_visible(timeout=5000):
                movie_link.click()
                console.print(f"[green]✓ Clicked on '{movie_name}' in results[/green]")
                page.wait_for_timeout(3000)
                return True
        except:
            pass
        
        return False
        
    except Exception as e:
        console.print(f"[red]Search error: {e}[/red]")
        return False


def find_and_correct(wrong_text: str, elements: list) -> dict:
    """
    Find the correct element that matches the wrong/broken text.
    Uses fuzzy matching to auto-correct.
    """
    best_match = None
    best_score = 0
    
    wrong_lower = wrong_text.lower()
    wrong_len = len(wrong_text)
    
    for elem in elements:
        elem_text = elem["text"]
        elem_lower = elem_text.lower()
        elem_len = len(elem_text)
        
        # Calculate fuzzy scores
        ratio = fuzz.ratio(wrong_lower, elem_lower)
        token_sort = fuzz.token_sort_ratio(wrong_lower, elem_lower)
        token_set = fuzz.token_set_ratio(wrong_lower, elem_lower)
        partial = fuzz.partial_ratio(wrong_lower, elem_lower)
        
        # Length penalty for very different lengths
        length_ratio = min(elem_len, wrong_len) / max(elem_len, wrong_len) if max(elem_len, wrong_len) > 0 else 0
        
        if elem_len < wrong_len * 0.4:
            partial = partial * 0.5
        
        score = max(ratio, token_sort, token_set, partial * 0.9)
        
        if 0.6 <= length_ratio <= 1.0:
            score = min(100, score * 1.1)
        
        if score > best_score:
            best_score = score
            best_match = {
                "original_wrong": wrong_text,
                "corrected_text": elem_text,
                "score": round(score, 1),
                "element": elem
            }
    
    return best_match


def run_bookmyshow_broken(movie_name: str, city_name: str, wrong_element: str, headless: bool = False):
    """
    Run the broken script that auto-corrects wrong element names.
    """
    console.print(Panel.fit(
        f"[bold red]BookMyShow - BROKEN Script[/bold red]\n"
        f"City: {city_name}\n"
        f"Movie: {movie_name}\n"
        f"Looking for: \"{wrong_element}\" [bold red](WRONG!)[/bold red]\n"
        f"This script will AUTO-CORRECT to the right element",
        title="❌ Script 2: Broken Version (Self-Correcting)"
    ))
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
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
                console.print(f"[yellow]⚠ Could not open movie page[/yellow]")
            
            # Step 4: Extract elements
            console.print(f"\n[yellow]Step 4:[/yellow] Extracting page elements...")
            page.wait_for_timeout(2000)
            elements = extract_buttons_and_links(page)
            console.print(f"[green]✓ Found {len(elements)} elements[/green]")
            
            # Step 5: Try to find the WRONG element and auto-correct
            console.print(f"\n[yellow]Step 5:[/yellow] Trying to find \"{wrong_element}\"...")
            console.print(f"[red]❌ ERROR: Element \"{wrong_element}\" not found exactly![/red]")
            console.print(f"[cyan]🔧 Attempting auto-correction...[/cyan]\n")
            
            # Find the best match
            result = find_and_correct(wrong_element, elements)
            
            if result and result["score"] >= 40:
                console.print(Panel.fit(
                    f"[bold green]✅ AUTO-CORRECTION SUCCESSFUL![/bold green]\n\n"
                    f"[red]You said (WRONG):[/red] \"{result['original_wrong']}\"\n"
                    f"[green]Corrected to:[/green] \"{result['corrected_text']}\"\n"
                    f"[cyan]Confidence:[/cyan] {result['score']}%\n"
                    f"[magenta]Element type:[/magenta] {result['element']['tag']}",
                    title="🎯 Self-Correction Result"
                ))
                
                # Show other possible matches
                console.print("\n[dim]Other possible matches:[/dim]")
                for elem in elements[:15]:
                    score = fuzz.token_set_ratio(wrong_element.lower(), elem["text"].lower())
                    if score >= 30 and elem["text"] != result["corrected_text"]:
                        console.print(f"  • \"{elem['text']}\" ({score}%)")
                
                return result
            else:
                console.print("[red]❌ Could not find a good match for auto-correction[/red]")
                console.print("\n[yellow]Available elements on page:[/yellow]")
                for elem in elements[:20]:
                    console.print(f"  • \"{elem['text']}\"")
                return None
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return None
        finally:
            try:
                page.screenshot(path="bookmyshow_broken_screenshot.png")
                console.print("\n[dim]Screenshot saved: bookmyshow_broken_screenshot.png[/dim]")
            except:
                pass
            browser.close()
            console.print("[dim]Browser closed.[/dim]")


def main():
    parser = argparse.ArgumentParser(description="BookMyShow Broken Script - Auto-corrects wrong element names")
    parser.add_argument("--movie", type=str, default="Border 2", help="Movie name to search")
    parser.add_argument("--city", type=str, default="Mumbai", help="City to select")
    parser.add_argument("--find", type=str, default="book home", help="The WRONG element text (will be auto-corrected)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    args = parser.parse_args()
    run_bookmyshow_broken(args.movie, args.city, args.find, args.headless)


if __name__ == "__main__":
    main()
