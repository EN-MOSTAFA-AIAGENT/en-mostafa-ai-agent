import os
import time

LOG_FILE = r"C:\\mcp-agent\\events.log"


class EventLogger:
    def log_event(self, event_type: str, message: str):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {event_type} {message}\n"

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
