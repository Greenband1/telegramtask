# task_manager.py
# Manages task logic, reminders, and history for the Family Task Bot.

from datetime import datetime, timedelta
from storage import Storage
import uuid
from config import TASK_TYPES
import logging

# Set up logger
logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self):
        self.storage = Storage()
        self.valid_days = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}

    def _needs_action(self, task, today, weekday):
        """Check if a task needs action today."""
        if "type" not in task:
            logger.warning(f"Task {task.get('id', 'unknown')} is missing 'type' key.")
            return False
        
        task_type = task["type"]
        if task_type == "one-time":
            # Include all one-time tasks that are not completed today
            today_str = datetime.strptime(today, "%Y-%m-%d").date().isoformat()
            return today_str not in task.get("completions", [])
        elif task_type == "daily":
            needs_action = today not in task.get("completions", [])
        elif task_type == "recurring":
            if "days" not in task:
                logger.warning(f"Recurring task {task['id']} is missing 'days'.")
                needs_action = False
            else:
                needs_action = weekday in task["days"] and today not in task.get("completions", [])
        else:
            logger.warning(f"Unknown task type '{task_type}' for task {task['id']}.")
            needs_action = False
        
        logger.info(f"Task {task['id']} ({task['title']}): needs_action={needs_action}")
        return needs_action

    def _is_due_today(self, task, today, weekday):
        """Check if a task is due today, including completed tasks."""
        task_type = task.get("type", "daily")  # Default to daily if type is missing
        if task_type == "one-time":
            due_date = task.get("date")
            if due_date is None:
                logger.warning(f"One-time task {task.get('id', 'unknown')} is missing 'date'.")
                return False  # Exclude tasks without a date
            if due_date == today:
                return True  # Due today, show regardless of completion
            elif due_date < today and not any(c for c in task.get("completions", []) if c <= today):
                return True  # Overdue and not completed on or after due date
            return False  # Completed on or after due date, or due in future
        elif task_type == "daily":
            return True  # Always show daily tasks
        elif task_type == "recurring":
            if "days" not in task:
                return False  # Invalid recurring task
            return weekday in task["days"]  # Show if today is a recurring day
        return False  # Unknown type, exclude

    def get_user_tasks(self, username, mine=True):
        """Get tasks for a user, optionally filtering for those needing action."""
        tasks = self.storage.get_user_tasks(username)
        if not mine:
            return tasks  # Return all tasks if mine=False
        today = datetime.now().date().isoformat()
        weekday = datetime.now().strftime("%a")
        return [task for task in tasks if self._needs_action(task, today, weekday)]

    def get_tasks_due_today(self, username):
        """Get all tasks due today for a user, completed or incomplete."""
        tasks = self.storage.get_user_tasks(username)
        today = datetime.now().date().isoformat()
        weekday = datetime.now().strftime("%a")
        return [task for task in tasks if self._is_due_today(task, today, weekday)]

    def add_task(self, username, title, task_type, time="23:59", date=None, days=None):
        """Add a new task for a user."""
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "title": title,
            "type": task_type,
            "time": time,
            "completions": []
        }
        if task_type == "one-time" and date is None:
            raise ValueError("One-time tasks must have a date.")
        if task_type == "one-time":
            task["date"] = date
        elif task_type == "recurring":
            task["days"] = days
        self.storage.save_task(username, task)
        return task_id

    def complete_task(self, username, task_id):
        """Mark a task as completed today."""
        tasks = self.storage.get_user_tasks(username)
        for task in tasks:
            if task["id"] == task_id:
                today = datetime.now().date().isoformat()
                if today not in task.get("completions", []):
                    task["completions"] = task.get("completions", []) + [today]
                    self.storage.save_task(username, task)
                    self.storage.log_history(task, "completed", username)
                break

    def edit_task(self, username, task_id, title=None, time=None, date=None, days=None):
        """Edit an existing task."""
        tasks = self.storage.get_user_tasks(username)
        for task in tasks:
            if task["id"] == task_id:
                if title:
                    task["title"] = title
                if time:
                    task["time"] = time
                if date and task["type"] == "one-time":
                    task["date"] = date
                if days and task["type"] == "recurring":
                    task["days"] = days
                self.storage.save_task(username, task)
                break

    def delete_task(self, username, task_id):
        """Delete a task."""
        self.storage.delete_task(username, task_id)

    def log_incomplete_tasks(self):
        """Log tasks that were due today but not completed."""
        today = datetime.now().date().isoformat()
        weekday = datetime.now().strftime("%a")
        for username in self.storage.get_all_users():
            tasks = self.get_tasks_due_today(username)
            for task in tasks:
                if today not in task.get("completions", []):
                    self.storage.log_history(task, "incomplete", username)

    def get_history(self):
        """Retrieve all history entries."""
        return self.storage.get_history()

    def get_task_by_id(self, username, task_id):
        """Retrieve a task by its ID."""
        tasks = self.storage.get_user_tasks(username)
        return next((task for task in tasks if task["id"] == task_id), None)

    def validate_time(self, time_str):
        """Validate and return time in HH:MM format."""
        try:
            datetime.strptime(time_str, "%H:%M")
            return time_str
        except ValueError:
            raise ValueError("Time must be in HH:MM format (e.g., 14:30).")

    def validate_date(self, date_str):
        """Validate and return date in YYYY-MM-DD format."""
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if date < datetime.now().date():
                raise ValueError("Date cannot be in the past.")
            return date_str
        except ValueError as e:
            if str(e) == "Date cannot be in the past.":
                raise
            raise ValueError("Date must be in YYYY-MM-DD format (e.g., 2025-12-31).")

    def validate_days(self, days):
        """Validate recurring task days."""
        invalid_days = set(days) - self.valid_days
        if invalid_days:
            raise ValueError(f"Invalid days: {', '.join(invalid_days)}. Use Mon, Tue, Wed, Thu, Fri, Sat, Sun.")
        return days