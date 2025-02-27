# storage.py
# Manages JSON storage for tasks and history in the Family Task Bot.

import json
from datetime import datetime, timedelta
import os
from config import TASKS_FILE, HISTORY_FILE, HISTORY_RETENTION_DAYS

class Storage:
    def __init__(self):
        # Ensure JSON files exist with default structure if they don’t
        # Note: No file locking; assumes single-threaded access for simplicity (<10 users).
        if not os.path.exists(TASKS_FILE):
            self.save_data(TASKS_FILE, {"users": {}})
        if not os.path.exists(HISTORY_FILE):
            self.save_data(HISTORY_FILE, {"history": []})

    def load_data(self, filename):
        """Load data from a JSON file, returning default structure if file is missing."""
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"users": {}} if filename == TASKS_FILE else {"history": []}

    def save_data(self, filename, data):
        """Save data to a JSON file with proper formatting."""
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

    def add_user_if_new(self, username, chat_id):
        """Add a new user if they don’t exist, associating their chat ID."""
        data = self.load_data(TASKS_FILE)
        if username not in data["users"]:
            data["users"][username] = {"chat_id": chat_id, "tasks": []}
            self.save_data(TASKS_FILE, data)
        elif data["users"][username]["chat_id"] != chat_id and chat_id is not None:
            # Update chat ID if provided and different
            data["users"][username]["chat_id"] = chat_id
            self.save_data(TASKS_FILE, data)

    def get_user_tasks(self, username):
        """Retrieve all tasks for a given user."""
        data = self.load_data(TASKS_FILE)
        return data["users"].get(username, {}).get("tasks", [])

    def save_task(self, username, task):
        """Save a new or updated task for a user, ensuring required fields."""
        # Ensure task has required fields with defaults if missing
        task = {
            "id": task.get("id"),
            "title": task.get("title", "Untitled"),
            "type": task.get("type", "one-time"),
            "time": task.get("time", "23:59"),
            "completions": task.get("completions", []),
            **{k: v for k, v in task.items() if k in ["date", "days"]}  # Preserve optional fields
        }
        if not task["id"] or not task["title"]:
            raise ValueError("Task must have an 'id' and 'title'.")
        
        data = self.load_data(TASKS_FILE)
        if username not in data["users"]:
            data["users"][username] = {"chat_id": None, "tasks": []}
        tasks = data["users"][username]["tasks"]
        task_ids = [t["id"] for t in tasks]
        if task["id"] in task_ids:
            for i, t in enumerate(tasks):
                if t["id"] == task["id"]:
                    tasks[i] = task
                    break
        else:
            tasks.append(task)
        data["users"][username]["tasks"] = tasks
        self.save_data(TASKS_FILE, data)

    def delete_task(self, username, task_id):
        """Remove a task by ID for a user and log it in history."""
        data = self.load_data(TASKS_FILE)
        if username in data["users"]:
            tasks = data["users"][username]["tasks"]
            task_to_delete = next((t for t in tasks if t["id"] == task_id), None)
            if task_to_delete:
                tasks.remove(task_to_delete)
                data["users"][username]["tasks"] = tasks
                self.save_data(TASKS_FILE, data)
                self.log_history(task_to_delete, "deleted", username)
            else:
                raise ValueError("Task not found.")

    def get_all_users(self):
        """Return a list of all usernames."""
        data = self.load_data(TASKS_FILE)
        return list(data["users"].keys())

    def delete_user(self, username):
        """Remove a user and their tasks."""
        data = self.load_data(TASKS_FILE)
        if username in data["users"]:
            del data["users"][username]
            self.save_data(TASKS_FILE, data)

    def log_history(self, task, status, username):
        """Log task activity (completed, incomplete, deleted) to history."""
        history_data = self.load_data(HISTORY_FILE)
        history_entry = {
            "task_id": task["id"],
            "title": task["title"],
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "user": username
        }
        history_data["history"].append(history_entry)
        self.prune_history(history_data)
        self.save_data(HISTORY_FILE, history_data)

    def prune_history(self, history_data):
        """Remove history entries older than 14 days."""
        cutoff = datetime.now() - timedelta(days=HISTORY_RETENTION_DAYS)
        history_data["history"] = [
            entry for entry in history_data["history"]
            if datetime.fromisoformat(entry["timestamp"]) >= cutoff
        ]

    def get_history(self):
        """Retrieve all history entries."""
        return self.load_data(HISTORY_FILE)["history"]

    def get_user_chat_id(self, username):
        """Get the chat ID for a user."""
        data = self.load_data(TASKS_FILE)
        return data["users"].get(username, {}).get("chat_id")