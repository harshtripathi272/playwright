"""
Script 1: Element Extractor

This script demonstrates how to:
1. Navigate to a website
2. Perform a search
3. Extract all interactive elements from the results page

Usage:
    python scripts/element_extractor.py --url "https://en.wikipedia.org" --search "Python programming"
    python scripts/element_extractor.py --url "https://www.imdb.com" --search "Inception"
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from rich.console import Console
from rich.panel import Panel
from utils.helpers import extract_all_elements, display_elements_table, find_search_input

console = Console()


def run_element_extraction(url: str, search_query: str, headless: bool = False):
    """
    Main function to extract elements from a website after searching.
    
    Args:
        url: Website URL to navigate to
        search_query: Term to search for
        headless: Run browser in headless mode (default: False for visibility)
    """
    console.print(Panel.fit(
        f"[bold blue]Element Extractor[/bold blue]\n"
        f"URL: {url}\n"
        f"Search: {search_query}",
        title="🔍 Starting Extraction"
    ))
    
    with sync_playwright() as p:
        # Launch browser (visible by default for demo purposes)
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()
        
        try:
            # Step 1: Navigate to the URL
            console.print(f"\n[yellow]Step 1:[/yellow] Navigating to {url}...")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)  # Wait for dynamic content
            console.print("[green]✓ Page loaded successfully[/green]")
            
            # Step 2: Find and use the search input
            console.print(f"\n[yellow]Step 2:[/yellow] Searching for '{search_query}'...")
            try:
                search_input = find_search_input(page)
                search_input.click()
                search_input.fill(search_query)
                search_input.press("Enter")
                console.print("[green]✓ Search submitted[/green]")
            except Exception as e:
                console.print(f"[red]Could not find search input: {e}[/red]")
                console.print("[yellow]Continuing with current page elements...[/yellow]")
            
            # Step 3: Wait for results to load
            console.print(f"\n[yellow]Step 3:[/yellow] Waiting for results...")
            page.wait_for_timeout(3000)  # Wait for search results
            console.print("[green]✓ Results loaded[/green]")
            
            # Step 4: Extract all elements
            console.print(f"\n[yellow]Step 4:[/yellow] Extracting page elements...")
            elements = extract_all_elements(page)
            console.print(f"[green]✓ Found {len(elements)} interactive elements[/green]")
            
            # Step 5: Display results
            console.print(f"\n[yellow]Step 5:[/yellow] Displaying results...")
            display_elements_table(elements, title=f"Elements on '{search_query}' results page")
            
            # Show some example elements with text containing keywords
            console.print("\n[bold magenta]🎯 Notable Elements (buttons, links with text):[/bold magenta]")
            notable = [e for e in elements if e.get("tag") in ["button", "a"] and len(e.get("text", "")) > 3]
            for elem in notable[:10]:
                console.print(f"  • [{elem['tag']}] \"{elem['text']}\" → {elem['selector']}")
            
            return elements
            
        except PlaywrightTimeout as e:
            console.print(f"[red]Timeout error: {e}[/red]")
            return []
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return []
        finally:
            browser.close()
            console.print("\n[dim]Browser closed.[/dim]")


def main():
    parser = argparse.ArgumentParser(
        description="Extract interactive elements from a webpage after searching"
    )
    parser.add_argument(
        "--url", 
        type=str, 
        default="https://en.wikipedia.org",
        help="URL of the website to scrape"
    )
    parser.add_argument(
        "--search", 
        type=str, 
        default="Python programming language",
        help="Search query to enter"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    
    args = parser.parse_args()
    run_element_extraction(args.url, args.search, args.headless)


if __name__ == "__main__":
    main()
