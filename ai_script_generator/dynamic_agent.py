"""
Dynamic Agentic Playwright Agent

A think-act loop agent that:
1. Executes one action at a time
2. Extracts page elements after each action
3. Asks LLM to decide the next step based on live page state
4. Retries up to 3 times if an action fails

This is more adaptive than static script generation because
it sees the actual page before deciding what to do.
"""
import time
import random
import json
import re
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright, Page
from playwright_stealth.stealth import Stealth
import google.generativeai as genai

from config import GEMINI_API_KEY, MODEL_NAME, MAX_RETRIES


# Prompt for the dynamic agent
DYNAMIC_AGENT_PROMPT = """You are a Playwright automation expert controlling a browser in real-time.

CURRENT GOAL: {goal}
CURRENT URL: {url}
STEPS COMPLETED: {steps_completed}

ELEMENTS ON PAGE (visible, interactive):
{elements}

Based on the elements you can see, decide the NEXT SINGLE ACTION to take.

AVAILABLE ACTIONS:
- click: Click on an element. Provide selector.
- type: Type text into an input. Provide selector and text.
- press: Press a key (Enter, Escape, Tab). Provide key.
- goto: Navigate to a URL. Provide url.
- wait: Wait for page to load. Provide seconds (1-5).
- done: Goal is achieved, stop.
- fail: Cannot proceed, give up.

RESPONSE FORMAT (JSON only):
{{
  "thought": "Brief reasoning about current state and what to do",
  "action": "click|type|press|goto|wait|done|fail",
  "selector": "CSS selector or text=... (for click/type)",
  "text": "text to type (for type action)",
  "key": "key to press (for press action)",
  "url": "URL (for goto action)",
  "seconds": 2 (for wait action),
  "done": true/false
}}

IMPORTANT RULES:
- Always use text=... selectors when possible (e.g., text=Mumbai)
- For search inputs, look for input[placeholder*='Search'] or similar
- If you see a city popup, click the city first
- After typing in search, wait 3 seconds for dropdown
- Click dropdown results using text matching
- Set done=true only when you've achieved the goal

Respond with ONLY the JSON, no other text.
"""


def random_delay(min_ms=100, max_ms=500):
    """Add random delay to mimic human behavior."""
    time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))


def move_mouse_randomly(page: Page):
    """Move mouse to random positions."""
    for _ in range(2):
        x = random.randint(100, 800)
        y = random.randint(100, 500)
        page.mouse.move(x, y)
        random_delay(50, 150)


def extract_elements(page: Page) -> List[Dict[str, Any]]:
    """Extract visible interactive elements from the page."""
    elements = []
    
    selectors = [
        "a", "button", "input", "[role='button']",
        "li", "div[role='option']", "[onclick]"
    ]
    
    for selector in selectors:
        try:
            locators = page.locator(selector).all()
            for loc in locators[:30]:  # Limit per selector
                try:
                    if not loc.is_visible(timeout=500):
                        continue
                    
                    text = loc.inner_text(timeout=500).strip()[:80]
                    if not text:
                        text = loc.get_attribute("placeholder") or ""
                        text = text[:80]
                    
                    if not text:
                        continue
                    
                    tag = loc.evaluate("el => el.tagName.toLowerCase()")
                    elem_id = loc.get_attribute("id") or ""
                    elem_class = loc.get_attribute("class") or ""
                    
                    # Build selector
                    if elem_id:
                        css_selector = f"#{elem_id}"
                    elif "search" in text.lower() or "search" in elem_class.lower():
                        css_selector = f"input[placeholder*='Search']"
                    else:
                        css_selector = f"text={text[:40]}"
                    
                    elements.append({
                        "tag": tag,
                        "text": text,
                        "selector": css_selector,
                        "id": elem_id[:30],
                    })
                except:
                    continue
        except:
            continue
    
    # Remove duplicates
    seen = set()
    unique = []
    for elem in elements:
        key = elem["text"][:30]
        if key and key not in seen:
            seen.add(key)
            unique.append(elem)
    
    return unique[:50]  # Limit total


def format_elements_for_prompt(elements: List[Dict]) -> str:
    """Format elements for LLM prompt."""
    lines = []
    for i, elem in enumerate(elements):
        lines.append(f"{i+1}. [{elem['tag']}] \"{elem['text']}\" → {elem['selector']}")
    return "\n".join(lines) if lines else "(No visible interactive elements found)"


