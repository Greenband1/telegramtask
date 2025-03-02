from datetime import datetime, timedelta
from storage import Storage
import uuid
from config import TASK_TYPES
import logging

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self):
        self.storage = Storage()
        self.valid_days = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}

    def _needs_action(self, task, today, weekday):
        if "type" not in task:
            logger.warning(f"Task {task.get('id', 'unknown')} is missing 'type' key.")
            return False
        task_type = task["type"]
        if task_type == "one-time":
            needs_action = len(task.get("completions", [])) == 0
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
        logger.info(f"Task {task['id']} ({task['title']}): needs_action={needs_action}, type={task_type}, completions={task.get('completions', [])}")
        return needs_action

    def _is_due_today(self, task, today, weekday):
        """Check if a task is due today, regardless of completion status."""
        task_type = task.get("type", "daily")
        if task_type == "one-time":
            due_date = task.get("date")
            if due_date is None:
                logger.warning(f"One-time task {task.get('id', 'unknown')} is missing 'date'.")
                return False
            if due_date == today:
                return True
            elif due_date < today and not any(c for c in task.get("completions", []) if c <= today):
                return True
            return False
        elif task_type == "daily":
            return True
        elif task_type == "recurring":
            if "days" not in task:
                return False
            return weekday in task["days"]
        return False

    def get_user_tasks(self, username, mine=True):
        tasks = self.storage.get_user_tasks(username)
        if not mine:
            return tasks
        today = datetime.now().date().isoformat()
        weekday = datetime.now().strftime("%a")
        filtered_tasks = [task for task in tasks if self._needs_action(task, today, weekday)]
        logger.info(f"User {username} tasks (mine=True): {len(filtered_tasks)} tasks")
        return filtered_tasks

    def get_tasks_due_today(self, username):
        """Get all tasks due today for a user, including completed ones."""
        tasks = self.storage.get_user_tasks(username)
        today = datetime.now().date().isoformat()
        weekday = datetime.now().strftime("%a")
        filtered_tasks = [task for task in tasks if self._is_due_today(task, today, weekday)]
        logger.info(f"Tasks due today for {username}: {len(filtered_tasks)} tasks, today={today}, weekday={weekday}")
        return filtered_tasks

    def add_task(self, username, title, task_type, time="23:59", date=None, days=None):
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
        tasks = self.storage.get_user_tasks(username)
        for task in tasks:
            if task["id"] == task_id:
                today = datetime.now().date().isoformat()
                if today not in task.get("completions", []):
                    task["completions"] = task.get("completions", []) + [today]
                    self.storage.save_task(username, task)
                    self.storage.log_history(task, "completed", username)
                break

    def toggle_task(self, username, task_id):
        tasks = self.storage.get_user_tasks(username)
        for task in tasks:
            if task["id"] == task_id:
                today = datetime.now().date().isoformat()
                if today in task.get("completions", []):
                    task["completions"].remove(today)
                    status = "incomplete"
                else:
                    task["completions"].append(today)
                    status = "completed"
                self.storage.save_task(username, task)
                self.storage.log_history(task, status, username)
                return status
        raise ValueError(f"Task {task_id} not found for user {username}")

    def edit_task(self, username, task_id, title=None, time=None, date=None, days=None):
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
        self.storage.delete_task(username, task_id)

    def log_incomplete_tasks(self):
        today = datetime.now().date().isoformat()
        weekday = datetime.now().strftime("%a")
        for username in self.storage.get_all_users():
            tasks = self.get_tasks_due_today(username)
            for task in tasks:
                if today not in task.get("completions", []):
                    self.storage.log_history(task, "incomplete", username)

    def get_history(self):
        return self.storage.get_history()

    def get_task_by_id(self, username, task_id):
        tasks = self.storage.get_user_tasks(username)
        return next((task for task in tasks if task["id"] == task_id), None)

    def validate_time(self, time_str):
        try:
            datetime.strptime(time_str, "%H:%M")
            return time_str
        except ValueError:
            raise ValueError("Time must be in HH:MM format (e.g., 14:30).")

    def validate_date(self, date_str):
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
        invalid_days = set(days) - self.valid_days
        if invalid_days:
            raise ValueError(f"Invalid days: {', '.join(invalid_days)}. Use Mon, Tue, Wed, Thu, Fri, Sat, Sun.")
        return days