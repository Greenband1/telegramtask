"""
File: config.py
Purpose: Configuration settings and constants for the Family Task Bot.
Dependencies: python-dotenv==1.0.1
Last Modified: 2024-11-01
"""

import os
try:
    from dotenv import load_dotenv
except ImportError:
    raise ImportError(
        "Could not import dotenv module. "
        "Please install it using 'pip install python-dotenv==1.0.1'"
    )

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Token (loaded from .env)
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file.")

# File paths for JSON storage
TASKS_FILE = "tasks.json"
HISTORY_FILE = "history.json"

# Constants for task types
TASK_TYPES = {
    "one-time": "One-time",
    "recurring": "Recurring",
    "daily": "Daily"
}

# Valid days for recurring tasks
VALID_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Time for daily reminders (7 AM)
REMINDER_TIME = "07:00"

# History retention period (14 days)
HISTORY_RETENTION_DAYS = 14

# Timezone assumption (single time zone for this version)
TIMEZONE = "America/Chicago"