# Family Task Manager Telegram Bot - Product Requirements Document (PRD)

## Overview
The Family Task Manager is a Telegram-based task management bot designed for a family of fewer than 10 users. It provides a GUI-only interface using inline keyboards, stores data in JSON files, and supports basic task operations with minimal complexity. The bot is built to be intuitive, low-maintenance, and extensible for future enhancements.

## Goals
- Enable quick task creation, viewing, and completion for family members.
- Provide daily 7 AM reminders and manual nudges to keep tasks on track.
- Maintain a 14-day task history for reference and accountability.
- Keep maintenance low with a simple, extensible architecture using Python and JSON-based storage.

## Users
- **Target Users:** Family members with no access controls; all tasks are visible to everyone to encourage shared responsibility.
- **Assumptions:** Users interact via Telegram, and the bot assumes a single time zone (defaulting to America/Chicago) for simplicity.

## Features

### Tasks
- **Types:**
  - **Daily:** Tasks that recur every day and reset daily (e.g., "Walk the dog"). Included in "View My Tasks" if not completed today.
  - **Recurring:** Tasks scheduled for specific days of the week, resetting daily (e.g., "Feed the cat" on Mon, Wed, Sat). Included in "View My Tasks" if the current day matches the schedule and not completed today.
  - **One-time:** Tasks with a specific due date, carrying over until completed (e.g., "yardwork" due 2025-02-02). Included in "View My Tasks" if not completed today, regardless of due date (past, present, or future).
- **Attributes:**
  - **GUID-based ID:** Unique identifier for each task (e.g., "e8b5f9a1-2b3c-4d5e-6789-0abcdef12345").
  - **Title:** Descriptive name of the task (e.g., "Walk the dog").
  - **Time:** Default 23:59 or user-specified time in HH:MM format (e.g., "08:00").
  - **Type-specific Data:** "date" for one-time tasks (YYYY-MM-DD), "days" for recurring tasks (e.g., ["Mon", "Wed"]).
  - **Completion Status:** List of completion dates (e.g., ["2025-02-26"]) to track when tasks are marked done.
- **Operations:**
  - **Create:** Add new tasks with type, title, time, and type-specific details.
  - **View:**
    - **My Tasks:** Displays tasks assigned to the user, filtered for action (daily/recurring due today and incomplete, all incomplete one-time tasks regardless of due date).
    - **Other Users’ Tasks:** Shows tasks for selected users, filtered similarly to "My Tasks."
    - **View All Tasks:** Shows all tasks across users, including daily, recurring due today, and one-time tasks with due dates <= today, with completion status.
  - **Edit:** Modify title, time, or date/days for non-completed tasks only.
  - **Complete:** Mark a task as completed with today’s date, updating the completion list.
  - **Delete:** Remove a task, logging it in history.

### Reminders
- **Auto:** Sent at 7 AM local time (America/Chicago) to each user with tasks due that day (daily, recurring matching today, one-time due today), highlighting those needing action.
- **Manual:** "Nudge" feature allows any user to send an instant reminder to another user’s chat ID for a selected task, including its title and due time.

### User Management
- **Add:** Any user can add a new user by entering a Telegram username (e.g., "@gsdtexas"), with the bot assigning a `chat_id` on first interaction or `None` if unknown.
- **Validation:** Bot checks username existence on Telegram; unknown users are ignored without error.
- **Edit/Delete:** Any user can edit or delete users via the GUI, with self-deletion prevented.

### History
- **Storage:** 14-day log stored in `history.json`, pruning entries older than 14 days.
- **Details:** Includes task ID, title, status (completed/incomplete), timestamp, and user (if completed by someone).
- **Access:** Available via "View History" button, paginated with 10 entries per page.

### User Interface
- **Interaction:** Exclusively via inline keyboards for a GUI-only experience.
- **Task Creation Flow:**
  - Main Menu → "Add Task" → Select type (One-time, Recurring, Daily) → Enter title → Set time (default 23:59) → Set date (for one-time) or days (for recurring) → Confirm with task ID displayed.
- **Task Viewing:**
  - **My Tasks:** Lists user’s tasks with simplified labels (e.g., "Walk the dog (Daily)", "An definitely not (Mar 01)").
  - **Other Users’ Tasks:** Select a user to view their tasks, formatted similarly.
  - **View All Tasks:** Lists all relevant tasks with numbered toggles (e.g., "1. Walk the dog ✅ [Daily]"), allowing status changes.
