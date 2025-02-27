from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import logging
from datetime import datetime, date
from config import BOT_TOKEN, REMINDER_TIME
from storage import Storage
from task_manager import TaskManager
from ui import UI
from datetime import timedelta

# Enable detailed logging with tracebacks
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

storage = Storage()
task_mgr = TaskManager()
ui = UI()
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    storage.add_user_if_new(username, chat_id)
    await update.message.reply_text("Welcome to Family Task Bot!", reply_markup=ui.main_menu())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    username = query.from_user.username
    chat_id = query.message.chat_id
    data = query.data

    await query.answer()
    try:
        if data == "add_task":
            user_states[chat_id] = {"step": "task_type"}
            await query.edit_message_text("Select task type:", reply_markup=ui.task_types())
        elif data == "view_my":
            tasks = task_mgr.get_user_tasks(username, mine=True)
            keyboard = ui.task_list(tasks, "task")
            text = "Your tasks:" if keyboard else "No tasks due today!"
            await query.edit_message_text(text, reply_markup=keyboard or ui.main_menu())
        elif data == "view_others":
            other_users = [u for u in storage.get_all_users() if u != username]
            keyboard = ui.user_list(other_users)
            text = "Select a user to view their tasks:" if keyboard else "No other users found!"
            await query.edit_message_text(text, reply_markup=keyboard or ui.main_menu())
        elif data.startswith("view_user_"):
            target_user = data.split("_")[2]
            tasks = task_mgr.get_user_tasks(target_user, mine=True)
            keyboard = ui.task_list(tasks, "task", target_user)
            text = f"@{target_user}'s tasks:" if keyboard else f"No tasks due today for @{target_user}!"
            await query.edit_message_text(text, reply_markup=keyboard or ui.main_menu())
        elif data == "view_all":
            today = date.today()
            today_str = today.isoformat()
            weekday = today.strftime("%a")
            tasks = []
            for user in storage.get_all_users():
                user_tasks = task_mgr.get_user_tasks(user, mine=False)  # Fetch all tasks
                for task in user_tasks:
                    task_with_owner = task.copy()
                    task_with_owner["owner"] = user
                    task_type = task.get("type", "daily")
                    if task_type == "daily" or (task_type == "recurring" and weekday in task.get("days", [])) or \
                       (task_type == "one-time" and task.get("date") and datetime.strptime(task.get("date"), "%Y-%m-%d").date() <= today):
                        tasks.append(task_with_owner)
            message, keyboard = ui.all_tasks_message_and_keyboard(tasks)
            await query.edit_message_text(message, reply_markup=keyboard)
        elif data == "users":
            await query.edit_message_text("Manage users:", reply_markup=ui.user_management())
        elif data.startswith("history_"):
            page = int(data.split("_")[1])
            history = task_mgr.get_history()
            text, keyboard = ui.history_view(history, page)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")

        elif data.startswith("type_"):
            task_type_map = {"one": "one-time", "recurring": "recurring", "daily": "daily"}
            task_type = task_type_map[data.split("_")[1]]
            user_states[chat_id] = {"step": "title", "type": task_type}
            await query.edit_message_text("Enter task title:")
        elif data == "days_done":
            days = user_states[chat_id].get("days", [])
            if not days:
                await query.edit_message_text("Select at least one day.", reply_markup=ui.days_selection())
            else:
                task_id = task_mgr.add_task(username, user_states[chat_id]["title"], "recurring", days=days)
                user_states.pop(chat_id)
                await query.edit_message_text(f"Task added (ID: {task_id})!", reply_markup=ui.main_menu())
        elif data.startswith("day_"):
            day = data.split("_")[1].capitalize()[:3]
            state = user_states[chat_id]
            days = state.get("days", [])
            if day in days:
                days.remove(day)
            else:
                days.append(day)
            state["days"] = days
            await query.edit_message_reply_markup(reply_markup=ui.days_selection(days))
        elif data.startswith("date_"):
            days_offset = int(data.split("_")[1])
            due_date = (datetime.today() + timedelta(days=days_offset)).date().isoformat()
            task_id = task_mgr.add_task(username, user_states[chat_id]["title"], "one-time", date=due_date)
            user_states.pop(chat_id)
            await query.edit_message_text(f"Task added (ID: {task_id})!", reply_markup=ui.main_menu())
        elif data.startswith("toggle_"):
            index = int(data.split("_")[1])
            today = date.today()
            today_str = today.isoformat()
            weekday = today.strftime("%a")
            tasks = []
            for user in storage.get_all_users():
                user_tasks = task_mgr.get_user_tasks(user, mine=False)  # Fetch all tasks
                for task in user_tasks:
                    task_with_owner = task.copy()
                    task_with_owner["owner"] = user
                    task_type = task.get("type", "daily")
                    if task_type == "daily" or (task_type == "recurring" and weekday in task.get("days", [])) or \
                       (task_type == "one-time" and task.get("date") and datetime.strptime(task.get("date"), "%Y-%m-%d").date() <= today):
                        tasks.append(task_with_owner)
            if 0 <= index < len(tasks):
                task = tasks[index]
                if today_str in task["completions"]:
                    task["completions"].remove(today_str)
                    status = "incomplete"
                else:
                    task["completions"].append(today_str)
                    status = "completed"
                actual_task = next((t for t in storage.get_user_tasks(task["owner"]) if t["id"] == task["id"]), None)
                if actual_task:
                    actual_task["completions"] = task["completions"]
                    storage.save_task(task["owner"], actual_task)
                    storage.log_history(actual_task, status, username)
                # Rebuild filtered task list after toggle
                tasks = []
                for user in storage.get_all_users():
                    user_tasks = task_mgr.get_user_tasks(user, mine=False)
                    for task in user_tasks:
                        task_with_owner = task.copy()
                        task_with_owner["owner"] = user
                        task_type = task.get("type", "daily")
                        if task_type == "daily" or (task_type == "recurring" and weekday in task.get("days", [])) or \
                           (task_type == "one-time" and task.get("date") and datetime.strptime(task.get("date"), "%Y-%m-%d").date() <= today):
                            tasks.append(task_with_owner)
                message, keyboard = ui.all_tasks_message_and_keyboard(tasks)
                await query.edit_message_text(message, reply_markup=keyboard)

        elif data.startswith("task_"):
            task_id = data.split("_")[1]
            task = next((t for u in storage.get_all_users() for t in storage.get_user_tasks(u) if t["id"] == task_id), None)
            if task:
                is_owner = task in storage.get_user_tasks(username)
                await query.edit_message_text(f"Task: {task['title']}", reply_markup=ui.task_actions(task_id, is_owner))
            else:
                await query.edit_message_text("Task not found.", reply_markup=ui.main_menu())
        elif data.startswith("complete_"):
            task_id = data.split("_")[1]
            task_mgr.complete_task(username, task_id)
            await query.edit_message_text("Task completed!", reply_markup=ui.main_menu())
        elif data.startswith("edit_"):
            task_id = data.split("_")[1]
            task = next((t for u in storage.get_all_users() for t in storage.get_user_tasks(u) if t["id"] == task_id), None)
            if task:
                user_states[chat_id] = {"step": "edit", "task_id": task_id}
                await query.edit_message_text("Edit task:", reply_markup=ui.edit_options(task_id))
            else:
                await query.edit_message_text("Task not found.", reply_markup=ui.main_menu())
        elif data.startswith("delete_"):
            task_id = data.split("_")[1]
            task_mgr.delete_task(username, task_id)
            await query.edit_message_text("Task deleted!", reply_markup=ui.main_menu())
        elif data.startswith("nudge_"):
            task_id = data.split("_")[1]
            task = next((t for u in storage.get_all_users() for t in storage.get_user_tasks(u) if t["id"] == task_id), None)
            if task:
                owner = next(u for u in storage.get_all_users() if task in storage.get_user_tasks(u))
                owner_chat_id = storage.get_user_chat_id(owner)
                if owner_chat_id:
                    await context.bot.send_message(chat_id=owner_chat_id, text=f"Nudge from @{username}: {task['title']} due at {task['time']}!")
                    await query.edit_message_text("Nudge sent!", reply_markup=ui.main_menu())
                else:
                    await query.edit_message_text("User has no chat ID.", reply_markup=ui.main_menu())

        elif data.startswith("edit_title_") or data.startswith("edit_time_") or data.startswith("edit_date_"):
            task_id = data.split("_")[2]
            field = data.split("_")[1]
            user_states[chat_id] = {"step": f"edit_{field}", "task_id": task_id}
            prompt = {"title": "Enter new title:", "time": "Enter new time (HH:MM):", "date": "Enter new date (YYYY-MM-DD) or days:"}
            await query.edit_message_text(prompt[field])

        elif data == "add_user":
            user_states[chat_id] = {"step": "add_user"}
            await query.edit_message_text("Enter Telegram username to add (e.g., @username):")
        elif data == "edit_user":
            await query.edit_message_text("Edit user not implemented yet.", reply_markup=ui.main_menu())
        elif data == "delete_user":
            user_states[chat_id] = {"step": "delete_user"}
            await query.edit_message_text("Enter Telegram username to delete:")

        elif data in ["back", "cancel"]:
            user_states.pop(chat_id, None)
            await query.edit_message_text("Main menu:", reply_markup=ui.main_menu())

    except Exception as e:
        import traceback
        logger.error(f"Error in button handler: {e}\n{traceback.format_exc()}")
        error_text, error_markup = ui.error_message(f"Something went wrong: {str(e)}")
        await query.edit_message_text(error_text, reply_markup=error_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    username = update.message.from_user.username
    text = update.message.text.strip()

    if chat_id not in user_states:
        await update.message.reply_text("Please use /start to begin.", reply_markup=ui.main_menu())
        return

    state = user_states[chat_id]
    try:
        if state["step"] == "title":
            state["title"] = text
            if state["type"] == "one-time":
                state["step"] = "date"
                await update.message.reply_text("Select due date:", reply_markup=ui.date_selection())
            elif state["type"] == "recurring":
                state["step"] = "days"
                await update.message.reply_text("Select days:", reply_markup=ui.days_selection())
            else:  # daily
                task_id = task_mgr.add_task(username, state["title"], "daily")
                user_states.pop(chat_id)
                await update.message.reply_text(f"Task added (ID: {task_id})!", reply_markup=ui.main_menu())
                
        elif state["step"].startswith("edit_"):
            field = state["step"].split("_")[1]
            task_id = state["task_id"]
            if field == "title":
                task_mgr.edit_task(username, task_id, title=text)
            elif field == "time":
                time = task_mgr.validate_time(text)
                task_mgr.edit_task(username, task_id, time=time)
            elif field == "date":
                task = task_mgr.get_task_by_id(username, task_id)
                if task["type"] == "one-time":
                    date = task_mgr.validate_date(text)
                    task_mgr.edit_task(username, task_id, date=date)
                elif task["type"] == "recurring":
                    days = [d.strip().capitalize()[:3] for d in text.split(",")]
                    days = task_mgr.validate_days(days)
                    task_mgr.edit_task(username, task_id, days=days)
            user_states.pop(chat_id)
            await update.message.reply_text("Task updated!", reply_markup=ui.main_menu())

        elif state["step"] == "add_user":
            new_username = text.lstrip("@")
            storage.add_user_if_new(new_username, None)
            user_states.pop(chat_id)
            await update.message.reply_text(f"User {new_username} added!", reply_markup=ui.main_menu())
            
        elif state["step"] == "delete_user":
            target_username = text.lstrip("@")
            if target_username not in storage.get_all_users():
                await update.message.reply_text(f"User {target_username} not found.", reply_markup=ui.main_menu())
            elif target_username == username:
                await update.message.reply_text("You cannot delete yourself!", reply_markup=ui.main_menu())
            else:
                storage.delete_user(target_username)
                await update.message.reply_text(f"User {target_username} deleted!", reply_markup=ui.main_menu())
            user_states.pop(chat_id)

    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        error_text, error_markup = ui.error_message(f"Failed to process: {str(e)}")
        await update.message.reply_text(error_text, reply_markup=error_markup)

async def send_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    task_mgr.log_incomplete_tasks()
    for username in storage.get_all_users():
        chat_id = storage.get_user_chat_id(username)
        if chat_id:
            tasks = task_mgr.get_user_tasks(username, mine=True)
            if tasks:
                await context.bot.send_message(chat_id=chat_id, text=ui.reminder_message(tasks))

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    reminder_time = datetime.strptime(REMINDER_TIME, "%H:%M").time()
    application.job_queue.run_daily(send_reminders, time=reminder_time)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()