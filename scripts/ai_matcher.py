"""
Script 2B: AI-Based Element Matcher

This script uses Google's Gemini AI to understand your intent
and find the correct element on the page.

Instead of relying on exact text matching, it understands what you MEAN
and finds the most appropriate element.

Example:
    - You say: "I want to book movie tickets"
    - AI finds: The "Book Tickets" or "Buy Now" button

Requirements:
    Set GEMINI_API_KEY environment variable or pass via --api-key

Usage:
    python scripts/ai_matcher.py --url "https://en.wikipedia.org" --intent "I want to search for something"
    python scripts/ai_matcher.py --url "https://www.imdb.com" --intent "show me movie ratings"
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright, Page
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from utils.helpers import extract_all_elements

console = Console()

# Try to import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    console.print("[yellow]⚠ google-generativeai not installed. AI features disabled.[/yellow]")


def setup_gemini(api_key: Optional[str] = None) -> bool:
    """Configure Gemini API with the provided key."""
    if not GEMINI_AVAILABLE:
        return False
    
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        console.print("[yellow]⚠ No Gemini API key found. Set GEMINI_API_KEY or use --api-key[/yellow]")
        return False
    
    genai.configure(api_key=key)
    return True


def ai_find_element(
    intent: str, 
    elements: List[Dict[str, Any]],
    model_name: str = "gemini-2.5-flash"
) -> Dict[str, Any]:
    """
    Use Gemini AI to find the element that best matches the user's intent.
    
    Args:
        intent: Natural language description of what the user wants to do
        elements: List of elements extracted from the page
        model_name: Gemini model to use
    
    Returns:
        Dictionary with the matched element and AI's reasoning
    """
    # Prepare element list for the prompt
    element_list = []
    for i, elem in enumerate(elements[:100]):  # Limit to 100 elements
        text = elem.get("text", "")
        tag = elem.get("tag", "")
        if text:
            element_list.append(f"{i}. [{tag}] \"{text}\"")
    
    elements_text = "\n".join(element_list)
    
    prompt = f"""You are a web automation assistant. The user wants to interact with a webpage.

USER'S INTENT: "{intent}"

Here are the interactive elements on the page (index, tag, text):
{elements_text}

Your task:
1. Understand what the user wants to do
2. Find the element that best matches their intent
3. Return ONLY a JSON object with this format:
{{
    "matched_index": <number>,
    "element_text": "<the text of the matched element>",
    "confidence": <0-100>,
    "reasoning": "<brief explanation of why this element matches>"
}}

If no element matches, return:
{{
    "matched_index": -1,
    "element_text": null,
    "confidence": 0,
    "reasoning": "<explanation>"
}}

Return ONLY the JSON, no other text."""

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        
        # Parse the response
        import json
        response_text = response.text.strip()
        
        # Clean up response if it has markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        
        # Add the full element info if found
        matched_index = result.get("matched_index", -1)
        if 0 <= matched_index < len(elements):
            result["element"] = elements[matched_index]
        
        return result
        
    except Exception as e:
        console.print(f"[red]AI Error: {e}[/red]")
        return {
            "matched_index": -1,
            "element_text": None,
            "confidence": 0,
            "reasoning": f"Error: {str(e)}"
        }


def fallback_fuzzy_match(intent: str, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fallback to fuzzy matching when AI is not available."""
    from rapidfuzz import fuzz
    
    best_match = None
    best_score = 0
    
    # Extract keywords from intent
    keywords = intent.lower().split()
    
    for elem in elements:
        text = elem.get("text", "").lower()
        if not text:
            continue
        
        # Calculate score based on keyword presence and fuzzy matching
        score = 0
        for keyword in keywords:
            if keyword in text:
                score += 30
            score += fuzz.partial_ratio(keyword, text) * 0.5
        
        if score > best_score:
            best_score = score
            best_match = elem
    
    if best_match:
        return {
            "matched_index": elements.index(best_match) if best_match in elements else -1,
            "element_text": best_match.get("text"),
            "confidence": min(int(best_score), 100),
            "reasoning": "Matched using fuzzy keyword matching (AI not available)",
            "element": best_match
        }
    
    return {
        "matched_index": -1,
        "element_text": None,
        "confidence": 0,
        "reasoning": "No match found"
    }


