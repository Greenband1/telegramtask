"""
File: ui.py
Purpose: Generates inline keyboards and messages for the Family Task Bot.
Dependencies: python-telegram-bot>=21.0
Last Modified: 2025-03-01
"""

from datetime import datetime
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
except ImportError:
    raise ImportError(
        "Could not import telegram module. "
        "Please install it using 'pip install python-telegram-bot>=21.0'"
    )
from config import TASK_TYPES
import logging

logger = logging.getLogger(__name__)

class UI:
    def __init__(self):
        self.days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.history_page_size = 10  # Number of history entries per page

    def main_menu(self, users=None):
        """Generate the main menu keyboard with user-specific buttons, without Add Task."""
        if users is None:
            users = []
        buttons = [
            [InlineKeyboardButton("My Tasks", callback_data="view_my"),
             InlineKeyboardButton("View Others", callback_data="view_others")],
            [InlineKeyboardButton("All Tasks", callback_data="view_all")],
            [InlineKeyboardButton("Users", callback_data="users"),
             InlineKeyboardButton("History", callback_data="history_0")],
        ]
        # Add buttons for the first 4 users, sorted alphabetically
        user_buttons = [
            InlineKeyboardButton(f"@{user}", callback_data=f"view_user_tasks_{user}")
            for user in sorted(users)[:4]
        ]
        # Arrange user buttons in rows of three
        for i in range(0, len(user_buttons), 3):
            buttons.append(user_buttons[i:i+3])
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

    def date_selection(self):
        """Generate keyboard for selecting a one-time task due date."""
        buttons = [
            [InlineKeyboardButton("Today", callback_data="date_0"),
             InlineKeyboardButton("+1 Day", callback_data="date_1")],
            [InlineKeyboardButton("+2 Days", callback_data="date_2"),
             InlineKeyboardButton("+3 Days", callback_data="date_3")],
            [InlineKeyboardButton("+1 Week", callback_data="date_7"),
             InlineKeyboardButton("+2 Weeks", callback_data="date_14")],
            [InlineKeyboardButton("+1 Month", callback_data="date_30"),
             InlineKeyboardButton("Cancel", callback_data="cancel")]
        ]
        return InlineKeyboardMarkup(buttons)

    def task_actions(self, task_id, is_owner=True):
        """Generate actions for a specific task, differing based on ownership."""
        if is_owner:
            buttons = [
                [InlineKeyboardButton("Complete", callback_data=f"complete_{task_id}"),
                 InlineKeyboardButton("Edit", callback_data=f"edit_{task_id}")],
                [InlineKeyboardButton("Delete", callback_data=f"delete_{task_id}")],
                [InlineKeyboardButton("Back", callback_data="back")]
            ]
        else:
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
             InlineKeyboardButton("Back to Main Menu", callback_data="back")]
        ]
        return InlineKeyboardMarkup(buttons)

    def task_list(self, tasks, prefix, username=None):
        """Generate a list of tasks with buttons, showing type and due date/days, with Add Task for own tasks."""
        if not tasks and username:  # If viewing someone else's tasks with no tasks, no Add Task button
            return None
        buttons = []
        today = datetime.now().date()
        for task in tasks:
            title = task["title"]
            task_type = task.get("type", "daily")
            if task_type == "one-time":
                due_date = task.get("date", "No date")
                if due_date == "No date":
                    label = f"{title}"
                else:
                    try:
                        due_date_dt = datetime.strptime(due_date, "%Y-%m-%d").date()
                        label = f"{title} ({due_date_dt.strftime('%b %d')})"
                    except ValueError:
                        label = f"{title}"
            elif task_type == "recurring":
                days = ",".join(task.get("days", []))
                label = f"{title} ({days})"
            else:  # daily
                label = f"{title} (Daily)"
            if username:
                label += f" (@{username})"
            buttons.append([InlineKeyboardButton(label, callback_data=f"{prefix}_{task['id']}")])
        # Add "Add Task" button only for own tasks (when username is None)
        if not username:
            buttons.append([InlineKeyboardButton("Add Task", callback_data="add_task")])
        buttons.append([InlineKeyboardButton("Back to Main Menu", callback_data="back")])
        return InlineKeyboardMarkup(buttons)

    def user_list(self, users):
        """Generate a list of users as buttons for task viewing."""
        if not users:
            return None
        buttons = [
            [InlineKeyboardButton(f"@{user}", callback_data=f"view_user_{user}")]
            for user in users
        ]
        buttons.append([InlineKeyboardButton("Back to Main Menu", callback_data="back")])
        return InlineKeyboardMarkup(buttons)

    def all_tasks_message_and_keyboard(self, tasks, username=None):
        """Generate message and keyboard for all tasks with number toggle buttons."""
        if not tasks:
            message = f"No tasks due today for @{username}!" if username else "No tasks found!"
            keyboard = [[InlineKeyboardButton("Back to Main Menu", callback_data="back")]]
        else:
            today = datetime.now().date()
            today_str = today.isoformat()
            weekday = today.strftime("%a")
            message = "Click a number to toggle task status:\n"
            task_index = 1
            task_mapping = []
            for user in sorted(set(task.get("owner", username) for task in tasks if "owner" in task or username)):  # Use username as fallback
                user_tasks = [t for t in tasks if t.get("owner", username) == user]
                if user_tasks:
                    message += f"\n**{user}'s Tasks**\n"
                    for task in user_tasks:
                        status = "✅" if today_str in task.get("completions", []) else "❌"  # Check completions for status
                        task_type = task.get("type", "daily")
                        if task_type == "one-time":
                            due_date_str = task.get("date", "No date")
                            if due_date_str != "No date":
                                due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                                completions = task.get("completions", [])
                                completed_on_or_after_due = any(datetime.strptime(c, "%Y-%m-%d").date() >= due_date for c in completions)
                                overdue = "‼ " if due_date < today and not completed_on_or_after_due else ""
                                due_month_day = due_date.strftime("%b %d")
                                extra = f"{overdue}[{due_month_day}]"
                            else:
                                extra = "[No date]"
                        elif task_type == "recurring":
                            days = ",".join(task.get("days", []))
                            extra = f"[{days}]"
                        else:  # daily
                            extra = "[Daily]"
                        message += f"{task_index}. {task['title']} {status} {extra}\n"
                        task_mapping.append((task["id"], task))  # Store task ID and task
                        task_index += 1
            
            buttons = [
                InlineKeyboardButton(str(i + 1), callback_data=f"toggle_{task_id}")
                for i, (task_id, _) in enumerate(task_mapping)
            ]
            keyboard = [buttons[i:i+5] for i in range(0, len(buttons), 5)]
            keyboard.append([InlineKeyboardButton("Back to Main Menu", callback_data="back")])
        return message, InlineKeyboardMarkup(keyboard)

    def history_view(self, history, page=0):
        """Generate message and keyboard for viewing task history."""
        if not history:
            text = "No history available."
            keyboard = [[InlineKeyboardButton("Back to Main Menu", callback_data="back")]]
        else:
            sorted_history = sorted(history, key=lambda x: x["timestamp"], reverse=True)
            total_entries = len(sorted_history)
            start_idx = page * self.history_page_size
            end_idx = min(start_idx + self.history_page_size, total_entries)
            if start_idx >= total_entries:
                start_idx = max(0, total_entries - self.history_page_size)
                end_idx = total_entries
            lines = []
            for entry in sorted_history[start_idx:end_idx]:
                status = entry["status"].capitalize()
                time = entry["timestamp"]
                user = entry["user"]
                title = entry["title"]
                lines.append(f"{status}: {title} by {user} at {time}")
            text = "\n".join(lines) or "No history available."
            if total_entries > self.history_page_size:
                text += f"\n\nPage {page + 1} of {((total_entries - 1) // self.history_page_size) + 1}"
            buttons = []
            if page > 0:
                buttons.append(InlineKeyboardButton("Previous", callback_data=f"history_{page - 1}"))
            if end_idx < total_entries:
                buttons.append(InlineKeyboardButton("Next", callback_data=f"history_{page + 1}"))
            buttons.append(InlineKeyboardButton("Back to Main Menu", callback_data="back"))
            keyboard = [buttons] if len(buttons) <= 3 else [buttons[:2], buttons[2:]]
        return text, InlineKeyboardMarkup(keyboard)

    def reminder_message(self, tasks):
        """Generate a concise reminder message with due tasks."""
        if not tasks:
            return "No tasks need action today!"
        today = datetime.now().date().isoformat()
        lines = ["Tasks needing action:"]
        for task in tasks:
            task_type = task.get("type", "daily")
            if task_type == "one-time":
                extra = f"(Due: {task.get('date', 'No date')})" if task.get("date") else ""
            elif task_type == "recurring":
                extra = f"({','.join(task.get('days', []))})"
            else:
                extra = "(Daily)"
            lines.append(f"- {task['title']} {extra}")
        return "\n".join(lines)

    def error_message(self, error):
        """Generate an error message with a back button."""
        buttons = [[InlineKeyboardButton("Back to Main Menu", callback_data="back")]]
        return f"Error: {error}", InlineKeyboardMarkup(buttons)