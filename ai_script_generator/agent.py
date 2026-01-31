"""
Playwright Agent - LLM-powered script generation
Uses Gemini to generate Playwright scripts from processed inputs

PATTERNS EXTRACTED FROM WORKING SCRIPTS:
- bookmyshow_stealth.py: Human-like typing, mouse movements, stealth mode
- ai_matcher.py: AI element matching, fuzzy fallback
- fuzzy_matcher.py: RapidFuzz matching algorithms
"""
import json
import re
from typing import Optional
import google.generativeai as genai

from config import GEMINI_API_KEY, MODEL_NAME


# Complete system prompt with ALL patterns from working scripts
SYSTEM_PROMPT = """You are an expert Playwright automation engineer. Generate complete, working Python scripts.

=== COMPLETE WORKING SCRIPT TEMPLATE ===

Use this EXACT structure for all generated scripts:

```python
import time
import random
from playwright.sync_api import sync_playwright
from playwright_stealth.stealth import Stealth  # CRITICAL: Anti-bot detection

def random_delay(min_ms=100, max_ms=500):
    \"\"\"Add random delay to mimic human behavior.\"\"\"
    time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

def human_type(page, text: str):
    \"\"\"Type like a human with random delays and occasional typos.\"\"\"
    for i, char in enumerate(text):
        # 5% chance to make a typo
        if random.random() < 0.05 and i < len(text) - 1:
            wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
            page.keyboard.type(wrong_char)
            random_delay(150, 400)
            page.keyboard.press("Backspace")
            random_delay(200, 500)
        
        page.keyboard.type(char)
        if char == " ":
            random_delay(150, 400)
        else:
            random_delay(40, 200)

def move_mouse_randomly(page):
    \"\"\"Move mouse to random positions like a human.\"\"\"
    for _ in range(3):
        x = random.randint(100, 800)
        y = random.randint(100, 500)
        page.mouse.move(x, y)
        random_delay(100, 300)

def main():
    with sync_playwright() as p:
        # Launch with anti-detection settings
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-infobars',
                '--disable-extensions',
                '--disable-gpu',
                '--window-size=1920,1080',
            ]
        )
        
        # Create context with realistic settings (Indian locale for BookMyShow)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            geolocation={"latitude": 19.0760, "longitude": 72.8777},  # Mumbai
            permissions=["geolocation"],
            extra_http_headers={
                "Accept-Language": "en-IN,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            }
        )
        
        page = context.new_page()
        
        # CRITICAL: Apply stealth mode to hide automation signatures
        stealth = Stealth()
        stealth.apply_stealth_sync(page)
        print("Stealth mode activated!")
        
        try:
            # Step 1: Navigate
            random_delay(500, 1000)
            page.goto("https://example.com", wait_until="domcontentloaded", timeout=60000)
            random_delay(2000, 3000)
            move_mouse_randomly(page)
            
            # Step 2: Your automation here...
            # ALWAYS use try/except for element interactions
            # ALWAYS add random_delay() between actions
            # ALWAYS hover() before click()
            
            print("Automation completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="error.png")
        finally:
            random_delay(1000, 2000)
            browser.close()
            print("Browser closed.")

if __name__ == "__main__":
    main()
```

=== CRITICAL PATTERNS (MUST FOLLOW) ===

1. FINDING SEARCH INPUT - Try multiple selectors:
```python
search_selectors = [
    "input[placeholder*='Search']",
    "input[type='search']",
    "input[type='text']",
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

# Fallback: click on search text first
if not search_input:
    try:
        page.locator("text=Search").first.click()
        random_delay(500, 1000)
        search_input = page.locator("input:visible").first
    except:
        pass
```

2. CLICKING ELEMENTS - Always hover first:
```python
try:
    element = page.locator("text=Mumbai").first
    if element.is_visible(timeout=5000):
        element.hover()
        random_delay(200, 500)
        element.click()
        random_delay(2000, 3000)
except Exception as e:
    print(f"Click failed: {e}")
```

3. TYPING IN INPUTS:
```python
search_input.hover()
random_delay(200, 400)
search_input.click()
random_delay(300, 600)
search_input.fill("")  # Clear first
random_delay(200, 400)

# Use human_type for natural typing
human_type(page, "Border 2")
random_delay(3000, 4000)  # Wait for dropdown
```

4. HANDLING CITY/POPUP - With graceful fallback:
```python
try:
    city_button = page.locator("text=Mumbai").first
    if city_button.is_visible(timeout=5000):
        city_button.hover()
        random_delay(200, 500)
        city_button.click()
        print("City selected: Mumbai")
        random_delay(2000, 3000)
except Exception as e:
    print(f"City selection skipped: {e}")
```

5. CLICKING DROPDOWN RESULTS:
```python
# Wait for dropdown
random_delay(3000, 4000)

# Find and click best match
items = page.locator("li, a, div[role='option']").all()
for item in items:
    try:
        if not item.is_visible():
            continue
        text = item.inner_text().strip()
        if "Border 2" in text or "border" in text.lower():
            item.scroll_into_view_if_needed()
            item.hover(timeout=2000)
            random_delay(300, 800)
            item.click(force=True)
            print(f"Clicked: {text}")
            break
    except:
        continue
```

6. FORCE CLICK WITH HREF FALLBACK:
```python
try:
    element.click(force=True)
except Exception as e:
    print(f"Click failed: {e}, trying href...")
    href = element.get_attribute("href")
    if href:
        url = href if href.startswith("http") else "https://site.com" + href
        page.goto(url, wait_until="domcontentloaded")
```

7. SCREENSHOTS AT KEY STEPS:
```python
page.screenshot(path="step1_homepage.png")
print("Screenshot saved: step1_homepage.png")
```

=== FORBIDDEN PATTERNS (NEVER USE) ===

❌ NEVER: browser.new_new_page() → ✅ USE: context.new_page()
❌ NEVER: CSS with | pipe → ✅ USE: XPath for OR, or separate locators
❌ NEVER: except expect.TimeoutError → ✅ USE: except Exception as e:
❌ NEVER: page.wait_for_load_state("networkidle") → ✅ USE: "domcontentloaded"
❌ NEVER: time.sleep(5) without randomness → ✅ USE: random_delay(4000, 6000)
❌ NEVER: Skip stealth mode → ✅ ALWAYS apply stealth!

=== ⚠️ MANDATORY REQUIREMENTS (MUST INCLUDE IN EVERY SCRIPT) ===

Your script MUST include ALL of these or it will be REJECTED:

1. Import: `from playwright_stealth.stealth import Stealth`
2. After creating page: `stealth = Stealth(); stealth.apply_stealth_sync(page)`
3. Helper functions: random_delay(), human_type(), move_mouse_randomly()
4. Geolocation in context: geolocation={"latitude": 19.0760, "longitude": 72.8777}
5. Extra HTTP headers with Accept-Language and Sec-Fetch headers

Without stealth mode, BookMyShow will detect the bot and show "No results found"!

=== OUTPUT FORMAT ===
Respond with JSON:
{
  "steps": ["Step 1: Navigate to site", "Step 2: Select city", ...],
  "script": "complete python code WITH STEALTH MODE",
  "expected_outcome": "what happens on success"
}

The script must use sync_playwright (NOT async), be complete, and runnable.
Include playwright_stealth, helper functions, and all anti-detection code in EVERY script.
"""


