# task_manager.py
# Manages task CRUD operations and history for the Family Task Bot.

import uuid
from datetime import datetime, date
from storage import Storage
from config import TASK_TYPES, HISTORY_RETENTION_DAYS, VALID_DAYS

class TaskManager:
    def __init__(self):
        """Initialize TaskManager with Storage instance."""
        self.storage = Storage()

    def add_task(self, username, title, task_type, time, date=None, days=None):
        """Create a new task for the specified user."""
        if not title or not time:
            raise ValueError("Title and time are required.")
        if task_type not in TASK_TYPES:
            raise ValueError("Invalid task type.")
        if task_type == "one-time" and not date:
            raise ValueError("One-time tasks require a date.")
        if task_type == "recurring" and (not days or not isinstance(days, list)):
            raise ValueError("Recurring tasks require a list of days.")

        task = {
            "id": str(uuid.uuid4()),
            "title": title,
            "type": task_type,
            "time": time,
            "completed": False
        }
        if task_type == "one-time":
            task["date"] = date
        elif task_type == "recurring":
            task["days"] = days
        self.storage.save_task(username, task)
        return task["id"]

    def get_user_tasks(self, username, mine=True):
        """Get incomplete tasks for a user (mine) or all other users (not mine)."""
        all_users = self.storage.get_all_users()
        today = date.today().isoformat()
        weekday = date.today().strftime("%A")[:3]  # e.g., "Mon"
        
        if mine:
            tasks = self.storage.get_user_tasks(username)
            return [t for t in tasks if self._is_task_due(t, today, weekday)]
        else:
            other_tasks = []
            for other_user in all_users:
                if other_user != username:
                    tasks = self.storage.get_user_tasks(other_user)
                    other_tasks.extend([t for t in tasks if self._is_task_due(t, today, weekday)])
            return other_tasks

    def _is_task_due(self, task, today, weekday):
        """Check if a task is due today and not completed."""
        if task["completed"]:
            return False
        if task["type"] == "daily":
            return True
        elif task["type"] == "recurring":
            return weekday in task["days"]
        elif task["type"] == "one-time":
            return task["date"] <= today
        return False

    def get_task_by_id(self, username, task_id):
        """Get a task by ID from a user’s task list."""
        tasks = self.storage.get_user_tasks(username)
        return next((t for t in tasks if t["id"] == task_id), None)

    def complete_task(self, username, task_id):
        """Mark a task as completed and log it in history."""
        task = self.get_task_by_id(username, task_id)
        if task and not task["completed"]:
            task["completed"] = True
            self.storage.save_task(username, task)
            self.storage.log_history(task, "completed", username)

    def edit_task(self, username, task_id, title=None, time=None, date=None, days=None):
        """Edit a non-completed task’s fields."""
        task = self.get_task_by_id(username, task_id)
        if not task:
            raise ValueError("Task not found.")
        if task["completed"]:
            raise ValueError("Cannot edit a completed task.")
        
        if title:
            task["title"] = title
        if time:
            task["time"] = self.validate_time(time)
        if task["type"] == "one-time" and date:
            task["date"] = self.validate_date(date)
        elif task["type"] == "recurring" and days:
            task["days"] = self.validate_days(days)
        self.storage.save_task(username, task)

    def delete_task(self, username, task_id):
        """Delete a task and log it in history."""
        task = self.get_task_by_id(username, task_id)
        if task:
            self.storage.delete_task(username, task_id)
            self.storage.log_history(task, "deleted", username)

    def get_tasks_for_reminder(self, username):
        """Get tasks due today or past due one-time tasks for reminders."""
        tasks = self.storage.get_user_tasks(username)
        today = date.today().isoformat()
        weekday = date.today().strftime("%A")[:3]
        return [t for t in tasks if self._is_task_due(t, today, weekday)]

    def log_incomplete_tasks(self):
        """Log incomplete tasks due today or past due for history."""
        today = date.today().isoformat()
        weekday = date.today().strftime("%A")[:3]
        for username in self.storage.get_all_users():
            tasks = self.storage.get_user_tasks(username)
            for task in tasks:
                if self._is_task_due(task, today, weekday):
                    history = self.storage.get_history()
                    already_logged = any(
                        h["task_id"] == task["id"] and
                        h["status"] == "incomplete" and
                        h["timestamp"].startswith(today)
                        for h in history
                    )
                    if not already_logged:
                        self.storage.log_history(task, "incomplete", username)

    def get_history(self):
        """Return the full task history."""
        return self.storage.get_history()

    def validate_date(self, date_str):
        """Validate a date string (YYYY-MM-DD) is today or future."""
        try:
            task_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if task_date < date.today():
                raise ValueError("Date must be today or in the future.")
            return date_str
        except ValueError as e:
            raise ValueError("Invalid date format. Use YYYY-MM-DD.") from e

    def validate_time(self, time_str):
        """Validate a time string (HH:MM)."""
        try:
            datetime.strptime(time_str, "%H:%M")
            return time_str
        except ValueError:
            raise ValueError("Invalid time format. Use HH:MM (24-hour).")

    def validate_days(self, days):
        """Validate a list of days for recurring tasks."""
        if not days or not all(day in VALID_DAYS for day in days):
            raise ValueError(f"Invalid days. Use {', '.join(VALID_DAYS)}.")
        return days