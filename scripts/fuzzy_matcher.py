"""
Script 2A: Fuzzy Element Matcher

This script demonstrates how to find elements using fuzzy string matching.
If you provide an approximate or misspelled element description,
it will find the closest matching element on the page.

Example:
    - You say: "book home" 
    - It finds: "Book Tickets" (closest match)

Usage:
    python scripts/fuzzy_matcher.py --url "https://en.wikipedia.org" --find "reed articel"
    python scripts/fuzzy_matcher.py --url "https://www.imdb.com" --find "wach trailor"
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright, Page
from rapidfuzz import fuzz, process
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from utils.helpers import extract_all_elements

console = Console()


def find_best_match(
    search_text: str, 
    elements: List[Dict[str, Any]], 
    threshold: int = 50
) -> List[Tuple[Dict[str, Any], int]]:
    """
    Find elements that best match the search text using fuzzy matching.
    
    Args:
        search_text: The approximate text to search for
        elements: List of element dictionaries from the page
        threshold: Minimum similarity score (0-100) to consider a match
    
    Returns:
        List of (element, score) tuples, sorted by score descending
    """
    matches = []
    search_lower = search_text.lower()
    search_len = len(search_text)
    
    for elem in elements:
        elem_text = elem.get("text", "")
        if not elem_text:
            continue
        
        elem_lower = elem_text.lower()
        elem_len = len(elem_text)
        
        # Calculate multiple fuzzy matching scores
        ratio = fuzz.ratio(search_lower, elem_lower)
        partial_ratio = fuzz.partial_ratio(search_lower, elem_lower)
        token_sort = fuzz.token_sort_ratio(search_lower, elem_lower)
        token_set = fuzz.token_set_ratio(search_lower, elem_lower)
        
        # IMPORTANT: Penalize very short element texts that match via partial_ratio
        # This prevents "Art" from matching "reed articel" with 100%
        # The penalty increases as the length difference grows
        length_ratio = min(elem_len, search_len) / max(elem_len, search_len) if max(elem_len, search_len) > 0 else 0
        
        # Apply length penalty to partial_ratio
        # If element is much shorter than search text, reduce its partial_ratio score
        if elem_len < search_len * 0.5:  # Element is less than half the search length
            partial_ratio = partial_ratio * (elem_len / search_len)
        
        # Weighted scoring: prefer token-based matching for multi-word phrases
        # token_sort handles word reordering, token_set handles word subsets
        word_count = len(search_text.split())
        
        if word_count >= 2:
            # For multi-word searches, prefer token-based matching
            best_score = max(
                ratio,
                token_sort,
                token_set,
                partial_ratio * 0.8  # Reduce weight of partial matching
            )
        else:
            # For single-word searches, use standard matching
            best_score = max(ratio, token_sort, partial_ratio * 0.9)
        
        # Boost score if lengths are similar (good for typo correction)
        if 0.7 <= length_ratio <= 1.0:
            best_score = min(100, best_score * 1.1)
        
        if best_score >= threshold:
            matches.append((elem, round(best_score, 1)))
    
    # Sort by score descending
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


def display_matches(
    search_text: str, 
    matches: List[Tuple[Dict[str, Any], int]], 
    top_n: int = 5
):
    """Display the top matching elements in a nice table."""
    console.print(f"\n[bold cyan]🔍 Searching for: [yellow]\"{search_text}\"[/yellow][/bold cyan]\n")
    
    if not matches:
        console.print("[red]❌ No matches found![/red]")
        return
    
    table = Table(title=f"Top {min(top_n, len(matches))} Matches", show_header=True, header_style="bold magenta")
    table.add_column("Rank", style="cyan", width=6)
    table.add_column("Score", style="green", width=8)
    table.add_column("Element Text", style="yellow", width=40)
    table.add_column("Tag", style="blue", width=10)
    table.add_column("Selector", style="white", width=25)
    
    for i, (elem, score) in enumerate(matches[:top_n], 1):
        score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
        table.add_row(
            f"#{i}",
            f"[{score_color}]{score}%[/{score_color}]",
            elem.get("text", "")[:40],
            elem.get("tag", ""),
            elem.get("selector", "")[:25]
        )
    
    console.print(table)
    
    # Show the best match prominently
    if matches:
        best_elem, best_score = matches[0]
        console.print(Panel.fit(
            f"[bold green]✅ Best Match Found![/bold green]\n\n"
            f"[yellow]You said:[/yellow] \"{search_text}\"\n"
            f"[green]Corrected to:[/green] \"{best_elem.get('text', '')}\"\n"
            f"[cyan]Confidence:[/cyan] {best_score}%\n"
            f"[magenta]Selector:[/magenta] {best_elem.get('selector', '')}",
            title="🎯 Auto-Correction Result"
        ))


def run_fuzzy_matcher(
    url: str, 
    find_text: str, 
    threshold: int = 50,
    headless: bool = False,
    interact: bool = False
):
    """
    Main function to find and optionally interact with elements using fuzzy matching.
    
    Args:
        url: Website URL to navigate to
        find_text: Approximate element text to find
        threshold: Minimum similarity score to consider a match
        headless: Run browser in headless mode
        interact: Whether to click the found element
    """
    console.print(Panel.fit(
        f"[bold blue]Fuzzy Element Matcher[/bold blue]\n"
        f"URL: {url}\n"
        f"Finding: \"{find_text}\"\n"
        f"Threshold: {threshold}%",
        title="🔧 Self-Correcting Script"
    ))
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()
        
        try:
            # Navigate to URL
            console.print(f"\n[yellow]Step 1:[/yellow] Navigating to {url}...")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)
            console.print("[green]✓ Page loaded[/green]")
            
            # Extract elements
            console.print(f"\n[yellow]Step 2:[/yellow] Extracting page elements...")
            elements = extract_all_elements(page)
            console.print(f"[green]✓ Found {len(elements)} elements[/green]")
            
            # Find matches
            console.print(f"\n[yellow]Step 3:[/yellow] Finding matches for \"{find_text}\"...")
            matches = find_best_match(find_text, elements, threshold)
            
            # Display results
            display_matches(find_text, matches)
            
            # Optionally interact with the best match
            if interact and matches:
                best_elem, score = matches[0]
                selector = best_elem.get("selector", "")
                if selector:
                    console.print(f"\n[yellow]Step 4:[/yellow] Clicking on \"{best_elem.get('text')}\"...")
                    try:
                        page.locator(selector).first.click(timeout=5000)
                        page.wait_for_timeout(2000)
                        console.print(f"[green]✓ Clicked successfully! New URL: {page.url}[/green]")
                    except Exception as e:
                        console.print(f"[red]Could not click: {e}[/red]")
            
            return matches
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return []
        finally:
            browser.close()
            console.print("\n[dim]Browser closed.[/dim]")


def main():
    parser = argparse.ArgumentParser(
        description="Find elements on a page using fuzzy string matching"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="https://en.wikipedia.org",
        help="URL of the website"
    )
    parser.add_argument(
        "--find",
        type=str,
        required=True,
        help="Approximate text of the element to find (can be misspelled)"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=50,
        help="Minimum similarity score (0-100) to consider a match"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--click",
        action="store_true",
        help="Click on the best matching element"
    )
    
    args = parser.parse_args()
    run_fuzzy_matcher(args.url, args.find, args.threshold, args.headless, args.click)


if __name__ == "__main__":
    main()