class PlaywrightAgent:
    """LLM Agent for generating Playwright scripts"""
    
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set in environment")
        
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(MODEL_NAME)
    
    def generate_script(self, processed_input: dict, retry_context: Optional[dict] = None) -> dict:
        """
        Generate a Playwright script from processed input
        
        Args:
            processed_input: Output from InputProcessor
            retry_context: Optional context from previous failed attempts
            
        Returns:
            dict with 'steps', 'script', and 'expected_outcome'
        """
        prompt = self._build_prompt(processed_input, retry_context)
        
        # Handle different input types
        if processed_input["type"] == "image":
            response = self._generate_with_image(prompt, processed_input)
        elif processed_input["type"] == "video":
            response = self._generate_with_video(prompt, processed_input)
        else:
            response = self._generate_text_only(prompt)
        
        return self._parse_response(response)
    
    def _build_prompt(self, processed_input: dict, retry_context: Optional[dict]) -> str:
        """Build the complete prompt for the LLM"""
        parts = [SYSTEM_PROMPT, "\n\n"]
        
        # Add the input-specific prompt
        parts.append(f"TASK:\n{processed_input['prompt']}\n\n")
        
        # Add retry context if this is a retry attempt
        if retry_context:
            parts.append(self._build_retry_context(retry_context))
        
        return "".join(parts)
    
    def _build_retry_context(self, context: dict) -> str:
        """Build retry context section for the prompt"""
        lines = [
            "\n=== PREVIOUS ATTEMPT FAILED - FIX THESE ISSUES ===",
            f"Attempt #{context.get('attempt_number', 1)} failed.",
            f"Error: {context.get('error_message', 'Unknown error')}",
            "",
            "COMMON FIXES:",
            "1. 'new_new_page' → Use context.new_page()",
            "2. CSS '|' error → Use XPath or separate locators with try/except",
            "3. TimeoutError → Use except Exception as e:",
            "4. Element not found → Add more fallback selectors",
            "5. Click failed → Use force=True or href fallback",
            "6. Timeout → Use domcontentloaded not networkidle",
            "7. Add more random_delay() between actions",
        ]
        
        if context.get('failed_step'):
            step = context['failed_step']
            lines.append(f"\nFailed at: Step {step.get('step_number')}: {step.get('description')}")
        
        if context.get('completed_steps'):
            lines.append(f"Completed: {', '.join(context['completed_steps'])}")
        
        if context.get('current_url'):
            lines.append(f"Last URL: {context['current_url']}")
            
        if context.get('previous_script'):
            # Show the problematic line from previous script
            error_msg = context.get('error_message', '')
            lines.append(f"\nFix the specific error: {error_msg[:200]}")
        
        lines.append("\n=== GENERATE A FIXED SCRIPT ===\n")
        
        return "\n".join(lines)
    
    def _generate_text_only(self, prompt: str) -> str:
        """Generate response for text-only input"""
        response = self.model.generate_content(prompt)
        return response.text
    
    def _generate_with_image(self, prompt: str, processed_input: dict) -> str:
        """Generate response with image input"""
        import base64
        
        image_data = base64.b64decode(processed_input["content"])
        
        image_part = {
            "mime_type": processed_input.get("mime_type", "image/png"),
            "data": image_data
        }
        
        response = self.model.generate_content([prompt, image_part])
        return response.text
    
    def _generate_with_video(self, prompt: str, processed_input: dict) -> str:
        """Generate response with video frames"""
        import base64
        
        parts = [prompt]
        
        for i, frame_b64 in enumerate(processed_input["content"][:5]):
            frame_data = base64.b64decode(frame_b64)
            parts.append({
                "mime_type": "image/jpeg",
                "data": frame_data
            })
        
        response = self.model.generate_content(parts)
        return response.text
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse LLM response into structured format"""
        # Try to extract JSON from response
        try:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
                
                if "script" in result:
                    return {
                        "steps": result.get("steps", []),
                        "script": result["script"],
                        "expected_outcome": result.get("expected_outcome", "")
                    }
        except json.JSONDecodeError:
            pass
        
        # Fallback: extract code block
        code_match = re.search(r'```python\n([\s\S]*?)```', response_text)
        if code_match:
            return {
                "steps": ["Execute automation script"],
                "script": code_match.group(1),
                "expected_outcome": "Automation completes successfully"
            }
        
        # Last resort
        if "def " in response_text or "from playwright" in response_text:
            # Try to clean up the response
            lines = response_text.split('\n')
            code_lines = []
            in_code = False
            for line in lines:
                if 'import' in line or 'def ' in line or 'from playwright' in line:
                    in_code = True
                if in_code:
                    code_lines.append(line)
            
            if code_lines:
                return {
                    "steps": ["Execute automation script"],
                    "script": '\n'.join(code_lines),
                    "expected_outcome": "Automation completes successfully"
                }
        
        raise ValueError("Could not parse valid script from LLM response")