class DynamicAgent:
    """Think-Act loop agent that decides actions based on live page state."""
    
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set")
        
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(MODEL_NAME)
        self.max_steps = 20
        self.action_retries = 3  # Retry each action up to 3 times
    
    def run(self, goal: str, start_url: str = None) -> dict:
        """
        Run the dynamic agent to achieve a goal.
        
        Args:
            goal: Natural language description of what to do
            start_url: Optional starting URL (extracted from goal if not provided)
            
        Returns:
            dict with success status, steps taken, and screenshots
        """
        print(f"\n{'='*60}")
        print(f"🤖 Dynamic Agent Starting")
        print(f"{'='*60}")
        print(f"Goal: {goal}")
        
        # Extract URL from goal if not provided
        if not start_url:
            start_url = self._extract_url_from_goal(goal)
        
        print(f"URL: {start_url}\n")
        
        steps_completed = []
        screenshots = []
        
        with sync_playwright() as p:
            # Launch browser with stealth
            browser = p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--window-size=1920,1080',
                ]
            )
            
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                locale="en-IN",
                timezone_id="Asia/Kolkata",
                geolocation={"latitude": 19.0760, "longitude": 72.8777},
                permissions=["geolocation"],
            )
            
            page = context.new_page()
            
            # Apply stealth
            stealth = Stealth()
            stealth.apply_stealth_sync(page)
            print("✓ Stealth mode activated\n")
            
            try:
                # Navigate to start URL
                print(f"→ Navigating to {start_url}...")
                page.goto(start_url, wait_until="domcontentloaded", timeout=60000)
                random_delay(2000, 3000)
                move_mouse_randomly(page)
                
                screenshot_path = f"dynamic_step_0_start.png"
                page.screenshot(path=screenshot_path)
                screenshots.append(screenshot_path)
                print(f"✓ Page loaded, screenshot: {screenshot_path}\n")
                
                # Think-Act Loop
                for step_num in range(1, self.max_steps + 1):
                    print(f"{'─'*40}")
                    print(f"Step {step_num}/{self.max_steps}")
                    print(f"{'─'*40}")
                    
                    # Extract current page elements
                    elements = extract_elements(page)
                    print(f"📊 Found {len(elements)} interactive elements")
                    
                    # Add a delay here to respect Gemini Free Tier rate limits (RPM)
                    if step_num > 1:
                        print(f"   ⏳ Rate limit cooldown (5s)...")
                        time.sleep(5)

                    # Ask LLM for next action (with retries)
                    action = None
                    for retry in range(self.action_retries):
                        try:
                            action = self._get_next_action(
                                goal, page.url, steps_completed, elements
                            )
                            break
                        except Exception as e:
                            print(f"   ⚠ LLM error (attempt {retry+1}/{self.action_retries}): {e}")
                            if retry < self.action_retries - 1:
                                time.sleep(2)
                    
                    if not action:
                        print("   ✗ Failed to get action from LLM")
                        continue
                    
                    print(f"💭 Thought: {action.get('thought', 'N/A')}")
                    print(f"🎯 Action: {action.get('action')} → {action.get('selector', action.get('text', action.get('key', '')))}")
                    
                    # Check if done
                    if action.get("done") or action.get("action") == "done":
                        print("\n✅ Goal achieved!")
                        screenshot_path = f"dynamic_step_{step_num}_done.png"
                        page.screenshot(path=screenshot_path)
                        screenshots.append(screenshot_path)
                        
                        return {
                            "success": True,
                            "steps": steps_completed,
                            "screenshots": screenshots,
                            "final_url": page.url
                        }
                    
                    if action.get("action") == "fail":
                        print(f"\n❌ Agent gave up: {action.get('thought')}")
                        return {
                            "success": False,
                            "error": action.get("thought"),
                            "steps": steps_completed,
                            "screenshots": screenshots
                        }
                    
                    # Execute action (with retries)
                    success = False
                    for retry in range(self.action_retries):
                        try:
                            self._execute_action(page, action)
                            success = True
                            break
                        except Exception as e:
                            print(f"   ⚠ Action failed (attempt {retry+1}/{self.action_retries}): {e}")
                            if retry < self.action_retries - 1:
                                random_delay(1000, 2000)
                    
                    if success:
                        step_desc = f"{action.get('action')}: {action.get('selector', action.get('text', ''))}"
                        steps_completed.append(step_desc)
                        print(f"   ✓ Action completed")
                        
                        # Screenshot
                        screenshot_path = f"dynamic_step_{step_num}.png"
                        page.screenshot(path=screenshot_path)
                        screenshots.append(screenshot_path)
                    else:
                        print(f"   ✗ Action failed after {self.action_retries} retries")
                    
                    print()
                
                # Max steps reached
                print(f"\n⚠ Max steps ({self.max_steps}) reached")
                return {
                    "success": False,
                    "error": "Max steps reached",
                    "steps": steps_completed,
                    "screenshots": screenshots
                }
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                page.screenshot(path="dynamic_error.png")
                return {
                    "success": False,
                    "error": str(e),
                    "steps": steps_completed,
                    "screenshots": ["dynamic_error.png"]
                }
            finally:
                random_delay(1000, 2000)
                browser.close()
                print("\n🔒 Browser closed")
    
    def _extract_url_from_goal(self, goal: str) -> str:
        """Extract URL from goal description."""
        goal_lower = goal.lower()
        
        if "bookmyshow" in goal_lower or "book my show" in goal_lower:
            return "https://in.bookmyshow.com"
        elif "google" in goal_lower:
            return "https://www.google.com"
        elif "wikipedia" in goal_lower:
            return "https://en.wikipedia.org"
        elif "imdb" in goal_lower:
            return "https://www.imdb.com"
        else:
            # Try to find URL in goal
            url_match = re.search(r'https?://[^\s]+', goal)
            if url_match:
                return url_match.group()
            return "https://www.google.com"
    
    def _get_next_action(
        self, 
        goal: str, 
        current_url: str, 
        steps_completed: List[str], 
        elements: List[Dict]
    ) -> dict:
        """Ask LLM for the next action based on current page state."""
        prompt = DYNAMIC_AGENT_PROMPT.format(
            goal=goal,
            url=current_url,
            steps_completed=", ".join(steps_completed) if steps_completed else "(none yet)",
            elements=format_elements_for_prompt(elements)
        )
        
        response = self.model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Parse JSON
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        return json.loads(response_text.strip())
    
    def _execute_action(self, page: Page, action: dict):
        """Execute a single action on the page."""
        action_type = action.get("action")
        
        if action_type == "click":
            selector = action.get("selector", "")
            element = page.locator(selector).first
            
            try:
                element.hover(timeout=3000)
                random_delay(200, 500)
                element.click(force=True)
            except Exception as e:
                if "intercepts pointer events" in str(e):
                    print("   ⚠ Click intercepted! Attempting to close popups (Escape key)...")
                    page.keyboard.press("Escape")
                    random_delay(1000, 2000)
                    # Try clicking again without hover
                    element.click(force=True)
                else:
                    raise e
            random_delay(2000, 3000)
        
        elif action_type == "type":
            selector = action.get("selector", "")
            text = action.get("text", "")
            element = page.locator(selector).first
            element.click()
            random_delay(200, 400)
            element.fill("")
            random_delay(100, 200)
            # Type character by character
            for char in text:
                page.keyboard.type(char)
                random_delay(40, 150)
            random_delay(3000, 4000)  # Wait for autocomplete
        
        elif action_type == "press":
            key = action.get("key", "Enter")
            page.keyboard.press(key)
            random_delay(1000, 2000)
        
        elif action_type == "goto":
            url = action.get("url", "")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            random_delay(2000, 3000)
        
        elif action_type == "wait":
            seconds = action.get("seconds", 2)
            time.sleep(min(seconds, 5))
        
        else:
            raise ValueError(f"Unknown action: {action_type}")


def main():
    """CLI for dynamic agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dynamic Playwright Agent")
    parser.add_argument("--goal", "-g", required=True, help="Goal to achieve")
    parser.add_argument("--url", "-u", help="Starting URL (optional)")
    
    args = parser.parse_args()
    
    agent = DynamicAgent()
    result = agent.run(args.goal, args.url)
    
    print(f"\n{'='*60}")
    if result["success"]:
        print("✅ SUCCESS!")
        print(f"Steps taken: {len(result['steps'])}")
    else:
        print("❌ FAILED")
        print(f"Error: {result.get('error')}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
