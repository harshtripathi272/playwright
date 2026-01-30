"""
Demo Script - Run all Playwright automation examples

This script provides an interactive demo of all three automation approaches:
1. Element Extraction - Extract all elements after searching
2. Fuzzy Matching - Find elements with approximate/wrong names
3. AI Matching - Find elements using natural language intent

Usage:
    python run_demo.py
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()


def demo_element_extractor():
    """Demo the element extraction script."""
    from scripts.element_extractor import run_element_extraction
    
    console.print("\n" + "="*60)
    console.print("[bold cyan]DEMO 1: Element Extractor[/bold cyan]")
    console.print("="*60)
    
    url = Prompt.ask(
        "Enter URL", 
        default="https://en.wikipedia.org"
    )
    search = Prompt.ask(
        "Enter search query", 
        default="Python programming"
    )
    
    run_element_extraction(url, search, headless=False)


def demo_fuzzy_matcher():
    """Demo the fuzzy matching script."""
    from scripts.fuzzy_matcher import run_fuzzy_matcher
    
    console.print("\n" + "="*60)
    console.print("[bold cyan]DEMO 2: Fuzzy Element Matcher[/bold cyan]")
    console.print("="*60)
    console.print("[dim]Try entering a misspelled or approximate element name![/dim]")
    console.print("[dim]Examples: 'reed articel', 'serch', 'log n', 'contentz'[/dim]\n")
    
    url = Prompt.ask(
        "Enter URL", 
        default="https://en.wikipedia.org"
    )
    find_text = Prompt.ask(
        "Enter approximate element text (try misspelling!)", 
        default="reed articel"
    )
    click = Confirm.ask("Click on the found element?", default=False)
    
    run_fuzzy_matcher(url, find_text, threshold=40, headless=False, interact=click)


def demo_ai_matcher():
    """Demo the AI-based matching script."""
    from scripts.ai_matcher import run_ai_matcher
    
    console.print("\n" + "="*60)
    console.print("[bold cyan]DEMO 3: AI Element Matcher[/bold cyan]")
    console.print("="*60)
    console.print("[dim]Describe what you want to do in natural language![/dim]")
    console.print("[dim]Examples: 'I want to search for something', 'show me the main article'[/dim]\n")
    
    url = Prompt.ask(
        "Enter URL", 
        default="https://en.wikipedia.org"
    )
    intent = Prompt.ask(
        "Describe what you want to do", 
        default="I want to search for something"
    )
    click = Confirm.ask("Click on the found element?", default=False)
    
    api_key = Prompt.ask(
        "Enter Gemini API key (press Enter to use fuzzy fallback)", 
        default="",
        password=True
    )
    
    run_ai_matcher(
        url, 
        intent, 
        api_key=api_key if api_key else None, 
        headless=False, 
        interact=click
    )


def main():
    console.print(Panel.fit(
        "[bold blue]Playwright Automation Demo[/bold blue]\n\n"
        "This demo showcases three approaches to web automation:\n"
        "1. [cyan]Element Extractor[/cyan] - Search & extract page elements\n"
        "2. [yellow]Fuzzy Matcher[/yellow] - Find elements with approximate names\n"
        "3. [green]AI Matcher[/green] - Use AI to understand your intent\n",
        title="🚀 Welcome!"
    ))
    
    while True:
        console.print("\n[bold]Choose a demo:[/bold]")
        console.print("  [1] Element Extractor")
        console.print("  [2] Fuzzy Matcher (Self-Correcting)")
        console.print("  [3] AI Matcher (Self-Correcting)")
        console.print("  [4] Run All Demos")
        console.print("  [q] Quit")
        
        choice = Prompt.ask("Enter choice", choices=["1", "2", "3", "4", "q"], default="1")
        
        if choice == "q":
            console.print("[dim]Goodbye![/dim]")
            break
        elif choice == "1":
            demo_element_extractor()
        elif choice == "2":
            demo_fuzzy_matcher()
        elif choice == "3":
            demo_ai_matcher()
        elif choice == "4":
            demo_element_extractor()
            if Confirm.ask("\nContinue to Fuzzy Matcher demo?", default=True):
                demo_fuzzy_matcher()
            if Confirm.ask("\nContinue to AI Matcher demo?", default=True):
                demo_ai_matcher()
        
        if choice != "q" and not Confirm.ask("\nRun another demo?", default=True):
            console.print("[dim]Goodbye![/dim]")
            break


if __name__ == "__main__":
    main()
