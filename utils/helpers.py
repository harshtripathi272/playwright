"""
Common utility functions for Playwright automation scripts.
"""

from playwright.sync_api import Page, Locator
from rich.console import Console
from rich.table import Table
from typing import List, Dict, Any

console = Console()


def extract_all_elements(page: Page) -> List[Dict[str, Any]]:
    """
    Extract all interactive elements from a page.
    
    Returns a list of dictionaries containing:
    - tag: HTML tag name
    - text: Visible text content
    - selector: CSS selector to find this element
    - attributes: Important attributes (id, class, href, etc.)
    """
    elements = []
    
    # Define selectors for interactive elements
    interactive_selectors = [
        "a",           # Links
        "button",      # Buttons
        "input",       # Input fields
        "select",      # Dropdowns
        "[role='button']",  # Elements with button role
        "[onclick]",   # Elements with click handlers
    ]
    
    for selector in interactive_selectors:
        try:
            locators = page.locator(selector).all()
            for locator in locators:
                try:
                    element_info = extract_element_info(locator, selector)
                    if element_info and element_info.get("text"):  # Only include elements with text
                        elements.append(element_info)
                except Exception:
                    continue  # Skip elements that can't be processed
        except Exception:
            continue
    
    return elements


def extract_element_info(locator: Locator, base_selector: str) -> Dict[str, Any]:
    """Extract information from a single element."""
    try:
        text = locator.inner_text(timeout=1000).strip()
        if not text:
            text = locator.get_attribute("value") or ""
            text = text.strip() if text else ""
        
        # Get attributes
        tag = locator.evaluate("el => el.tagName.toLowerCase()")
        element_id = locator.get_attribute("id") or ""
        element_class = locator.get_attribute("class") or ""
        href = locator.get_attribute("href") or ""
        placeholder = locator.get_attribute("placeholder") or ""
        
        # Build a unique selector
        if element_id:
            unique_selector = f"#{element_id}"
        elif element_class:
            first_class = element_class.split()[0] if element_class else ""
            unique_selector = f"{tag}.{first_class}" if first_class else tag
        else:
            unique_selector = base_selector
        
        return {
            "tag": tag,
            "text": text[:100] if text else placeholder[:100],  # Limit text length
            "selector": unique_selector,
            "id": element_id,
            "class": element_class[:50] if element_class else "",
            "href": href[:100] if href else "",
        }
    except Exception:
        return None


def display_elements_table(elements: List[Dict[str, Any]], title: str = "Page Elements"):
    """Display extracted elements in a nice table format."""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    
    table.add_column("Tag", style="cyan", width=10)
    table.add_column("Text", style="green", width=40)
    table.add_column("Selector", style="yellow", width=30)
    table.add_column("ID", style="blue", width=20)
    
    for elem in elements[:50]:  # Limit to 50 elements for display
        table.add_row(
            elem.get("tag", ""),
            elem.get("text", "")[:40],  # Truncate long text
            elem.get("selector", ""),
            elem.get("id", "")
        )
    
    console.print(table)
    console.print(f"\n[bold]Total elements found: {len(elements)}[/bold]")


def find_search_input(page: Page) -> Locator:
    """
    Try to find a search input on the page using common patterns.
    """
    search_selectors = [
        "input[type='search']",
        "input[name='search']",
        "input[name='q']",
        "input[placeholder*='search' i]",
        "input[placeholder*='Search' i]",
        "input[aria-label*='search' i]",
        "#search",
        "#searchInput",
        ".search-input",
        "input[type='text']",  # Fallback to first text input
    ]
    
    for selector in search_selectors:
        try:
            locator = page.locator(selector).first
            if locator.is_visible(timeout=1000):
                return locator
        except Exception:
            continue
    
    raise Exception("Could not find search input on the page")