- **Error Handling:** Displays clear messages (e.g., "Error: Enter date as YYYY-MM-DD") with a "Back to Main Menu" button.

## Non-Goals
- Text commands for operation.
- Support for multiple time zones.
- Tracking late completions beyond due date.
- Restrictions on task duplication.
- Automated backups or completion notifications.

## User Flows
1. **Create Task:**
   - **Steps:** Main Menu → Click "Add Task" → Choose type (e.g., "One-time") → Enter title (e.g., "yardwork") → Set time (e.g., "23:59") → Select date (e.g., "2025-02-02") → Confirm → Receive task ID (e.g., "a7b8e9c3-...").
   - **Keyboard Logic:** 
     - Initial: "Add Task" button.
     - Type Selection: Three buttons ("One-time", "Recurring", "Daily") + "Cancel".
     - Title Input: Text input prompt.
     - Time Input: Text input prompt (default pre-filled).
     - Date/Days: For one-time, buttons ("Today", "+1 Day", "+2 Days", "+3 Days", "+1 Week", "+2 Weeks", "+1 Month", "Cancel"); for recurring, multi-select days ("Mon", "Tue", etc.) + "Done" + "Cancel".
     - Confirmation: Displays task ID and returns to Main Menu.

2. **View/Complete Task:**
   - **Steps:** Main Menu → Click "View My Tasks" or "View Others" → (for others, select user) → View task list → Click task → Choose action (Complete/Edit/Delete) → Confirm action.
   - **Keyboard Logic:**
     - Initial: "View My Tasks", "View Others", "View All Tasks" buttons.
     - User Selection (Others): List of usernames (e.g., "@cindyli77", "@gsdtexas") + "Back to Main Menu".
     - Task List (My/Other): Buttons for each task (e.g., "Walk the dog (Daily)", "yardwork (Feb 02)") + "Back to Main Menu".
     - Task Actions: For owner: "Complete", "Edit", "Delete", "Back"; for non-owner: "Complete", "Edit", "Nudge", "Delete", "Back".
     - Post-Action: Returns to Main Menu or task list with confirmation.

3. **Edit Task:**
   - **Steps:** View task → Click "Edit" → Select field (Title/Time/Date/Days) → Enter new value → Confirm.
   - **Keyboard Logic:**
     - Edit Options: "Title", "Time", "Date/Days", "Cancel" buttons.
     - Field Input: Text input prompt for each field (e.g., "Enter new title:").
     - Confirmation: Returns to Main Menu with "Task updated!" message.

4. **Manage Users:**
   - **Steps:** Main Menu → Click "Users" → Choose action (Add/Edit/Delete) → Enter username → Confirm.
   - **Keyboard Logic:**
     - User Management: "Add User", "Edit User", "Delete User", "Back to Main Menu" buttons.
     - Action Input: Text input prompt (e.g., "Enter Telegram username to add:").
     - Confirmation: Returns to Main Menu with success/error message (e.g., "User @gsdtexas added!").

5. **View History:**
   - **Steps:** Main Menu → Click "View History" → View paginated list → Navigate (Previous/Next) or return.
   - **Keyboard Logic:**
     - History View: Displays list (e.g., "Completed: Walk the dog by gsdtexas at 2025-02-26T12:00:00") + "Previous" (if page > 0) + "Next" (if more entries) + "Back to Main Menu".
     - Pagination: Updates page number and list based on button clicks.

## Technical Requirements
- **Platform:** Telegram Bot API with `python-telegram-bot` library (version >= 21.0).
- **Language:** Python 3.12.
- **Storage:** 
  - `tasks.json`: Real-time storage of user tasks with structure { "users": { username: { "chat_id": int/str, "tasks": [task_dict] } } }.
  - `history.json`: 14-day log with structure { "history": [ { "task_id": str, "title": str, "status": str, "timestamp": str, "user": str } ] }.
- **Config:** `.env` file with `BOT_TOKEN=7732177198:AAGrOcvo1jXDWYOexwHwmDxUXqYZejrf_VQ` for authentication.
- **Dependencies:** `python-dotenv==1.0.1` for environment variable management.
- **Assumptions:** Single-threaded access (no file locking) due to <10 users.

## Success Metrics
- Daily active usage by all family members (target: 100% participation).
- Zero user-reported confusion or errors during task management (target: <1% error rate based on logs).
- Consistent task visibility and actionability across all views.

