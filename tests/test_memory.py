import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from memory import AgentMemory


class AgentMemoryTests(unittest.TestCase):
    def test_store_and_retrieve(self):
        memory = AgentMemory(max_items=2, default_ttl=60)
        memory.store("project", "agent")
        self.assertEqual(memory.retrieve("project"), "agent")

    def test_expired_item_is_removed(self):
        memory = AgentMemory(default_ttl=60)
        memory.store("short", "value", ttl=0.01)
        time.sleep(0.02)
        self.assertIsNone(memory.retrieve("short"))

    def test_capacity_evicts_oldest(self):
        memory = AgentMemory(max_items=2)
        memory.store("a", 1)
        memory.store("b", 2)
        memory.store("c", 3)
        self.assertIsNone(memory.retrieve("a"))
        self.assertEqual(memory.retrieve("c"), 3)


if __name__ == "__main__":
    unittest.main()
