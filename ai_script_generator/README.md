# AI-Powered Playwright Script Generator

An intelligent system that automatically generates and executes Playwright automation scripts from multimodal inputs (text, images, or videos).

## Features

- 🤖 **AI-Powered Generation**: Uses Google Gemini to interpret inputs and generate scripts
- 📷 **Multimodal Input**: Accepts text descriptions, screenshots, or video recordings
- ✅ **Pre-Execution Validation**: AST parsing and security checks before running
- 🔄 **Smart Retry**: Up to 3 attempts with rich error context feedback
- 🛡️ **Sandboxed Execution**: Safe subprocess execution with timeouts
- 📸 **Screenshot Capture**: Automatically captures screenshots during execution

## Usage

```bash
# Text input
python main.py --text "Go to google.com and search for weather"

# Image input (screenshot of UI)
python main.py --image screenshot.png

# Video input (screen recording)
python main.py --video recording.mp4
```

## Requirements

```bash
pip install -r requirements.txt
playwright install chromium
```

## Environment Variables

Create a `.env` file in the `ai_script_generator` folder or the project root:

```env
GEMINI_API_KEY=your_api_key_here
```

## Architecture

```
ai_script_generator/
├── main.py           # Entry point & orchestrator
├── input_processor.py # Handles text/image/video inputs
├── agent.py          # LLM-powered script generation
├── validator.py      # Pre-execution validation
├── executor.py       # Sandboxed script execution
├── context_manager.py # Retry context tracking
└── config.py         # Configuration settings
```

## How It Works

1. **Input Processing**: Converts text/image/video into structured prompts
2. **Script Generation**: LLM generates Playwright Python script
3. **Validation**: Checks syntax and security before execution
4. **Execution**: Runs script in isolated subprocess with timeout
5. **Retry**: On failure, captures context and refines script (up to 3x)