## Detailed Keyboard Logic
### Main Menu
- **Buttons:** "Add Task", "View My Tasks", "View Others", "View All Tasks", "Users", "View History".
- **Behavior:** 
  - Clicking any button triggers a new message or edits the current one with the corresponding view.
  - Initial state after `/start` or "Back" action.

### Task Creation Keyboards
1. **Type Selection:**
   - **Buttons:** "One-time", "Recurring", "Daily", "Cancel".
   - **Logic:** User selects a task type; "Cancel" returns to Main Menu. Each type leads to a title input prompt.
2. **Title Input:**
   - **Buttons:** None (text input prompt).
   - **Logic:** User enters title; bot waits for text, then proceeds to time input or date/days selection based on type.
3. **Time Input:**
   - **Buttons:** None (text input prompt, default "23:59" suggested).
   - **Logic:** User enters time in HH:MM; invalid input triggers error ("Time must be in HH:MM format"), valid input proceeds.
4. **Date Selection (One-time):**
   - **Buttons:** "Today", "+1 Day", "+2 Days", "+3 Days", "+1 Week", "+2 Weeks", "+1 Month", "Cancel".
   - **Logic:** Each button adds the offset to the current date, formats as YYYY-MM-DD, and creates the task. "Cancel" returns to Main Menu.
5. **Days Selection (Recurring):**
   - **Buttons:** "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun" (toggle with ✓), "Done", "Cancel".
   - **Logic:** Clicking a day toggles its selection; "Done" creates the task with selected days; "Cancel" returns to Main Menu. Requires at least one day.

### Task Viewing Keyboards
1. **User Selection (View Others):**
   - **Buttons:** List of usernames (e.g., "@cindyli77", "@gsdtexas") + "Back to Main Menu".
   - **Logic:** Each username button displays that user’s tasks; "Back" returns to Main Menu.
2. **Task List (My/Other):**
   - **Buttons:** One per task (e.g., "Walk the dog (Daily)", "yardwork (Feb 02)") + "Back to Main Menu".
   - **Logic:** Clicking a task opens action options; "Back" returns to Main Menu. Labels simplified: Daily as "(Daily)", Recurring as "(days)", One-time as "(Month Day)" if date exists.
3. **Task Actions:**
   - **Buttons (Owner):** "Complete", "Edit", "Delete", "Back".
   - **Buttons (Non-Owner):** "Complete", "Edit", "Nudge", "Delete", "Back".
   - **Logic:** "Complete" marks task done, "Edit" opens edit options, "Delete" removes task, "Nudge" sends a message to the owner, "Back" returns to task list.
4. **View All Tasks:**
   - **Buttons:** Numbered toggles (1 to n, up to 5 per row) + "Back to Main Menu".
   - **Logic:** Numbers correspond to task indices in the filtered list (daily, recurring due today, one-time due <= today); clicking toggles completion status and refreshes the list with the same filter.

### Edit Task Keyboards
1. **Edit Options:**
   - **Buttons:** "Title", "Time", "Date/Days", "Cancel".
   - **Logic:** Each field opens a text input prompt; "Cancel" returns to task actions.
2. **Field Input:**
   - **Buttons:** None (text input prompt).
   - **Logic:** User enters new value; invalid input (e.g., wrong date format) triggers error, valid input updates task and returns to Main Menu.

### User Management Keyboards
1. **User Management:**
   - **Buttons:** "Add User", "Edit User", "Delete User", "Back to Main Menu".
   - **Logic:** "Add User" and "Delete User" prompt for username; "Edit User" is unimplemented; "Back" returns to Main Menu.
2. **Username Input:**
   - **Buttons:** None (text input prompt).
   - **Logic:** User enters username (e.g., "@gsdtexas"); bot adds/deletes user, prevents self-deletion, and returns to Main Menu with confirmation.

### History Viewing Keyboard
- **Buttons:** "Previous" (if page > 0), "Next" (if more entries), "Back to Main Menu".
- **Logic:** Displays 10 entries per page, sorted by timestamp descending; "Previous"/"Next" adjusts page; "Back" returns to Main Menu.

## Notes
- The bot assumes single-threaded access due to the small user base (<10), avoiding file locking.
- All keyboards are designed for simplicity, with clear navigation and minimal steps to complete actions.