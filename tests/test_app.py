"""Exercise the original application contract without a Redis/network dependency."""
import os
import unittest
from unittest.mock import Mock, patch

import app as module


class ApplicationContractTests(unittest.TestCase):
    def setUp(self):
        self.client = module.app.test_client()

    def test_health_does_not_touch_redis(self):
        with patch.object(module, "r") as redis:
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "ok\n")
        redis.incr.assert_not_called()

    def test_index_increments_hits_and_uses_student(self):
        redis = Mock()
        redis.incr.side_effect = [41, 42]
        with patch.object(module, "r", redis), patch.dict(os.environ, STUDENT="Chugunov"):
            first = self.client.get("/")
            second = self.client.get("/")
        self.assertEqual(first.status_code, 200)
        self.assertIn("KR2 | Chugunov | container ", first.text)
        self.assertTrue(first.text.endswith(" | hits: 41\n"))
        self.assertTrue(second.text.endswith(" | hits: 42\n"))
        self.assertEqual(redis.incr.call_args_list[0].args, ("hits",))

    def test_whoami_reports_proxy_headers(self):
        response = self.client.get("/whoami", headers={
            "X-Forwarded-Proto": "https", "X-Real-IP": "192.0.2.10",
            "Host": "api.devops.local",
        })
        self.assertEqual(response.text, "scheme: https\nclient: 192.0.2.10\nhost: api.devops.local\n")

    def test_whoami_missing_forwarding_headers(self):
        response = self.client.get("/whoami")
        self.assertEqual(response.text, "scheme: none\nclient: none\nhost: localhost\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
