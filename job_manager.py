"""
Job Manager - Shared State بين MCP و REST
Thread-Safe + NO HTTP calls between processes
"""

import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
from datetime import datetime
import uuid
import re


class JobState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_USER = "waiting_user"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CommandType(Enum):
    PAUSE = "pause"
    RESUME = "resume"
    WAIT_LOAD = "wait_load"
    SCROLL = "scroll"
    SCREENSHOT = "screenshot"
    RELOAD = "reload"
    GOTO = "goto"
    BACK = "back"
    CANCEL = "cancel"


@dataclass
class Command:
    type: CommandType
    params: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Job:
    id: str
    name: str
    state: JobState = JobState.PENDING
    progress: int = 0
    message: str = ""
    result: Optional[dict] = None
    current_url: str = ""

    _cancel_flag: bool = field(default=False, repr=False)
    _pause_flag: bool = field(default=False, repr=False)
    _resume_event: threading.Event = field(default_factory=threading.Event, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)
    _commands: List[Command] = field(default_factory=list, repr=False)

    def __post_init__(self):
        self._resume_event.set()

    @property
    def cancel_flag(self) -> bool:
        with self._lock:
            return self._cancel_flag

    @cancel_flag.setter
    def cancel_flag(self, value: bool):
        with self._lock:
            self._cancel_flag = value
            if value:
                self._resume_event.set()

    @property
    def pause_flag(self) -> bool:
        with self._lock:
            return self._pause_flag

    @pause_flag.setter
    def pause_flag(self, value: bool):
        with self._lock:
            self._pause_flag = value
            if value:
                self._resume_event.clear()
            else:
                self._resume_event.set()

    def get_state(self) -> JobState:
        """Thread-safe state read"""
        with self._lock:
            return self.state

    def set_state(self, new_state: JobState):
        """Thread-safe state write"""
        with self._lock:
            self.state = new_state

    def add_command(self, cmd: Command):
        with self._lock:
            self._commands.append(cmd)

    def get_command(self) -> Optional[Command]:
        with self._lock:
            return self._commands.pop(0) if self._commands else None

    def has_commands(self) -> bool:
        with self._lock:
            return len(self._commands) > 0

    def wait_if_paused(self, timeout: float = 0.5) -> bool:
        """Wait if paused - returns False if cancelled"""
        while self.pause_flag and not self.cancel_flag:
            self._resume_event.wait(timeout=timeout)
        return not self.cancel_flag

    def set_waiting_user(self, message: str = ""):
        """Switch to waiting user mode"""
        with self._lock:
            self.state = JobState.WAITING_USER
            self.message = message
            self._pause_flag = True
            self._resume_event.clear()

    def resume_from_user(self):
        """Resume after user action"""
        with self._lock:
            self._pause_flag = False
            self.state = JobState.RUNNING
            self._resume_event.set()


class CommandParser:
    """Natural language to commands"""

    PATTERNS = {
        CommandType.PAUSE: [r"وق[ِّ]?ف", r"اسكت", r"pause", r"stop", r"انتظر[ي]?"],
        CommandType.RESUME: [r"كم[ِّ]?ل", r"resume", r"continue", r"يلا", r"امشي"],
        CommandType.WAIT_LOAD: [r"استنى.*تحم[ي]?ل", r"wait.*load"],
        CommandType.SCROLL: [r"انزل.*(تحت|لتحت)", r"scroll.*down", r"نزل",
                            r"ط[ّ]?ل[ع]?.*(فوق|لأعلى)", r"scroll.*up"],
        CommandType.SCREENSHOT: [r"لقطة?\s*شاشة", r"screenshot", r"صور[ي]?"],
        CommandType.RELOAD: [r"اعمل\s*reload", r"reload", r"ريفرش", r"refresh"],
        CommandType.GOTO: [r"افتح\s+(https?://[^\s]+)", r"goto\s+(https?://[^\s]+)"],
        CommandType.BACK: [r"ارجع?\s*خطوة", r"رج[ّ]?ع", r"back"],
        CommandType.CANCEL: [r"الغ[ي]?", r"cancel"],
    }

    @classmethod
    def parse(cls, text: str) -> Optional[Command]:
        text = text.strip().lower()

        for cmd_type, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    params = {}

                    if cmd_type == CommandType.GOTO:
                        url = match.group(1) if match.groups() else None
                        if url:
                            params['url'] = url

                    elif cmd_type == CommandType.SCROLL:
                        if 'تحت' in text or 'down' in text or 'نزل' in text:
                            params['direction'] = 'down'
                        elif 'فوق' in text or 'up' in text:
                            params['direction'] = 'up'
                        else:
                            params['direction'] = 'down'

                        num = re.search(r'(\d+)', text)
                        params['pages'] = int(num.group(1)) if num else 1

                    return Command(type=cmd_type, params=params)

        return None


class JobManager:
    """
    Shared State Manager
    REST و MCP يشتغلوا على نفس الـ object في الـ memory
    مش فيه HTTP calls بينهم
    """

    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._current_job_id: Optional[str] = None
        self._lock = threading.RLock()

    def create_job(self, name: str) -> Job:
        job = Job(id=str(uuid.uuid4())[:8], name=name)
        with self._lock:
            self._jobs[job.id] = job
            self._current_job_id = job.id  # ✅ تحديث الـ current
        return job

    def get_current_job(self) -> Optional[Job]:
        with self._lock:
            if self._current_job_id:
                return self._jobs.get(self._current_job_id)
        return None

    def set_current_job(self, job_id: str):
        with self._lock:
            if job_id in self._jobs:
                self._current_job_id = job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self) -> List[Job]:
        with self._lock:
            return list(self._jobs.values())

    def pause_job(self, job_id: str = None) -> bool:
        """
        Pause job
        ✅ يقبل RUNNING أو WAITING_USER
        """
        job = self.get_job(job_id) if job_id else self.get_current_job()
        if job:
            current_state = job.get_state()
            # ✅ يقبل RUNNING أو WAITING_USER
            if current_state in [JobState.RUNNING, JobState.WAITING_USER]:
                job.pause_flag = True
                job.set_state(JobState.PAUSED)
                return True
        return False

    def resume_job(self, job_id: str = None) -> bool:
        job = self.get_job(job_id) if job_id else self.get_current_job()
        if job:
            current_state = job.get_state()
            if current_state in [JobState.PAUSED, JobState.WAITING_USER]:
                job.resume_from_user()
                return True
        return False

    def cancel_job(self, job_id: str = None) -> bool:
        job = self.get_job(job_id) if job_id else self.get_current_job()
        if job:
            current_state = job.get_state()
            if current_state in [JobState.RUNNING, JobState.PAUSED, JobState.WAITING_USER]:
                job.cancel_flag = True
                job.set_state(JobState.CANCELLED)
                return True
        return False

    def send_command(self, text: str, job_id: str = None) -> Optional[Command]:
        cmd = CommandParser.parse(text)
        if cmd:
            job = self.get_job(job_id) if job_id else self.get_current_job()
            if job:
                job.add_command(cmd)
                return cmd
        return cmd


# Global instance - مشترك بين REST و MCP
job_manager = JobManager()
