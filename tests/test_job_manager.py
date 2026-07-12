import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from job_manager import CommandParser, CommandType, JobManager, JobState


class JobManagerTests(unittest.TestCase):
    def test_arabic_pause_and_resume(self):
        manager = JobManager()
        job = manager.create_job("demo")
        job.set_state(JobState.RUNNING)
        self.assertTrue(manager.pause_job(job.id))
        self.assertEqual(job.get_state(), JobState.PAUSED)
        self.assertTrue(manager.resume_job(job.id))
        self.assertEqual(job.get_state(), JobState.RUNNING)

    def test_parse_goto(self):
        command = CommandParser.parse("افتح https://example.com")
        self.assertEqual(command.type, CommandType.GOTO)
        self.assertEqual(command.params["url"], "https://example.com")

    def test_parse_scroll_direction(self):
        command = CommandParser.parse("scroll down 2")
        self.assertEqual(command.type, CommandType.SCROLL)
        self.assertEqual(command.params["pages"], 2)
        self.assertEqual(command.params["direction"], "down")


if __name__ == "__main__":
    unittest.main()
