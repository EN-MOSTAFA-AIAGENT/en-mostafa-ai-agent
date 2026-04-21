import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
import traceback
from typing import Optional, Dict


LOG_DIR = r"C:\\mcp-agent\\logs"


class CustomFormatter(logging.Formatter):
    """
    Formatter مخصص لإخراج اللوج بالشكل المطلوب
    """

    def format(self, record: logging.LogRecord) -> str:
        dt = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M")
        level = record.levelname
        component = getattr(record, "component", "general")
        message = record.getMessage()
        return f"[{dt}] [{level}] [{component}] {message}"


class AgentLogger:
    """
    كلاس مركزي لإدارة عمليات الـ Logging داخل النظام
    """

    def __init__(self, name: str):
        """
        تهيئة logger خاص بكل component
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """
        إعداد الـ handlers (File + Console)
        """
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR, exist_ok=True)

        log_file = os.path.join(LOG_DIR, f"agent_{datetime.now().strftime('%Y-%m-%d')}.log")

        formatter = CustomFormatter()

        file_handler = TimedRotatingFileHandler(
            filename=log_file,
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _log(self, level: int, message: str, context: Optional[Dict] = None):
        """
        دالة داخلية لإرسال اللوج مع إضافة context
        """
        extra = {"component": self.name}

        if context:
            message = f"{message} | context={context}"

        self.logger.log(level, message, extra=extra)

    def info(self, message: str, context: Optional[Dict] = None):
        """
        تسجيل رسالة معلومات
        """
        self._log(logging.INFO, message, context)

    def warning(self, message: str, context: Optional[Dict] = None):
        """
        تسجيل تحذير
        """
        self._log(logging.WARNING, message, context)

    def debug(self, message: str, context: Optional[Dict] = None):
        """
        تسجيل رسالة debug
        """
        self._log(logging.DEBUG, message, context)

    def error(self, message: str, error: Exception = None, context: Optional[Dict] = None):
        """
        تسجيل خطأ مع traceback كامل
        """
        full_message = message

        if error:
            tb = traceback.format_exc()
            full_message = f"{message} | error={str(error)}\n{tb}"

        self._log(logging.ERROR, full_message, context)


def get_logger(name: str) -> AgentLogger:
    """
    إرجاع instance من AgentLogger لاستخدامه في أي جزء من المشروع
    """
    return AgentLogger(name)


# Example usage:
# logger = get_logger("server")
# logger.info("Server started")
