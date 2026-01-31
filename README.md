# Intelligent Playwright Automation

A robust, stealthy, and self-correcting web automation agent built with **Playwright** and **Google Gemini AI**.
This project mimics human behavior to bypass anti-bot protections on sites like **BookMyShow** and uses AI to understand user intent (e.g., mapping "book home" to the "Book Tickets" button).

---

## Key Features

### 1. **Advanced Stealth Mode**
*   **Bypasses Bot Detection**: Uses `playwright-stealth` to mask automation signals (`navigator.webdriver`, headers).
*   **Human-Like Interaction**:
    *   **Typing**: Simulates variable typing speeds, typos (5% chance), and backspace corrections.
    *   **Mouse**: Random mouse jitters and reaction delays.
    *   **Fail-Safe Navigation**: If a click is blocked (e.g., hidden element), it intelligently extracts the link and navigates directly.

### 2. **AI Intent Understanding** (Gemini)
*   Instead of fragile selectors (`#btn-123`), the agent looks at the page and understands **meaning**.
*   **Example**: Command `"I want to buy seats"` -> Agent finds and clicks the **"Book Tickets"** button.

### 3. **Fuzzy Matching Fallback**
*   Works even without an AI key!
*   Uses `rapidfuzz` to find elements based on string similarity (e.g., "book tckets" finds "Book Tickets").

---

## Project Structure

| File | Description |
| :--- | :--- |
| **`scripts/bookmyshow_stealth.py`** | **The Main Engine.** Integrates stealth, automation, and decision-making logic. |
| **`scripts/ai_matcher.py`** | **The Brain.** Uses Gemini API to analyze page elements and find the best match for a user's intent. |
| **`scripts/fuzzy_matcher.py`** | **The Backup.** Finds elements using fuzzy string matching when AI is unavailable. |
| **`scripts/element_extractor.py`** | **The Eyes.** Scrapes interactive elements (buttons, links) from any page. |
| **`utils/helpers.py`** | **The Toolbox.** Shared functions for element extraction and selector logic. |

---

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd playwright-automation
    ```

2.  **Set up Virtual Environment**:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    source venv/bin/activate # Mac/Linux
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```

4.  **Set up Environment Variables** (Optional, for AI features):
    Create a `.env` file:
    ```env
    GOOGLE_API_KEY=your_gemini_api_key_here
    ```

---

## Usage

### 1. Run Stealth Mode (BookMyShow)
Navigate to a movie flow with human-like behavior.

```bash
# Basic Usage
python scripts/bookmyshow_stealth.py --movie "Border 2" --city "Mumbai"
```

### 2. Run with AI/Smart Intent
Tell the script what to do in plain English.

**With AI (Requires API Key):**
```bash
python scripts/bookmyshow_stealth.py --movie "Border 2" --city "Mumbai" --find "book home"
# Result: AI understands "book home" contextually means "Book Tickets" and clicks it.
```

**With Fuzzy Match (No API Key):**
```bash
python scripts/bookmyshow_stealth.py --movie "Border 2" --city "Mumbai" --find "book ticets"
# Result: Finds "Book Tickets" based on spelling similarity.
```

---

## Requirements
*   Python 3.8+
*   `playwright`
*   `playwright-stealth`
*   `google-generativeai`
*   `rapidfuzz`
*   `rich` (for beautiful console output)
