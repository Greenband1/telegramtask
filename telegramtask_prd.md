# Family Task Manager Telegram Bot - Product Requirements Document (PRD)

## Overview
A simple Telegram-based task management bot for a family of <10 users. Uses inline keyboards for a GUI-only interface, stores data in JSON files, and supports basic task operations with minimal complexity.

## Goals
- Enable quick task creation, viewing, and completion.
- Provide daily 7 AM reminders and manual nudges.
- Maintain a 14-day task history.
- Keep maintenance low with an extensible architecture.

## Users
- Family members (no access controls, all tasks visible to everyone).

## Features

### Tasks
- **Types**: 
  - Daily (every day, resets daily).
  - Recurring (specific days of the week, resets daily, incomplete logged in history).
  - One-time (specific date, carries over until completed).
- **Attributes**: GUID-based ID, title, time, type-specific date/days, completion status.
- **Operations**: Create, view (mine vs. others), edit (non-completed only), complete, delete.

### Reminders
- **Auto**: Sent to each user at 7 AM local time with all tasks due that day (daily, recurring, one-time).
- **Manual**: Instant “nudge” sent to a selected user for their due tasks.

### User Management
- **Add**: Anyone can add users by Telegram username.
- **Validation**: On first access, bot collects chat ID if username exists; ignores unknown users.
- **Edit/Delete**: Anyone can modify/delete users via GUI.

### History
- **Storage**: 14-day log of completed and incomplete tasks.
- **Details**: Task ID, title, status (completed/incomplete), timestamp, user who completed (if applicable).
- **Access**: “View History” button in main menu.

### User Interface
- Inline keyboards for all interactions.
- Task creation: Simple flow (type → date/days/time → confirm).
- Task viewing: Split into “My Tasks” and “Other Users’ Tasks.”
- Error handling: Clear, actionable messages (e.g., “Enter date as YYYY-MM-DD”).

## Non-Goals
- Text commands, time zone support, late completion tracking, task duplication restrictions, backups, completion notifications.

## User Flows
1. **Create Task**: Main Menu → Add Task → [One-time/Recurring/Daily] → Time/Date/Days → Confirm.
2. **View/Complete Task**: Main Menu → View Tasks → [My Tasks/Other Users’ Tasks] → Select → [Complete/Edit/Delete].
3. **Edit Task**: Select Task → Edit → Modify Title/Time/Date/Days → Confirm.
4. **Manage Users**: Main Menu → Users → [Add/Edit/Delete] → Enter Username.
5. **View History**: Main Menu → View History → List of last 14 days.

## Technical Requirements
- **Platform**: Telegram Bot API.
- **Language**: Python with `python-telegram-bot` library.
- **Storage**: Real-time JSON updates (`tasks.json` for live data, `history.json` for 14-day log).
- **Config**: `.env` with `BOT_TOKEN=7732177198:AAGrOcvo1jXDWYOexwHwmDxUXqYZejrf_VQ`.

## Success Metrics
- Daily usage by all family members.
- Intuitive task management without confusion or errors.