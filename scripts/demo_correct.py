"""
Script 1: Demo Website - Correct Script

This is the CORRECT script that works with our demo website:
1. Opens the demo website
2. Searches for a movie (e.g., "Border 2")
3. Selects the movie from dropdown
4. Opens the movie page
5. Extracts all elements including "Book Tickets" button

Usage:
    python scripts/demo_correct.py --movie "Border 2"
    python scripts/demo_correct.py --movie "Pushpa"
"""

import argparse
import sys
import os
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


def run_demo_correct(movie_name: str, headless: bool = False):
    """
    Run the correct script on our demo website.
    """
    console.print(Panel.fit(
        f"[bold green]Demo Website - CORRECT Script[/bold green]\n"
        f"Movie: {movie_name}\n"
        f"This script extracts the ACTUAL button texts",
        title="✅ Script 1: Correct Version"
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
            
            # Step 2: Search for the movie
            console.print(f"\n[yellow]Step 2:[/yellow] Searching for '{movie_name}'...")
            search_input = page.locator("#searchInput")
            search_input.click()
            
            # Type the movie name to trigger dropdown
            for char in movie_name:
                page.keyboard.type(char)
                page.wait_for_timeout(100)
            
            page.wait_for_timeout(500)
            console.print("[green]✓ Search dropdown appeared[/green]")
            
            # Take screenshot of dropdown
            page.screenshot(path="demo_search_dropdown.png")
            console.print("[dim]Screenshot saved: demo_search_dropdown.png[/dim]")
            
            # Step 3: Select the movie from dropdown
            console.print(f"\n[yellow]Step 3:[/yellow] Selecting movie from dropdown...")
            try:
                movie_item = page.locator(f".search-item:has-text('{movie_name.split()[0]}')").first
                if movie_item.is_visible(timeout=2000):
                    movie_item.click()
                    console.print(f"[green]✓ Selected '{movie_name}' from dropdown[/green]")
                    page.wait_for_timeout(1000)
            except:
                # Try clicking on movie card directly
                try:
                    movie_card = page.locator(f".movie-card:has-text('{movie_name.split()[0]}')").first
                    movie_card.click()
                    console.print(f"[green]✓ Clicked on '{movie_name}' movie card[/green]")
                    page.wait_for_timeout(1000)
                except:
                    console.print("[yellow]⚠ Could not find movie, showing current elements[/yellow]")
            
            # Step 4: Extract all elements from the movie page
            console.print(f"\n[yellow]Step 4:[/yellow] Extracting page elements...")
            elements = extract_buttons_and_links(page)
            console.print(f"[green]✓ Found {len(elements)} elements[/green]")
            
            # Take screenshot of movie page
            page.screenshot(path="demo_movie_page.png")
            console.print("[dim]Screenshot saved: demo_movie_page.png[/dim]")
            
            # Step 5: Display results
            console.print(f"\n[yellow]Step 5:[/yellow] Here are the CORRECT element texts:\n")
            
            table = Table(title="Available Page Elements (Correct Texts)", show_header=True)
            table.add_column("Text", style="green", width=50)
            table.add_column("Tag", style="cyan", width=10)
            
            for elem in elements[:20]:
                table.add_row(elem["text"][:50], elem["tag"])
            
            console.print(table)
            
            # Highlight the important buttons
            console.print("\n[bold magenta]🎯 Key buttons found:[/bold magenta]")
            important_keywords = ["book", "ticket", "trailer", "wishlist", "watch"]
            for elem in elements:
                if any(kw in elem["text"].lower() for kw in important_keywords):
                    console.print(f"  ✅ \"{elem['text']}\" [{elem['tag']}]")
            
            return elements
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return []
        finally:
            browser.close()
            console.print("\n[dim]Browser closed.[/dim]")


def main():
    parser = argparse.ArgumentParser(description="Demo Website Correct Script")
    parser.add_argument("--movie", type=str, default="Border 2", help="Movie name to search")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    args = parser.parse_args()
    run_demo_correct(args.movie, args.headless)


if __name__ == "__main__":
    main()
