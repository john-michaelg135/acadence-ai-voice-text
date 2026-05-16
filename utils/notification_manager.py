"""
Non-blocking native system notification manager for Acadence.
Uses plyer to send Windows toast notifications on a background thread.
"""
import threading
import os
import sys
from typing import Optional
from utils.logger import logger

class NotificationManager:
    """Manages native system notifications without blocking the main application loop."""

    @staticmethod
    def _send_async(title: str, message: str, app_name: str, timeout: int, icon_path: Optional[str]):
        try:
            # Use win11toast for native Windows 10/11 toasts (supports true persistence)
            from win11toast import toast
            import time
            kwargs = {
                'title': title,
                'body': message,
                'app_id': app_name,
                'tag': str(time.time())  # Force unique tag so Windows 11 always shows the popup flyout
            }
            if icon_path:
                kwargs['icon'] = icon_path
                
            if timeout > 3600:
                kwargs['scenario'] = 'reminder'  # Stays on screen until user dismisses it
            else:
                kwargs['duration'] = 'short'
                
            toast(**kwargs)
        except ImportError:
            # Fallback to plyer for other platforms
            try:
                from plyer import notification
                notification.notify(
                    title=title,
                    message=message,
                    app_name=app_name,
                    app_icon=icon_path,
                    timeout=timeout if timeout < 3600 else 10
                )
            except Exception as e:
                logger.error(f"Failed to send system notification via plyer fallback: {e}")
        except Exception as e:
            logger.error(f"Failed to send system notification via win11toast: {e}")

    @classmethod
    def send(cls, title: str, message: str, app_name: str = "Acadence", timeout: int = 10, icon_name: Optional[str] = None):
        """
        Sends a native desktop notification asynchronously.

        :param title: The header text of the notification
        :param message: The body text of the notification
        :param app_name: The name of the application sending it
        :param timeout: Time in seconds before the notification auto-dismisses
        :param icon_name: File name of the icon (located in assets/)
        """
        icon_path = None
        if icon_name:
            # Resolve paths cleanly whether running as a script or compiled executable
            if getattr(sys, 'frozen', False):
                base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            potential_path = os.path.join(base_dir, 'assets', icon_name)
            if os.path.exists(potential_path):
                icon_path = potential_path

        # Offload execution to a background thread to prevent UI stuttering
        notification_thread = threading.Thread(
            target=cls._send_async,
            args=(title, message, app_name, timeout, icon_path),
            daemon=True
        )
        notification_thread.start()
