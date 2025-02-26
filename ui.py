"""
File: ui.py
Purpose: Generates inline keyboards and messages for the Family Task Bot.
Dependencies: python-telegram-bot>=21.0
Last Modified: 2024-11-01
"""

try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
except ImportError:
    raise ImportError(
        "Could not import telegram module. "
        "Please install it using 'pip install python-telegram-bot>=21.0'"
    )
from config import TASK_TYPES

class UI:
    def __init__(self):
        self.days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def main_menu(self):
        """Generate the main menu keyboard."""
        buttons = [
            [InlineKeyboardButton("Add Task", callback_data="add_task")],
            [InlineKeyboardButton("View My Tasks", callback_data="view_my"),
             InlineKeyboardButton("View Others", callback_data="view_others")],
            [InlineKeyboardButton("Users", callback_data="users"),
             InlineKeyboardButton("View History", callback_data="history")]
        ]
        return InlineKeyboardMarkup(buttons)

    def task_types(self):
        """Generate keyboard for selecting task type."""
        buttons = [
            [InlineKeyboardButton(TASK_TYPES["one-time"], callback_data="type_one"),
             InlineKeyboardButton(TASK_TYPES["recurring"], callback_data="type_recurring")],
            [InlineKeyboardButton(TASK_TYPES["daily"], callback_data="type_daily")],
            [InlineKeyboardButton("Cancel", callback_data="cancel")]
        ]
        return InlineKeyboardMarkup(buttons)

    def days_selection(self, selected_days=None):
        """Generate multi-select keyboard for recurring task days."""
        if selected_days is None:
            selected_days = []
        buttons = []
        for day in self.days:
            label = f"{day} ✓" if day in selected_days else day
            callback = f"day_{day.lower()}"
            buttons.append([InlineKeyboardButton(label, callback_data=callback)])
        buttons.append([InlineKeyboardButton("Done", callback_data="days_done"),
                       InlineKeyboardButton("Cancel", callback_data="cancel")])
        return InlineKeyboardMarkup(buttons)

    def task_actions(self, task_id):
        """Generate actions for a specific task."""
        buttons = [
            [InlineKeyboardButton("Complete", callback_data=f"complete_{task_id}"),
             InlineKeyboardButton("Edit", callback_data=f"edit_{task_id}")],
            [InlineKeyboardButton("Nudge", callback_data=f"nudge_{task_id}"),
             InlineKeyboardButton("Delete", callback_data=f"delete_{task_id}")],
            [InlineKeyboardButton("Back", callback_data="back")]
        ]
        return InlineKeyboardMarkup(buttons)

    def edit_options(self, task_id):
        """Generate options for editing a task."""
        buttons = [
            [InlineKeyboardButton("Title", callback_data=f"edit_title_{task_id}"),
             InlineKeyboardButton("Time", callback_data=f"edit_time_{task_id}")],
            [InlineKeyboardButton("Date/Days", callback_data=f"edit_date_{task_id}"),
             InlineKeyboardButton("Cancel", callback_data="cancel")]
        ]
        return InlineKeyboardMarkup(buttons)

    def user_management(self):
        """Generate user management keyboard."""
        buttons = [
            [InlineKeyboardButton("Add User", callback_data="add_user"),
             InlineKeyboardButton("Edit User", callback_data="edit_user")],
            [InlineKeyboardButton("Delete User", callback_data="delete_user"),
             InlineKeyboardButton("Back", callback_data="back")]
        ]
        return InlineKeyboardMarkup(buttons)

    def task_list(self, tasks, prefix):
        """Generate a list of tasks with buttons."""
        if not tasks:
            return None
        buttons = [
            [InlineKeyboardButton(task["title"], callback_data=f"{prefix}_{task['id']}")]
            for task in tasks
        ]
        buttons.append([InlineKeyboardButton("Back", callback_data="back")])
        return InlineKeyboardMarkup(buttons)

    def history_list(self, history):
        """Generate a formatted history message."""
        if not history:
            return "No history available."
        lines = []
        for entry in sorted(history, key=lambda x: x["timestamp"], reverse=True):
            status = entry["status"].capitalize()
            time = entry["timestamp"]
            user = entry["user"]
            title = entry["title"]
            lines.append(f"{status}: {title} by {user} at {time}")
        return "\n".join(lines) or "No history available."

    def reminder_message(self, tasks):
        """Generate a concise reminder message with due tasks."""
        if not tasks:
            return "No tasks due today!"
        lines = ["Tasks due:"]
        for task in tasks:
            lines.append(f"- {task['time']} {task['title']}")
        return "\n".join(lines)

    def error_message(self, error):
        """Generate an error message with a back button."""
        buttons = [[InlineKeyboardButton("Back", callback_data="back")]]
        return f"Error: {error}", InlineKeyboardMarkup(buttons)