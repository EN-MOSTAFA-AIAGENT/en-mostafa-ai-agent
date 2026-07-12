import os
import sys
import unittest

os.environ["READONLY_MODE"] = "true"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    import server
    IMPORT_ERROR = None
except ModuleNotFoundError as exc:
    server = None
    IMPORT_ERROR = str(exc)


@unittest.skipIf(server is None, f"optional service dependencies are not installed: {IMPORT_ERROR}")
class ServerSmokeTests(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()

    def test_health_is_readonly(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])
        self.assertTrue(response.get_json()["readonly_mode"])

    def test_dashboard_is_embedded(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"MOSTAFA AI Agent", response.data)

    def test_power_tools_are_blocked(self):
        response = self.client.post("/mcp/power", json={"action": "create_folder", "path": "blocked"})
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