def display_ai_result(intent: str, result: Dict[str, Any]):
    """Display the AI matching result."""
    console.print(f"\n[bold cyan]🤖 AI Intent Understanding[/bold cyan]")
    console.print(f"[yellow]Your intent:[/yellow] \"{intent}\"\n")
    
    if result.get("matched_index", -1) >= 0:
        confidence = result.get("confidence", 0)
        conf_color = "green" if confidence >= 80 else "yellow" if confidence >= 50 else "red"
        
        console.print(Panel.fit(
            f"[bold green]✅ Element Found![/bold green]\n\n"
            f"[yellow]Matched Element:[/yellow] \"{result.get('element_text', 'N/A')}\"\n"
            f"[{conf_color}]Confidence:[/{conf_color}] {confidence}%\n"
            f"[cyan]AI Reasoning:[/cyan] {result.get('reasoning', 'N/A')}\n"
            f"[magenta]Selector:[/magenta] {result.get('element', {}).get('selector', 'N/A')}",
            title="🎯 AI Match Result"
        ))
    else:
        console.print(Panel.fit(
            f"[bold red]❌ No Match Found[/bold red]\n\n"
            f"[cyan]AI Reasoning:[/cyan] {result.get('reasoning', 'No suitable element found')}",
            title="AI Result"
        ))


def run_ai_matcher(
    url: str,
    intent: str,
    api_key: Optional[str] = None,
    headless: bool = False,
    interact: bool = False
):
    """
    Main function to find elements using AI intent understanding.
    
    Args:
        url: Website URL to navigate to
        intent: Natural language description of what to do
        api_key: Optional Gemini API key
        headless: Run browser in headless mode
        interact: Whether to click the found element
    """
    console.print(Panel.fit(
        f"[bold blue]AI Element Matcher[/bold blue]\n"
        f"URL: {url}\n"
        f"Intent: \"{intent}\"",
        title="🤖 AI-Powered Self-Correcting Script"
    ))
    
    # Setup Gemini
    gemini_ready = setup_gemini(api_key)
    if not gemini_ready:
        console.print("[yellow]Will use fuzzy matching as fallback[/yellow]")
    
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
            
            # Find element using AI or fallback
            console.print(f"\n[yellow]Step 3:[/yellow] Analyzing intent with {'AI' if gemini_ready else 'fuzzy matching'}...")
            
            if gemini_ready:
                result = ai_find_element(intent, elements)
            else:
                result = fallback_fuzzy_match(intent, elements)
            
            # Display results
            display_ai_result(intent, result)
            
            # Optionally interact with the element
            if interact and result.get("matched_index", -1) >= 0:
                elem = result.get("element", {})
                selector = elem.get("selector", "")
                if selector:
                    console.print(f"\n[yellow]Step 4:[/yellow] Clicking on \"{elem.get('text')}\"...")
                    try:
                        page.locator(selector).first.click(timeout=5000)
                        page.wait_for_timeout(2000)
                        console.print(f"[green]✓ Clicked successfully! New URL: {page.url}[/green]")
                    except Exception as e:
                        console.print(f"[red]Could not click: {e}[/red]")
            
            return result
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return {}
        finally:
            browser.close()
            console.print("\n[dim]Browser closed.[/dim]")


def main():
    parser = argparse.ArgumentParser(
        description="Find elements using AI intent understanding"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="https://en.wikipedia.org",
        help="URL of the website"
    )
    parser.add_argument(
        "--intent",
        type=str,
        required=True,
        help="Natural language description of what you want to do"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Gemini API key (or set GEMINI_API_KEY env variable)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--click",
        action="store_true",
        help="Click on the matched element"
    )
    
    args = parser.parse_args()
    run_ai_matcher(args.url, args.intent, args.api_key, args.headless, args.click)


if __name__ == "__main__":
    main()
