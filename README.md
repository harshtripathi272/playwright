# Playwright Web Automation Scripts

Python-based web automation scripts using Playwright for element extraction and self-correcting element matching.

## 📋 Assignment Overview

This project demonstrates:
1. **Script 1**: Navigate to a website, search for content, and extract all page elements
2. **Script 2A**: Find elements using fuzzy string matching (auto-corrects misspelled element names)
3. **Script 2B**: Find elements using AI intent understanding (Gemini API)

## 🚀 Quick Start

### 1. Setup

```powershell
# Navigate to project directory
cd d:\Workspace\playwright

# Activate virtual environment
.\venv\Scripts\activate

# Install Playwright browsers (first time only)
playwright install chromium
```

### 2. Run the Interactive Demo

```powershell
python run_demo.py
```

### 3. Run Individual Scripts

#### Element Extractor (Script 1)
```powershell
# Basic usage - Wikipedia
python scripts/element_extractor.py --url "https://en.wikipedia.org" --search "Python programming"

# BookMyShow example
python scripts/element_extractor.py --url "https://in.bookmyshow.com" --search "Border 2"
```

#### Fuzzy Matcher (Script 2A - Self-Correcting)
```powershell
# Try with misspelled element name
python scripts/fuzzy_matcher.py --url "https://en.wikipedia.org" --find "reed articel"

# With click action
python scripts/fuzzy_matcher.py --url "https://en.wikipedia.org" --find "serch" --click
```

#### AI Matcher (Script 2B - Self-Correcting)
```powershell
# Without API key (falls back to fuzzy matching)
python scripts/ai_matcher.py --url "https://en.wikipedia.org" --intent "I want to search for something"

# With Gemini API key
python scripts/ai_matcher.py --url "https://en.wikipedia.org" --intent "I want to read an article" --api-key YOUR_API_KEY
```

## 📁 Project Structure

```
playwright/
├── scripts/
│   ├── element_extractor.py   # Script 1: Search & extract elements
│   ├── fuzzy_matcher.py       # Script 2A: Fuzzy string matching
│   └── ai_matcher.py          # Script 2B: AI-based matching
├── utils/
│   └── helpers.py             # Common utility functions
├── venv/                      # Python virtual environment
├── requirements.txt           # Python dependencies
├── run_demo.py               # Interactive demo script
└── README.md                 # This file
```

## 🎯 How the Self-Correcting Scripts Work

### Fuzzy Matcher
Uses **string similarity algorithms** to find the closest matching element:
- `"book home"` → finds `"Book Tickets"` 
- `"serch"` → finds `"Search"`
- `"reed articel"` → finds `"Read article"`

### AI Matcher
Uses **Gemini AI** to understand your intent:
- `"I want to book movie tickets"` → finds the booking button
- `"show me the trailer"` → finds the play/trailer button
- `"I want to search for something"` → finds the search input

## 🔑 Gemini API Key (Optional)

To use the AI-based matcher with full capabilities:

1. Get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set as environment variable:
   ```powershell
   $env:GEMINI_API_KEY = "your-api-key-here"
   ```
3. Or pass directly:
   ```powershell
   python scripts/ai_matcher.py --api-key YOUR_KEY --intent "..."
   ```

## 📚 Dependencies

- `playwright` - Browser automation
- `rapidfuzz` - Fuzzy string matching
- `google-generativeai` - Gemini AI (optional)
- `rich` - Beautiful console output

## 🎬 Examples

### Example 1: Extract elements from Wikipedia search results
```powershell
python scripts/element_extractor.py --url "https://en.wikipedia.org" --search "Artificial Intelligence"
```

### Example 2: Find misspelled button
```powershell
python scripts/fuzzy_matcher.py --url "https://example.com" --find "sbmit buton" --click
```

### Example 3: Natural language element finding
```powershell
python scripts/ai_matcher.py --intent "I want to log into my account" --click
```

---

Created for internship assignment - Playwright Web Automation
