"""
Background notification scheduler for Acadence.
Uses a threshold-based system: notifications fire when a task crosses
specific day-boundaries (e.g., 2 days before, 1 day before, due today, overdue).
The scheduler polls near real-time (every 15 seconds).
"""
import threading
import time
from datetime import datetime, timedelta
from utils.notification_manager import NotificationManager
from utils.logger import logger


class NotificationScheduler:
    """Daemon thread that checks tasks and fires native system notifications
    based on days-before-deadline thresholds per priority."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton — only one scheduler should ever run."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._running = False
        self._thread = None
        self._user_id = None
        self._username = None

        # How many days in advance to notify, per priority (user-configurable 0–7)
        self._advance_days = {
            "High": 2,
            "Medium": 1,
            "Low": 0,
        }
        # Track which threshold has already fired per task to avoid spam.
        # Keys look like: "overdue_5", "today_5", "days_2_5" (threshold_taskId)
        self._notified_task_ids = set()
        self._enabled = True
        self._persistent = True
        self._group_notifications = False

    def start(self, user_id: int, username: str, settings: dict = None):
        """Starts the background scheduler loop."""
        self.stop()  # Clean up any previous run

        self._user_id = user_id
        self._username = username
        self._notified_task_ids = set()

        if settings:
            self.update_settings(settings)

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"NotificationScheduler started for user '{username}' (id={user_id})")

    def stop(self):
        """Stops the background scheduler loop."""
        if self._running:
            self._running = False
            logger.info("NotificationScheduler stopped.")
        self._thread = None

    def update_settings(self, settings: dict):
        """Updates scheduler advance-day thresholds and enabled state from saved preferences."""
        self._enabled = settings.get("enabled", True)
        self._advance_days["High"] = settings.get("high_advance_days", 2)
        self._advance_days["Medium"] = settings.get("medium_advance_days", 1)
        self._advance_days["Low"] = settings.get("low_advance_days", 0)
        self._persistent = settings.get("persistent", True)
        self._group_notifications = settings.get("group_notifications", False)
        logger.info(
            f"NotificationScheduler settings updated: enabled={self._enabled}, "
            f"advance_days={self._advance_days}, persistent={self._persistent}, "
            f"group={self._group_notifications}"
        )

    def _run_loop(self):
        """Main loop — polls every 15 seconds for near real-time threshold detection."""
        import sqlite3
        # Create a dedicated SQLite connection for this thread.
        # DatabaseManager is a singleton with check_same_thread=True, so we can't reuse it.
        try:
            from database.db_manager import DB_PATH
            conn = sqlite3.connect(DB_PATH, check_same_thread=True, timeout=30.0)
            conn.row_factory = sqlite3.Row
        except Exception as e:
            logger.error(f"NotificationScheduler: Failed to open database: {e}")
            return

        # Delay the first execution slightly so it doesn't collide with the Welcome login notification
        time.sleep(3)

        POLL_INTERVAL = 15  # Check every 15 seconds for near real-time
        while self._running:
            try:
                if self._enabled and self._user_id:
                    self._check_and_notify(conn)
            except Exception as e:
                logger.error(f"NotificationScheduler error: {e}", exc_info=True)

            # Sleep in small increments so stop() is responsive
            for _ in range(POLL_INTERVAL):
                if not self._running:
                    break
                time.sleep(1)

        # Clean up connection when loop ends
        try:
            conn.close()
        except Exception:
            pass

    def _check_and_notify(self, conn):
        """Queries pending tasks and fires notifications when tasks cross day-thresholds."""
        today = datetime.today().date()
        now_dt = datetime.now()

        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT t.*, s.name as subject_name 
                FROM tasks t 
                JOIN subjects s ON t.subject_id = s.id 
                WHERE s.user_id = ? AND t.status = 'pending'
                ORDER BY t.deadline ASC
            """, (self._user_id,))
            tasks = [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"NotificationScheduler failed to fetch tasks: {e}")
            return

        if not tasks:
            return

        # Collect messages to send, grouped per priority
        messages_by_priority = {"High": [], "Medium": [], "Low": []}

        for task in tasks:
            deadline_str = task.get('deadline')
            if not deadline_str:
                continue

            priority = task.get('priority', 'Low')
            if priority not in self._advance_days:
                continue

            advance = self._advance_days[priority]
            task_id = task['id']
            task_name = task['name']
            subject_name = task.get('subject_name', '')

            try:
                # Parse deadline date
                date_part = deadline_str.split(" ")[0]
                task_date = datetime.strptime(date_part, "%Y-%m-%d").date()

                # Determine if overdue (compare with time if available)
                compare_deadline = deadline_str if len(deadline_str) > 10 else deadline_str + " 23:59"
                is_overdue = compare_deadline < now_dt.strftime('%Y-%m-%d %H:%M')

                days_remaining = (task_date - today).days

                # Format the deadline for display: "May 20" style
                deadline_display = task_date.strftime("%b %d")

                # --- Check each threshold ---

                # 1. Overdue
                if is_overdue:
                    key = f"overdue_{task_id}"
                    if key not in self._notified_task_ids:
                        messages_by_priority[priority].append({
                            "msg": f"🚨 {task_name} is overdue! Was due ({deadline_display})",
                            "key": key
                        })

                # 2. Due today
                elif days_remaining == 0:
                    key = f"today_{task_id}"
                    if key not in self._notified_task_ids:
                        messages_by_priority[priority].append({
                            "msg": f"⏰ {task_name} is due today!",
                            "key": key
                        })

                # 3. Advance notice (1 day before, 2 days before, etc.)
                elif 1 <= days_remaining <= advance:
                    key = f"days_{days_remaining}_{task_id}"
                    if key not in self._notified_task_ids:
                        if days_remaining == 1:
                            label = "tomorrow"
                        else:
                            label = f"in {days_remaining} days"
                        messages_by_priority[priority].append({
                            "msg": f"📅 {task_name} is due {label} ({deadline_display})",
                            "key": key
                        })

            except Exception:
                pass

        # Send notifications per priority
        for priority in ["High", "Medium", "Low"]:
            entries = messages_by_priority[priority]
            if not entries:
                continue

            messages = [e["msg"] for e in entries]
            title = f"Acadence — {self._username}"
            timeout = 86400 if self._persistent else 10

            if self._group_notifications:
                body = "\n".join(messages[:4])
                if len(messages) > 4:
                    body += f"\n...and {len(messages) - 4} more"

                NotificationManager.send(
                    title=title,
                    message=body,
                    app_name="Acadence Tasks",
                    timeout=timeout
                )
            else:
                # Send up to 5 individual notifications to avoid spamming the OS
                for i, msg in enumerate(messages[:5]):
                    NotificationManager.send(
                        title=title,
                        message=msg,
                        app_name=f"Acadence Task {i + 1}",
                        timeout=timeout
                    )
                    time.sleep(0.5)
                if len(messages) > 5:
                    NotificationManager.send(
                        title=title,
                        message=f"...and {len(messages) - 5} more tasks",
                        app_name="Acadence Tasks",
                        timeout=timeout
                    )

            # Mark these thresholds as notified
            for e in entries:
                self._notified_task_ids.add(e["key"])

            logger.info(f"Sent {priority} priority notification: {len(messages)} alerts")

        # Safety valve: clear tracking set if it grows too large
        if len(self._notified_task_ids) > 500:
            self._notified_task_ids.clear()
