"""
Configuration for AI Script Generator
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"

# Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

# Execution Configuration
EXECUTION_TIMEOUT_SECONDS = 60
HEADLESS_MODE = False

# Sandbox Configuration
ALLOWED_DOMAINS = [
    "*"  # Allow all domains by default, can restrict as needed
]
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
SCREENSHOTS_DIR = os.path.join(OUTPUT_DIR, "screenshots")

# Create directories if they don't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
