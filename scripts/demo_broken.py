"""
Script 2: Demo Website - Broken/Self-Correcting Script

This is the BROKEN script that:
1. Opens the demo website
2. Searches for a movie
3. Opens the movie page
4. Tries to find an element with a WRONG name (e.g., "book home")
5. AUTOMATICALLY CORRECTS it to the right element (e.g., "Book Tickets")

Usage:
    python scripts/demo_broken.py --movie "Border 2" --find "book home"
    python scripts/demo_broken.py --movie "Pushpa" --find "wach tralier"
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
    
    selectors = ["button", "a", "[role='button']", ".btn", ".movie-card", ".search-item"]
    
    for selector in selectors:
        try:
            locators = page.locator(selector).all()
            for loc in locators:
                try:
                    text = loc.inner_text(timeout=1000).strip()
                    if text and len(text) > 0 and len(text) < 100:
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


def run_demo_broken(movie_name: str, wrong_element: str, headless: bool = False):
    """
    Run the broken script that auto-corrects wrong element names.
    """
    console.print(Panel.fit(
        f"[bold red]Demo Website - BROKEN Script[/bold red]\n"
        f"Movie: {movie_name}\n"
        f"Looking for: \"{wrong_element}\" [bold red](WRONG!)[/bold red]\n"
        f"This script will AUTO-CORRECT to the right element",
        title="❌ Script 2: Broken Version (Self-Correcting)"
    ))
    
    # Get the path to the demo website
    demo_path = Path(__file__).parent.parent / "demo_website" / "index.html"
    demo_url = f"file:///{demo_path.absolute()}".replace("\\", "/")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        try:
            # Step 1: Open demo website
            console.print(f"\n[yellow]Step 1:[/yellow] Opening demo website...")
            page.goto(demo_url, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            console.print("[green]✓ Demo website loaded[/green]")
            
            # Step 2: Search and select the movie
            console.print(f"\n[yellow]Step 2:[/yellow] Searching for '{movie_name}'...")
            search_input = page.locator("#searchInput")
            search_input.click()
            
            for char in movie_name:
                page.keyboard.type(char)
                page.wait_for_timeout(100)
            
            page.wait_for_timeout(500)
            
            # Select from dropdown
            try:
                movie_item = page.locator(f".search-item:has-text('{movie_name.split()[0]}')").first
                if movie_item.is_visible(timeout=2000):
                    movie_item.click()
                    console.print(f"[green]✓ Selected '{movie_name}'[/green]")
                    page.wait_for_timeout(1000)
            except:
                try:
                    movie_card = page.locator(f".movie-card:has-text('{movie_name.split()[0]}')").first
                    movie_card.click()
                    page.wait_for_timeout(1000)
                except:
                    pass
            
            # Step 3: Extract elements
            console.print(f"\n[yellow]Step 3:[/yellow] Extracting page elements...")
            elements = extract_buttons_and_links(page)
            console.print(f"[green]✓ Found {len(elements)} elements[/green]")
            
            # Step 4: Try to find the WRONG element and auto-correct
            console.print(f"\n[yellow]Step 4:[/yellow] Trying to find \"{wrong_element}\"...")
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
                
                # Show all matches
                console.print("\n[dim]All possible matches:[/dim]")
                all_matches = []
                for elem in elements:
                    score = fuzz.token_set_ratio(wrong_element.lower(), elem["text"].lower())
                    if score >= 30:
                        all_matches.append((elem["text"], score))
                
                all_matches.sort(key=lambda x: x[1], reverse=True)
                for text, score in all_matches[:10]:
                    console.print(f"  • \"{text}\" ({score}%)")
                
                # Take screenshot
                page.screenshot(path="demo_broken_result.png")
                console.print("\n[dim]Screenshot saved: demo_broken_result.png[/dim]")
                
                return result
            else:
                console.print("[red]❌ Could not find a good match[/red]")
                console.print("\n[yellow]Available elements:[/yellow]")
                for elem in elements[:15]:
                    console.print(f"  • \"{elem['text']}\"")
                return None
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return None
        finally:
            browser.close()
            console.print("[dim]Browser closed.[/dim]")


def main():
    parser = argparse.ArgumentParser(description="Demo Website Broken Script - Auto-corrects wrong element names")
    parser.add_argument("--movie", type=str, default="Border 2", help="Movie name to search")
    parser.add_argument("--find", type=str, default="book home", help="The WRONG element text (will be auto-corrected)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    args = parser.parse_args()
    run_demo_broken(args.movie, args.find, args.headless)


if __name__ == "__main__":
    main()
